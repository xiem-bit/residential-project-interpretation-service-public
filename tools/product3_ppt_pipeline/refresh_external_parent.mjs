import crypto from "node:crypto";
import fs from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

async function importRuntimeModule(packageName) {
  const nodeModules = process.env.RUNTIME_NODE_MODULES;
  if (!nodeModules || !path.isAbsolute(nodeModules)) throw new Error("RUNTIME_NODE_MODULES必须是绝对路径");
  const requireFromRuntime = createRequire(path.join(nodeModules, "__runtime__.cjs"));
  return import(pathToFileURL(requireFromRuntime.resolve(packageName)).href);
}

const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (!item.startsWith("--")) continue;
    const key = item.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) result[key] = true;
    else {
      result[key] = value;
      index += 1;
    }
  }
  return result;
}

async function loadJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function sha256File(filePath) {
  const data = await fs.readFile(filePath);
  return crypto.createHash("sha256").update(data).digest("hex");
}

function maxFontSize(element) {
  const sizes = (element.paragraphs || []).flatMap((paragraph) =>
    (paragraph.runs || []).map((run) => Number(run.fontSize || 0)),
  );
  return sizes.length ? Math.max(...sizes, 0) : Number(element.resolvedFontSize || 0);
}

function unique(items) {
  return [...new Set(items.filter(Boolean))];
}

