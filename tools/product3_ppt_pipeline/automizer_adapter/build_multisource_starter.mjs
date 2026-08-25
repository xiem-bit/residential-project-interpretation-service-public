import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import JSZip from "jszip";
import { Automizer } from "pptx-automizer";
import { sanitizePptxPackage } from "./pptx_package_safety.mjs";


const FORBIDDEN_MEDIA_EXTENSIONS = new Set([".avif", ".heic", ".heif", ".icns", ".jxl"]);
const HEIF_BRANDS = new Set(["avif", "mif1", "msf1", "heic", "heix", "hevc", "hevx"]);


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


async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}


async function sha256File(filePath) {
  const data = await fs.readFile(filePath);
  return crypto.createHash("sha256").update(data).digest("hex");
}


function forbiddenMediaSignature(bytes) {
  const text = (start, end) => Buffer.from(bytes.subarray(start, end)).toString("ascii");
  if (bytes.length >= 4 && text(0, 4) === "icns") return "icns";
  if (bytes.length >= 10 && bytes[0] === 0xff && bytes[1] === 0x0a) return "jxl-stream";
  if (bytes.length >= 8 && text(4, 8) === "JXL ") return "jxl-container";
  if (bytes.length >= 12 && text(4, 8) === "ftyp" && HEIF_BRANDS.has(text(8, 12))) {
    return `heif:${text(8, 12)}`;
  }
  return "";
}


async function assertSafePptxMedia(archive, logicalSource) {
  let mediaPartCount = 0;
  for (const [name, entry] of Object.entries(archive.files)) {
    if (entry.dir || !name.startsWith("ppt/media/")) continue;
    mediaPartCount += 1;
    const extension = path.posix.extname(name).toLowerCase();
    if (FORBIDDEN_MEDIA_EXTENSIONS.has(extension)) {
      throw new Error(`来源PPTX包含不支持的高风险媒体格式：${logicalSource}:${extension.slice(1)}`);
    }
    const bytes = await entry.async("uint8array");
    const signature = forbiddenMediaSignature(bytes);
    if (signature) {
      throw new Error(`来源PPTX包含不支持的高风险媒体签名：${logicalSource}:${signature}`);
    }
  }
  return {
    scanned_media_part_count: mediaPartCount,
    denied_formats: ["avif", "heic", "heif", "icns", "jxl"],
    policy: "deny_image_size_dos_formats_before_automizer",
  };
}


