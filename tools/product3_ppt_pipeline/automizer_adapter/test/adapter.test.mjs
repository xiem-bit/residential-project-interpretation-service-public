import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import test, { after, before } from "node:test";
import JSZip from "jszip";
import PptxGenJS from "pptxgenjs";
import { inspectPptxPackage } from "../pptx_package_safety.mjs";


const execFileAsync = promisify(execFile);
const TEST_DIR = path.dirname(fileURLToPath(import.meta.url));
const ADAPTER_DIR = path.resolve(TEST_DIR, "..");
const ADAPTER = path.join(ADAPTER_DIR, "build_multisource_starter.mjs");
const VERIFIER = path.join(ADAPTER_DIR, "verify_pptx_package.mjs");
const UNSELECTED_MARKERS = [
  "SELECTED_PUBLIC_NOTE_A",
  "UNSELECTED_SLIDE_MARKER",
  "UNSELECTED_NOTES_MARKER",
  "UNSELECTED_MEDIA_MARKER",
  "UNSELECTED_MASTER_MARKER",
];


let tempRoot;
let projectRoot;
let outputDir;
let outputPptx;
let receiptPath;
let receipt;


function svgData(marker) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="160" height="90"><text x="5" y="45">${marker}</text></svg>`;
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`;
}


async function writeSources(destination) {
  const first = new PptxGenJS();
  first.layout = "LAYOUT_WIDE";
  const selected = first.addSlide();
  selected.addText("SELECTED_PUBLIC_PAGE_A", { x: 1, y: 1, w: 8, h: 1 });
  selected.addNotes("SELECTED_PUBLIC_NOTE_A");
  first.defineSlideMaster({
    title: "PRIVATE_MASTER",
    background: { color: "FFFFFF" },
    objects: [
      {
        text: {
          text: "UNSELECTED_MASTER_MARKER",
          options: { x: 0.5, y: 0.5, w: 8, h: 0.5 },
        },
      },
    ],
  });
  const unselected = first.addSlide({ masterName: "PRIVATE_MASTER" });
  unselected.addText("UNSELECTED_SLIDE_MARKER", { x: 1, y: 1, w: 8, h: 1 });
  unselected.addNotes("UNSELECTED_NOTES_MARKER");
  unselected.addImage({
    data: svgData("UNSELECTED_MEDIA_MARKER"),
    x: 1,
    y: 2,
    w: 2,
    h: 1,
  });
  await first.writeFile({ fileName: path.join(destination, "source-a.pptx") });

  const second = new PptxGenJS();
  second.layout = "LAYOUT_WIDE";
  const secondSelected = second.addSlide();
  secondSelected.addText("SELECTED_PUBLIC_PAGE_B", { x: 1, y: 1, w: 8, h: 1 });
  await second.writeFile({ fileName: path.join(destination, "source-b.pptx") });
}


function planData(sourceA = "source-a.pptx") {
  return {
    schema: "product3.production_plan.v0.1",
    requires_multi_source_starter: true,
    source_decks: [sourceA, "source-b.pptx"],
    pages: [
      {
        page_id: "PAGE-A",
        production_route: "reuse_source_slide",
        source_deck: sourceA,
        source_slide: 1,
        source_page_ids: ["SYNTHETIC-A"],
      },
      {
        page_id: "PAGE-B",
        production_route: "reuse_source_slide",
        source_deck: "source-b.pptx",
        source_slide: 1,
        source_page_ids: ["SYNTHETIC-B"],
      },
    ],
  };
}


async function runAdapter(planPath, outPath, receiptFile, root = projectRoot) {
  return execFileAsync(
    process.execPath,
    [
      ADAPTER,
      "--plan",
      planPath,
      "--project-root",
      root,
      "--out",
      outPath,
      "--receipt",
      receiptFile,
    ],
    { cwd: ADAPTER_DIR, maxBuffer: 4 * 1024 * 1024 },
  );
}


async function archiveContains(archive, marker) {
  const needle = Buffer.from(marker);
  for (const entry of Object.values(archive.files)) {
    if (entry.dir) continue;
    const content = Buffer.from(await entry.async("uint8array"));
    if (content.includes(needle)) return true;
  }
  return false;
}


async function archivePartsContaining(archive, marker) {
  const matches = [];
  const needle = Buffer.from(marker);
  for (const [name, entry] of Object.entries(archive.files)) {
    if (entry.dir) continue;
    const content = Buffer.from(await entry.async("uint8array"));
    if (content.includes(needle)) matches.push(name);
  }
  return matches;
}


before(async () => {
  tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "public-pptx-adapter-test-"));
  projectRoot = path.join(tempRoot, "project");
  outputDir = path.join(tempRoot, "output");
  outputPptx = path.join(outputDir, "template-starter.pptx");
  receiptPath = path.join(outputDir, "receipt.json");
  await fs.mkdir(projectRoot, { recursive: true });
  await fs.mkdir(outputDir, { recursive: true });
  await writeSources(projectRoot);
  const planPath = path.join(projectRoot, "plan.json");
  await fs.writeFile(planPath, JSON.stringify(planData()), "utf8");
  await runAdapter(planPath, outputPptx, receiptPath);
  receipt = JSON.parse(await fs.readFile(receiptPath, "utf8"));
});


after(async () => {
  await fs.rm(tempRoot, { recursive: true, force: true });
});