function mapObjectRoles(layout, semanticId) {
  const elements = layout.elements || [];
  const textElements = elements.filter((item) => item.aid && typeof item.text === "string" && item.text.trim());
  const topText = textElements
    .filter((item) => Number(item.bbox?.[1] || 0) < 190)
    .sort((left, right) => maxFontSize(right) - maxFontSize(left) || Number(left.bbox?.[1] || 0) - Number(right.bbox?.[1] || 0));
  const title = topText[0]?.aid || "";
  const subtitle = topText.find((item) => item.aid !== title && Number(item.bbox?.[2] || 0) > 320)?.aid || "";
  const lowerText = textElements
    .filter((item) => Number(item.bbox?.[1] || 0) >= 500 && Number(item.bbox?.[2] || 0) >= 420)
    .sort((left, right) => maxFontSize(right) - maxFontSize(left));
  const conclusion = lowerText[0]?.aid || "";
  const footer = textElements
    .filter((item) => item.aid !== conclusion && Number(item.bbox?.[1] || 0) >= 650)
    .map((item) => item.aid);
  const body = textElements
    .filter((item) => ![title, subtitle, conclusion].includes(item.aid) && !footer.includes(item.aid))
    .map((item) => item.aid);
  const images = elements
    .filter((item) => item.kind === "image" && item.aid)
    .sort((left, right) => Number(right.bbox?.[2] || 0) * Number(right.bbox?.[3] || 0) - Number(left.bbox?.[2] || 0) * Number(left.bbox?.[3] || 0));
  const objects = {};
  if (title) objects.title = title;
  if (subtitle) objects.subtitle = subtitle;
  if (body.length) objects.body = unique(body);
  if (conclusion) objects.conclusion = conclusion;
  if (footer.length) objects.footer = unique(footer);
  if (images.length) {
    if (semanticId === "P3-COMPETITION-MAP") objects.map = images[0].aid;
    else objects.main_image = images[0].aid;
    if (images[1]) objects.proof_image_1 = images[1].aid;
    if (images[2]) objects.proof_image_2 = images[2].aid;
  }
  return objects;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  for (const key of ["pptx", "prior-mapping", "out-mapping", "preview-dir", "layout-dir", "receipt"]) {
    if (!args[key]) throw new Error(`缺少参数--${key}`);
  }
  const pptxPath = path.resolve(args.pptx);
  const priorMapping = await loadJson(path.resolve(args["prior-mapping"]));
  const missingCreationIds = priorMapping.pages.filter((page) => !page.slide_creation_id).map((page) => page.page_id);
  if (missingCreationIds.length) {
    throw new Error(`旧映射缺少slide_creation_id，须先刷新生产映射：${missingCreationIds.join(",")}`);
  }
  const priorByCreation = new Map(priorMapping.pages.map((page) => [String(page.slide_creation_id), page]));
  if (priorByCreation.size !== priorMapping.pages.length) throw new Error("旧映射的slide_creation_id重复");
  const presentation = await PresentationFile.importPptx(await FileBlob.load(pptxPath));
  const previewDir = path.resolve(args["preview-dir"]);
  const layoutDir = path.resolve(args["layout-dir"]);
  await Promise.all([fs.mkdir(previewDir, { recursive: true }), fs.mkdir(layoutDir, { recursive: true })]);
  const pages = [];
  const unmatchedSlides = [];
  for (let index = 0; index < presentation.slides.items.length; index += 1) {
    const slide = presentation.slides.getItem(index);
    const number = String(index + 1).padStart(3, "0");
    const previewPath = path.join(previewDir, `slide-${number}.png`);
    const layoutPath = path.join(layoutDir, `slide-${number}.layout.json`);
    await writeBlob(previewPath, await slide.export({ format: "png", scale: 1 }));
    await writeBlob(layoutPath, await slide.export({ format: "layout", scale: 1 }));
    const layout = await loadJson(layoutPath);
    const slideAnchor = layout.slide?.aid || "";
    const slideCreationId = String(slide.creationId || "");
    const prior = priorByCreation.get(slideCreationId);
    if (!prior) {
      unmatchedSlides.push({ order: index + 1, slide_anchor: slideAnchor, slide_creation_id: slideCreationId });
      continue;
    }
    pages.push({
      ...prior,
      order: index + 1,
      slide_anchor: slideAnchor,
      slide_creation_id: slideCreationId,
      slide_layout_id: layout.slide?.layoutId || "",
      slide_layout_name: layout.slide?.layoutName || "",
      master_layout_id: layout.slide?.masterLayoutId || "",
      objects: mapObjectRoles(layout, prior.semantic_id),
      preview_path: previewPath,
      layout_path: layoutPath,
    });
  }
  const missingPageIds = priorMapping.pages
    .filter((page) => !pages.some((current) => current.page_id === page.page_id))
    .map((page) => page.page_id);
  const status = unmatchedSlides.length || missingPageIds.length ? "fail_requires_control_console" : "pass_requires_change_reconciliation";
  const mapping = {
    schema: "product3.production_map.v0.2",
    project_id: priorMapping.project_id,
    assembly_version: `${priorMapping.assembly_version || "unknown"}-external-parent-refresh`,
    fixture_only: Boolean(priorMapping.fixture_only),
    external_parent_refresh: true,
    prior_mapping: path.resolve(args["prior-mapping"]),
    prior_deck_sha256: priorMapping.output_deck_sha256,
    output_deck_sha256: await sha256File(pptxPath),
    output_pptx: pptxPath,
    page_count: pages.length,
    asset_bindings_status: "requires_change_reconciliation",
    pages,
  };
  const outMapping = path.resolve(args["out-mapping"]);
  await fs.mkdir(path.dirname(outMapping), { recursive: true });
  await fs.writeFile(outMapping, `${JSON.stringify(mapping, null, 2)}\n`, "utf8");
  const receipt = {
    schema: "product3.external_parent_refresh_receipt.v0.1",
    status,
    pptx: pptxPath,
    mapping: outMapping,
    prior_page_count: priorMapping.pages.length,
    refreshed_page_count: pages.length,
    unmatched_slides: unmatchedSlides,
    missing_page_ids: missingPageIds,
    next_step: status.startsWith("pass")
      ? "compare refreshed previews with prior previews; reconcile changed text/images before next patch"
      : "return to assembly console to identify inserted/deleted pages and issue a new approved blueprint",
  };
  const receiptPath = path.resolve(args.receipt);
  await fs.mkdir(path.dirname(receiptPath), { recursive: true });
  await fs.writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
  console.log(JSON.stringify(receipt, null, 2));
  if (!status.startsWith("pass")) process.exitCode = 1;
}

await main();