function normalizeProjectRelativePath(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${label}不能为空`);
  if (value.includes("\0")) throw new Error(`${label}包含非法字符`);
  const normalizedInput = value.trim().replaceAll("\\", "/");
  if (path.posix.isAbsolute(normalizedInput) || path.win32.isAbsolute(value)) {
    throw new Error(`${label}必须是相对project-root的路径`);
  }
  const normalized = path.posix.normalize(normalizedInput);
  if (normalized === ".." || normalized.startsWith("../")) {
    throw new Error(`${label}不得越出project-root`);
  }
  return normalized;
}


function validatePlan(plan) {
  if (plan.schema !== "product3.production_plan.v0.1") throw new Error("生产计划schema不受支持");
  if (!plan.requires_multi_source_starter) throw new Error("该计划不是多来源starter计划");
  if (!Array.isArray(plan.source_decks) || plan.source_decks.length < 2) {
    throw new Error("多来源starter至少需要两份来源PPTX");
  }
  if (!Array.isArray(plan.pages) || !plan.pages.length) throw new Error("生产计划没有页面");

  const sourceDecks = plan.source_decks.map((deck, index) => (
    normalizeProjectRelativePath(deck, `source_decks[${index}]`)
  ));
  if (new Set(sourceDecks).size !== sourceDecks.length) throw new Error("source_decks存在重复路径");
  const sourceDeckSet = new Set(sourceDecks);
  const usedDecks = new Set();
  const pages = plan.pages.map((page, index) => {
    if (!page || typeof page !== "object") throw new Error(`pages[${index}]不是对象`);
    if (page.production_route !== "reuse_source_slide") {
      throw new Error("pptx-automizer适配器只接受原生页复用，不负责重新构图");
    }
    const sourceDeck = normalizeProjectRelativePath(page.source_deck, `pages[${index}].source_deck`);
    if (!sourceDeckSet.has(sourceDeck)) throw new Error(`pages[${index}]引用了未登记的来源PPTX`);
    const sourceSlide = Number(page.source_slide);
    if (!Number.isInteger(sourceSlide) || sourceSlide < 1) {
      throw new Error(`pages[${index}].source_slide必须是正整数`);
    }
    if (typeof page.page_id !== "string" || !page.page_id.trim()) {
      throw new Error(`pages[${index}].page_id不能为空`);
    }
    usedDecks.add(sourceDeck);
    return {
      ...page,
      source_deck: sourceDeck,
      source_slide: sourceSlide,
      source_page_ids: Array.isArray(page.source_page_ids) ? page.source_page_ids : [],
    };
  });
  const unusedDecks = sourceDecks.filter((deck) => !usedDecks.has(deck));
  if (unusedDecks.length) throw new Error("source_decks包含未被页面使用的来源PPTX");
  return { sourceDecks, pages };
}


async function prepareSanitizedTemplate(sourcePath, outputPath, logicalSource, retainedSlides) {
  const archive = await JSZip.loadAsync(await fs.readFile(sourcePath), { checkCRC32: true });
  const mediaSecurity = await assertSafePptxMedia(archive, logicalSource);
  let bomEntriesRemoved = 0;
  let absoluteRelationshipsNormalized = 0;
  for (const [name, entry] of Object.entries(archive.files)) {
    if (entry.dir || (!name.endsWith(".xml") && !name.endsWith(".rels"))) continue;
    let bytes = await entry.async("uint8array");
    if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
      bytes = bytes.slice(3);
      bomEntriesRemoved += 1;
    }
    let text = new TextDecoder("utf-8").decode(bytes);
    if (name.endsWith(".rels")) {
      const sourcePart = name === "_rels/.rels"
        ? ""
        : name.replace("/_rels/", "/").replace(/\.rels$/, "");
      const baseDir = sourcePart ? path.posix.dirname(sourcePart) : ".";
      text = text.replace(/Target="(\/[^"]+)"/g, (match, target) => {
        absoluteRelationshipsNormalized += 1;
        return `Target="${path.posix.relative(baseDir, target.slice(1))}"`;
      });
    }
    archive.file(name, text);
  }
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(
    outputPath,
    await archive.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
  );
  const packageSafety = await sanitizePptxPackage(outputPath, { keepSlideNumbers: retainedSlides });
  return {
    source_deck: logicalSource,
    temporary_name: path.basename(outputPath),
    retained_source_slides: retainedSlides,
    media_security: mediaSecurity,
    bom_entries_removed: bomEntriesRemoved,
    absolute_relationships_normalized: absoluteRelationshipsNormalized,
    package_safety: packageSafety,
    sanitized_sha256: await sha256File(outputPath),
  };
}


async function repairMissingRelationships(pptxPath) {
  const archive = await JSZip.loadAsync(await fs.readFile(pptxPath), { checkCRC32: true });
  const partNames = Object.keys(archive.files).filter((name) => !archive.files[name].dir);
  const partSet = new Set(partNames);
  const notesSlideBacklinks = new Map();
  for (const relsName of partNames.filter((name) => /^ppt\/slides\/_rels\/slide\d+\.xml\.rels$/.test(name))) {
    const sourceSlide = relsName.replace("/_rels/", "/").replace(/\.rels$/, "");
    const baseDir = path.posix.dirname(sourceSlide);
    const relsText = await archive.file(relsName).async("string");
    for (const tag of relsText.match(/<Relationship\b[^>]*\/>/g) || []) {
      if (!/relationships\/notesSlide"/.test(tag) || /TargetMode="External"/.test(tag)) continue;
      const target = tag.match(/Target="([^"]+)"/)?.[1];
      if (!target) continue;
      const resolved = target.startsWith("/")
        ? target.slice(1)
        : path.posix.normalize(path.posix.join(baseDir, target));
      const linkedSlides = notesSlideBacklinks.get(resolved) || [];
      linkedSlides.push(sourceSlide);
      notesSlideBacklinks.set(resolved, linkedSlides);
    }
  }
  const repairs = [];
  const unusedRelationshipsRemoved = [];
  const unresolved = [];
  for (const name of partNames.filter((item) => item.endsWith(".rels"))) {
    const entry = archive.file(name);
    let text = await entry.async("string");
    const sourcePart = name === "_rels/.rels"
      ? ""
      : name.replace("/_rels/", "/").replace(/\.rels$/, "");
    if (sourcePart && !archive.file(sourcePart)) {
      archive.remove(name);
      unusedRelationshipsRemoved.push({ rels: name, id: "__orphan_source_part__" });
      continue;
    }
    const sourceXml = sourcePart && archive.file(sourcePart)
      ? await archive.file(sourcePart).async("string")
      : "";
    const baseDir = sourcePart ? path.posix.dirname(sourcePart) : ".";
    text = text.replace(/<Relationship\b[^>]*\/>/g, (tag) => {
      if (/TargetMode="External"/.test(tag)) return tag;
      const targetMatch = tag.match(/Target="([^"]+)"/);
      const idMatch = tag.match(/Id="([^"]+)"/);
      const type = tag.match(/Type="([^"]+)"/)?.[1] || "";
      if (!targetMatch) return tag;
      const target = targetMatch[1];
      const resolved = target.startsWith("/")
        ? target.slice(1)
        : path.posix.normalize(path.posix.join(baseDir, target));
      if (partSet.has(resolved)) return tag;
      if (type.endsWith("/slide") && sourcePart.startsWith("ppt/notesSlides/")) {
        const linkedSlides = notesSlideBacklinks.get(sourcePart) || [];
        if (linkedSlides.length === 1 && partSet.has(linkedSlides[0])) {
          const replacement = path.posix.relative(baseDir, linkedSlides[0]);
          repairs.push({ rels: name, id: idMatch?.[1] || "" });
          return tag.replace(`Target="${target}"`, `Target="${replacement}"`);
        }
      }
      const normalizedTail = target.replace(/^\/+/, "").replace(/^(\.\.\/)+/, "");
      let candidates = partNames.filter((part) => part.endsWith(`/${normalizedTail}`) || part === normalizedTail);
      if (candidates.length !== 1) {
        const basename = path.posix.basename(normalizedTail);
        candidates = partNames.filter((part) => path.posix.basename(part) === basename);
      }
      if (candidates.length !== 1) {
        if (idMatch && sourceXml && !sourceXml.includes(idMatch[1])) {
          unusedRelationshipsRemoved.push({ rels: name, id: idMatch[1] });
          return "";
        }
        unresolved.push({
          rels: name,
          id: idMatch?.[1] || "",
          type,
          target,
          source_reference_present: Boolean(idMatch && sourceXml.includes(idMatch[1])),
          backlink_candidates: notesSlideBacklinks.get(sourcePart) || [],
        });
        return tag;
      }
      const replacement = path.posix.relative(baseDir, candidates[0]);
      repairs.push({ rels: name, id: idMatch?.[1] || "" });
      return tag.replace(`Target="${target}"`, `Target="${replacement}"`);
    });
    archive.file(name, text);
  }
  if (unresolved.length) {
    throw new Error(`starter仍有无法解析的内部关系：${JSON.stringify(unresolved)}`);
  }
  if (repairs.length || unusedRelationshipsRemoved.length) {
    await fs.writeFile(
      pptxPath,
      await archive.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }),
    );
  }
  return {
    repair_count: repairs.length,
    unused_relationship_removal_count: unusedRelationshipsRemoved.length,
  };
}


function assertPortableReceipt(receipt) {
  const text = JSON.stringify(receipt);
  const forbidden = [
    /\/Users\//,
    /\/Applications\//,
    /\/home\//,
    /\/(?:tmp|private\/var|var\/folders)\//,
    /[A-Za-z]:[\\/]/,
    /file:\/{2,3}/i,
  ];
  if (forbidden.some((pattern) => pattern.test(text))) {
    throw new Error("生产回执包含本机绝对路径");
  }
}


async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.plan || !args.out || !args.receipt) throw new Error("需要--plan、--out和--receipt");
  const planPath = path.resolve(args.plan);
  const plan = JSON.parse(await fs.readFile(planPath, "utf8"));
  const { sourceDecks, pages } = validatePlan(plan);
  const projectRoot = path.resolve(args["project-root"] || process.cwd());
  const outPath = path.resolve(args.out);
  const receiptPath = path.resolve(args.receipt);
  if (path.basename(outPath) !== "template-starter.pptx") {
    throw new Error("多来源适配器输出必须命名为template-starter.pptx");
  }
  if (await fileExists(outPath)) throw new Error("输出PPTX已存在，请使用新的输出目录");
  if (await fileExists(receiptPath)) throw new Error("生产回执已存在，请使用新的回执路径");
  await fs.mkdir(path.dirname(outPath), { recursive: true });
  await fs.mkdir(path.dirname(receiptPath), { recursive: true });

  const workDir = await fs.mkdtemp(path.join(os.tmpdir(), "product3-pptx-starter-"));
  const sanitizedDir = path.join(workDir, "sanitized-inputs");
  let outputAttempted = false;
  let receiptAttempted = false;
  try {
    const deckLabels = new Map();
    const sanitizedDecks = new Map();
    const sanitizedSlideNumbers = new Map();
    const sanitizedTemplates = [];
    for (let index = 0; index < sourceDecks.length; index += 1) {
      const deck = sourceDecks[index];
      const label = `deck_${index + 1}`;
      const sanitizedName = `${label}.pptx`;
      const sourcePath = path.resolve(projectRoot, ...deck.split("/"));
      const sourceStat = await fs.stat(sourcePath);
      if (!sourceStat.isFile()) throw new Error(`来源PPTX不是文件：${deck}`);
      const retainedSlides = [...new Set(
        pages.filter((page) => page.source_deck === deck).map((page) => page.source_slide),
      )].sort((left, right) => left - right);
      sanitizedSlideNumbers.set(
        deck,
        new Map(retainedSlides.map((sourceSlide, retainedIndex) => [sourceSlide, retainedIndex + 1])),
      );
      deckLabels.set(deck, label);
      sanitizedDecks.set(deck, sanitizedName);
      sanitizedTemplates.push(await prepareSanitizedTemplate(
        sourcePath,
        path.join(sanitizedDir, sanitizedName),
        deck,
        retainedSlides,
      ));
    }

    const rootDeck = sourceDecks[0];
    let presentation = new Automizer({
      templateDir: sanitizedDir,
      outputDir: path.dirname(outPath),
      useCreationIds: false,
      autoImportSlideMasters: true,
      removeExistingSlides: true,
      cleanup: true,
      compression: 0,
      verbosity: 0,
      continueOnError: false,
    }).loadRoot(sanitizedDecks.get(rootDeck));
    for (const deck of sourceDecks) {
      presentation = presentation.load(sanitizedDecks.get(deck), deckLabels.get(deck));
    }
    for (const page of pages) {
      presentation = presentation.addSlide(
        deckLabels.get(page.source_deck),
        sanitizedSlideNumbers.get(page.source_deck).get(page.source_slide),
      );
    }
    outputAttempted = true;
    await presentation.write(path.basename(outPath));
    const outputRelationshipRepairs = await repairMissingRelationships(outPath);
    const packageSafety = await sanitizePptxPackage(outPath);
    if (packageSafety.visible_slide_count !== pages.length) {
      throw new Error(`starter可见页数${packageSafety.visible_slide_count}与计划${pages.length}不一致`);
    }

    const sourceHashes = {};
    for (const deck of sourceDecks) {
      sourceHashes[deck] = await sha256File(path.resolve(projectRoot, ...deck.split("/")));
    }
    const receipt = {
      schema: "product3.automizer_starter_receipt.v0.2",
      status: "pass",
      adapter: "pptx-automizer",
      adapter_version: "0.9.3",
      path_policy: "logical_relative_paths_only",
      path_bases: {
        source_decks: "project_root",
        temporary_templates: "ephemeral_work_directory",
        output: "output_directory",
        plan: "invocation_basename",
      },
      plan: path.basename(planPath),
      plan_sha256: await sha256File(planPath),
      source_deck_sha256s: sourceHashes,
      temporary_source_copies_persisted: false,
      sanitized_templates: sanitizedTemplates,
      output_relationship_repairs: outputRelationshipRepairs,
      package_safety: packageSafety,
      output: path.basename(outPath),
      output_sha256: await sha256File(outPath),
      slide_count: pages.length,
      output_pages: pages.map((page, index) => ({
        output_slide: index + 1,
        page_id: page.page_id,
        source_deck: page.source_deck,
        source_slide: page.source_slide,
        source_page_ids: page.source_page_ids,
      })),
      scope: "multi-source native-slide starter only; no formal editing or visual QA",
    };
    assertPortableReceipt(receipt);
    receiptAttempted = true;
    await fs.writeFile(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
    console.log(JSON.stringify(receipt, null, 2));
  } catch (error) {
    if (outputAttempted) await fs.rm(outPath, { force: true });
    if (receiptAttempted) await fs.rm(receiptPath, { force: true });
    throw error;
  } finally {
    await fs.rm(workDir, { recursive: true, force: true });
  }
}


await main();