test("selected pages remain and package relationships are complete", async () => {
  const inspection = await inspectPptxPackage(outputPptx);
  assert.equal(inspection.visible_slide_count, 2);
  assert.equal(inspection.unreachable_parts.length, 0);
  assert.equal(inspection.broken_internal_relationships.length, 0);
  assert.equal(inspection.local_path_hits.length, 0);
  const archive = await JSZip.loadAsync(await fs.readFile(outputPptx), { checkCRC32: true });
  assert.equal(await archiveContains(archive, "SELECTED_PUBLIC_PAGE_A"), true);
  assert.equal(await archiveContains(archive, "SELECTED_PUBLIC_PAGE_B"), true);
});


test("unselected slide notes media and master content are absent from the final package", async () => {
  const archive = await JSZip.loadAsync(await fs.readFile(outputPptx), { checkCRC32: true });
  for (const marker of UNSELECTED_MARKERS) {
    assert.deepEqual(await archivePartsContaining(archive, marker), [], marker);
  }
});


test("receipt contains only portable logical paths and temporary source copies are removed", async () => {
  const receiptText = JSON.stringify(receipt);
  assert.equal(receipt.schema, "product3.automizer_starter_receipt.v0.2");
  assert.equal(receipt.status, "pass");
  assert.equal(receipt.slide_count, 2);
  assert.equal(receipt.package_safety.unreachable_part_count, 0);
  assert.equal(receipt.package_safety.broken_internal_relationship_count, 0);
  assert.equal(receipt.package_safety.local_path_hit_count, 0);
  assert.equal(receipt.temporary_source_copies_persisted, false);
  assert.equal(receipt.plan, "plan.json");
  assert.equal(receipt.output, "template-starter.pptx");
  assert.equal(receiptText.includes(tempRoot), false);
  assert.equal(/\/Users\/|\/Applications\/|\/home\/|\/(?:tmp|private\/var|var\/folders)\/|[A-Za-z]:[\\/]|file:\/{2,3}/i.test(receiptText), false);
  await assert.rejects(fs.access(path.join(outputDir, "sanitized-inputs")));
});


test("standalone package verifier rejects an injected orphan part", async () => {
  const unsafePptx = path.join(outputDir, "orphan-injected.pptx");
  const archive = await JSZip.loadAsync(await fs.readFile(outputPptx));
  archive.file("ppt/orphan/private.xml", "ORPHAN_TEST_MARKER");
  await fs.writeFile(unsafePptx, await archive.generateAsync({ type: "nodebuffer" }));
  await assert.rejects(
    execFileAsync(
      process.execPath,
      [VERIFIER, "--pptx", unsafePptx, "--expected-slides", "2"],
      { cwd: ADAPTER_DIR },
    ),
    (error) => {
      const report = JSON.parse(error.stdout);
      assert.equal(report.status, "fail");
      assert.equal(report.unreachable_part_count, 1);
      return true;
    },
  );
});


test("absolute and escaping source paths fail before output is created", async () => {
  const invalidDir = path.join(tempRoot, "invalid-path-plan");
  await fs.mkdir(invalidDir, { recursive: true });
  const invalidPlan = path.join(invalidDir, "plan.json");
  const absoluteSource = path.join(projectRoot, "source-a.pptx");
  await fs.writeFile(invalidPlan, JSON.stringify(planData(absoluteSource)), "utf8");
  const invalidOut = path.join(invalidDir, "template-starter.pptx");
  const invalidReceipt = path.join(invalidDir, "receipt.json");
  await assert.rejects(
    runAdapter(invalidPlan, invalidOut, invalidReceipt),
    (error) => {
      assert.match(error.stderr, /必须是相对project-root的路径/);
      return true;
    },
  );
  await assert.rejects(fs.access(invalidOut));
  await assert.rejects(fs.access(invalidReceipt));
});


test("known image-size denial-of-service media formats fail before automizer runs", async () => {
  const maliciousCases = [
    ["icns", Buffer.from([0x69, 0x63, 0x6e, 0x73, 0, 0, 0, 16, 0, 0, 0, 0])],
    ["jxl-container", Buffer.from([0, 0, 0, 12, 0x4a, 0x58, 0x4c, 0x20, 0x0d, 0x0a, 0x87, 0x0a])],
    ["heif", Buffer.from([0, 0, 0, 0, 0x66, 0x74, 0x79, 0x70, 0x68, 0x65, 0x69, 0x63])],
  ];
  for (const [label, maliciousBytes] of maliciousCases) {
    const caseDir = path.join(tempRoot, `malicious-${label}`);
    await fs.mkdir(caseDir, { recursive: true });
    const sourceArchive = await JSZip.loadAsync(await fs.readFile(path.join(projectRoot, "source-a.pptx")));
    sourceArchive.file("ppt/media/disguised.png", maliciousBytes);
    const maliciousSource = path.join(projectRoot, `malicious-${label}.pptx`);
    await fs.writeFile(maliciousSource, await sourceArchive.generateAsync({ type: "nodebuffer" }));
    const maliciousPlan = path.join(caseDir, "plan.json");
    await fs.writeFile(maliciousPlan, JSON.stringify(planData(path.basename(maliciousSource))), "utf8");
    const maliciousOut = path.join(caseDir, "template-starter.pptx");
    const maliciousReceipt = path.join(caseDir, "receipt.json");
    await assert.rejects(
      runAdapter(maliciousPlan, maliciousOut, maliciousReceipt),
      (error) => {
        assert.match(error.stderr, /不支持的高风险媒体/);
        return true;
      },
    );
    await assert.rejects(fs.access(maliciousOut));
    await assert.rejects(fs.access(maliciousReceipt));
  }
});
