import crypto from "node:crypto";
import fs from "node:fs/promises";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import { composeProjectPages } from "./compose_project_pages.mjs";

async function importRuntimeModule(packageName) {
  const nodeModules = process.env.RUNTIME_NODE_MODULES;
  if (!nodeModules || !path.isAbsolute(nodeModules)) {
    throw new Error("RUNTIME_NODE_MODULES必须是绝对路径");
  }
  const requireFromRuntime = createRequire(path.join(nodeModules, "__runtime__.cjs"));
  return import(pathToFileURL(requireFromRuntime.resolve(packageName)).href);
}

const { FileBlob, PresentationFile, Presentation } = await importRuntimeModule("@oai/artifact-tool");
const TOOL_DIR = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(TOOL_DIR, "../..");

const TEMPLATE_STARTER_BASENAME = "template-starter.pptx";

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
  if (typeof blob.arrayBuffer === "function") {
    await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
    return;
  }
  if (typeof blob.save === "function") {
    await blob.save(filePath);
    return;
  }
  throw new TypeError(`不支持的导出对象：${filePath}`);
}


async function sha256File(filePath) {
  const data = await fs.readFile(filePath);
  return crypto.createHash("sha256").update(data).digest("hex");
}


function maxFontSize(element) {
  const runSizes = (element.paragraphs || []).flatMap((paragraph) =>
    (paragraph.runs || []).map((run) => Number(run.fontSize || 0)),
  );
  return runSizes.length ? Math.max(...runSizes, 0) : Number(element.resolvedFontSize || 0);
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
  const charts = elements.filter((item) => item.kind === "chart" && item.aid).map((item) => item.aid);
  if (charts.length) objects.chart = unique(charts);
  return objects;
}


async function buildFromStarter(plan, starterPptx, outputPptx) {
  if (path.basename(starterPptx) !== TEMPLATE_STARTER_BASENAME) {
    throw new Error(`正式作者输入必须是${TEMPLATE_STARTER_BASENAME}`);
  }
  const presentation = await PresentationFile.importPptx(await FileBlob.load(starterPptx));
  if (presentation.slides.items.length !== plan.pages.length) {
    throw new Error(`starter页数异常：${presentation.slides.items.length}，计划=${plan.pages.length}`);
  }
  const pptx = await PresentationFile.exportPptx(presentation);
  await fs.mkdir(path.dirname(outputPptx), { recursive: true });
  await pptx.save(outputPptx);
}


async function exportEvidence(plan, outputPptx, mappingPath, previewDir, layoutDir, montagePath, workDir) {
  const finalPresentation = await PresentationFile.importPptx(await FileBlob.load(outputPptx));
  if (finalPresentation.slides.items.length !== plan.pages.length) {
    throw new Error(`终版重新导入页数异常：${finalPresentation.slides.items.length}`);
  }
  await Promise.all([
    fs.mkdir(previewDir, { recursive: true }),
    fs.mkdir(layoutDir, { recursive: true }),
    fs.mkdir(workDir, { recursive: true }),
  ]);
  const mappedPages = [];
  for (let index = 0; index < plan.pages.length; index += 1) {
    const slide = finalPresentation.slides.getItem(index);
    const number = String(index + 1).padStart(3, "0");
    const previewPath = path.join(previewDir, `slide-${number}.png`);
    const layoutPath = path.join(layoutDir, `slide-${number}.layout.json`);
    const preview = await slide.export({ format: "png", scale: 1 });
    const layoutBlob = await slide.export({ format: "layout", scale: 1 });
    await writeBlob(previewPath, preview);
    await writeBlob(layoutPath, layoutBlob);
    const layout = JSON.parse(await fs.readFile(layoutPath, "utf8"));
    const page = plan.pages[index];
    mappedPages.push({
      order: index + 1,
      page_id: page.page_id,
      page_name: page.page_name,
      semantic_id: page.semantic_id,
      slide_anchor: layout.slide?.aid || "",
      slide_creation_id: String(slide.creationId || ""),
      slide_layout_id: layout.slide?.layoutId || "",
      slide_layout_name: layout.slide?.layoutName || "",
      master_layout_id: layout.slide?.masterLayoutId || "",
      source_deck: page.source_deck,
      source_page_ids: page.source_page_ids,
      source_slide: page.source_slide,
      visual_variant_id: page.visual_variant_id,
      asset_bindings: page.asset_bindings,
      current_project_copy_status: plan.fixture_only
        && !page.render_content ? "technical_fixture_preserved_source_copy"
        : page.render_content ? "loaded_and_source_copy_cleared" : "not_loaded",
      objects: mapObjectRoles(layout, page.semantic_id),
      preview_path: previewPath,
      layout_path: layoutPath,
    });
  }
  // 整套缩略图由verify_production.py从同版逐页PNG生成；
  // Artifact Tool当前对导入PPT的montage导出只返回首张，不能冒充整套总览。
  await fs.rm(montagePath, { force: true });
  const outputHash = await sha256File(outputPptx);
  const sourceHashes = {};
  for (const sourceDeck of plan.source_decks) {
    sourceHashes[sourceDeck] = await sha256File(sourceDeck);
  }
  const mapping = {
    schema: "product3.production_map.v0.1",
    project_id: plan.project_id,
    assembly_version: plan.assembly_version,
    fixture_only: Boolean(plan.fixture_only),
    blueprint_sha256: plan.blueprint_sha256,
    source_deck_sha256: plan.source_decks.length === 1 ? sourceHashes[plan.source_decks[0]] : "",
    source_deck_sha256s: sourceHashes,
    output_deck_sha256: outputHash,
    output_pptx: outputPptx,
    page_count: mappedPages.length,
    pages: mappedPages,
    applied_assets: [...new Map(plan.pages.flatMap(p => p.resolved_assets || []).map(a => [a.asset_id, a])).values()],
  };
  await fs.mkdir(path.dirname(mappingPath), { recursive: true });
  await fs.writeFile(mappingPath, `${JSON.stringify(mapping, null, 2)}\n`, "utf8");

  await fs.writeFile(path.join(workDir, "template-audit.txt"), [
    `source=${plan.pages.some(p=>p.render_content) ? plan.blueprint_path : plan.source_decks[0]}`,
    `output_slides=${plan.pages.length}`,
    plan.pages.some(p=>p.render_content) ? "mode=current project content in specified native layouts" : "mode=duplicate selected technical source slides",
    "current_scope=only pages explicitly selected by the assembly blueprint; no chapter 1/4 generation",
  ].join("\n") + "\n", "utf8");
  await fs.writeFile(path.join(workDir, "deviation-log.txt"), "Visual and business quality require inspection of these exported pages against the specified reference.\n", "utf8");
  await fs.writeFile(path.join(workDir, "source-notes.txt"), `Frozen input: ${plan.blueprint_path}\n`, "utf8");
}


async function main() {
  const args = parseArgs(process.argv.slice(2));
  for (const key of ["plan", "out-pptx", "mapping", "preview-dir", "layout-dir", "montage", "work-dir"]) {
    if (!args[key]) throw new Error(`缺少参数--${key}`);
  }
  const plan = await loadJson(path.resolve(args.plan));
  if (plan.schema !== "product3.production_plan.v0.1") throw new Error("生产计划schema不受支持");
  if (plan.pages.length && plan.pages.every(p => p.render_content)) {
    const skill = process.env.PRESENTATIONS_SKILL_DIR;
    const python = process.env.RUNTIME_PYTHON || "python3";
    // Re-read the human ledger at the real build boundary too: an old plan must
    // not resurrect an asset deleted after planning.
    const inventory = plan.asset_inventory_path || path.join(PROJECT_ROOT,"references/product3/assets/产物3案例截图素材库/case_asset_inventory.json");
    const library = path.dirname(inventory);
    const ledger = path.join(library,"案例截图素材语义台账.xlsx");
    if (existsSync(ledger)) execFileSync(python,[path.join(PROJECT_ROOT,"tools/shared_datasets/build_case_asset_inventory.py"),"--ledger",ledger,"--original-dir",path.join(library,"original"),"--output",inventory,"--legacy-inventory",inventory],{stdio:"pipe"});
    if (!skill || !path.isAbsolute(skill)) throw new Error("请用当前已安装技能设置PRESENTATIONS_SKILL_DIR");
    if (plan.fixture_only && !args["allow-test-fixture"]) throw new Error("最小复用检查需显式--allow-test-fixture，不代表项目验收");
    // Reuse the existing input validation; do not accept a stale or hand-edited plan.
    execFileSync(python, [path.join(TOOL_DIR,"validate_production_input.py"), plan.blueprint_path, ...(plan.fixture_only ? ["--allow-test-fixture"] : [])]);
    const sorted = value => Array.isArray(value) ? value.map(sorted) : value && typeof value === "object" ? Object.fromEntries(Object.keys(value).sort().map(k=>[k,sorted(value[k])])) : value;
    const blueprint = await loadJson(plan.blueprint_path);
    const digest = crypto.createHash("sha256").update(JSON.stringify(sorted(blueprint))).digest("hex");
    if (digest !== plan.blueprint_sha256) throw new Error("装配清单已变化，请更新生产计划");
    if (plan.pages.length !== blueprint.pages.length || plan.pages.some((p,i)=>p.page_id!==blueprint.pages[i]["页面ID"] || p.visible_copy!==blueprint.pages[i]["页面文案"])) throw new Error("计划页序或可见文字与冻结清单不一致");
    const {resolvePresentationFont, finalizePresentation} = await import(pathToFileURL(path.join(skill,"container_tools/artifact_tool_utils.mjs")).href);
    const created = await composeProjectPages(plan,{Presentation,resolvePresentationFont,projectRoot:PROJECT_ROOT});
    await fs.mkdir(path.resolve(args["work-dir"]),{recursive:true});
    const candidate = path.resolve(args["work-dir"],"candidate.pptx");
    const output = path.resolve(args["out-pptx"]);
    if (candidate === output) throw new Error("候选文件与交付文件须分开");
    await fs.mkdir(path.dirname(output),{recursive:true});
    await (await PresentationFile.exportPptx(created.presentation)).save(candidate);
    await finalizePresentation({workspaceDir:PROJECT_ROOT,candidatePath:candidate,finalPath:output,pythonExecutable:python,
      integrityValidatorPath:path.join(skill,"container_tools/inspect_presentation_package_integrity.py"),
      layoutValidatorPath:path.join(skill,"container_tools/inspect_presentation_layout_geometry.py"),
      layoutArgs:["--expected-slide-size-emu","15240000,8572500","--validate-bullet-geometry","--validate-heading-fit"],
      explicitTotalSlideCount:plan.pages.length,requiredNativeTableOwnerSlides:[],fontPolicy:{basis:"design",families:[resolvePresentationFont({fontFamily:"PingFang SC"}),resolvePresentationFont({fontFamily:"Songti SC"})]},verifyArtifactToolImport:true,
      receiptPath:path.resolve(args["work-dir"],path.basename(output)+".validation.json")});
    await exportEvidence(plan,output,path.resolve(args.mapping),path.resolve(args["preview-dir"]),path.resolve(args["layout-dir"]),path.resolve(args.montage),path.resolve(args["work-dir"]));
    // Same entry produces actual text, preview/PDF and the existing receipt.
    execFileSync(python,[path.join(TOOL_DIR,"verify_production.py"),"--plan",path.resolve(args.plan),"--mapping",path.resolve(args.mapping),"--pptx",output,"--receipt",path.resolve(args["work-dir"],"production_receipt.json"),"--montage",path.resolve(args.montage),...(args.pdf?["--pdf",path.resolve(args.pdf)]:[])],{stdio:"inherit"});
    console.log(JSON.stringify({outputPptx:output,mapping:args.mapping,pages:plan.pages.length,mode:"current_project_content"}));
    return;
  }
  if (!args["starter-pptx"]) throw new Error("此来源路线需--starter-pptx；新项目默认在plan_production.py提供--content");
  if (plan.requires_multi_source_starter || plan.source_decks.length !== 1) {
    if (!args["automizer-starter-receipt"]) {
      throw new Error("多来源计划必须先由pptx-automizer窄适配生成starter并提供回执");
    }
    const adapterReceipt = await loadJson(path.resolve(args["automizer-starter-receipt"]));
    const starterPptx = path.resolve(args["starter-pptx"]);
    if (adapterReceipt.schema !== "product3.automizer_starter_receipt.v0.1" || adapterReceipt.status !== "pass") {
      throw new Error("pptx-automizer starter回执无效");
    }
    if (path.resolve(adapterReceipt.output) !== starterPptx || adapterReceipt.output_sha256 !== await sha256File(starterPptx)) {
      throw new Error("pptx-automizer starter与回执哈希不一致");
    }
    if (Number(adapterReceipt.slide_count) !== plan.pages.length) {
      throw new Error("pptx-automizer starter页数与生产计划不一致");
    }
  }
  if (!plan.fixture_only && plan.pages.some((page) => page.production_route === "reuse_source_slide")) {
    throw new Error("正式项目禁止整页继承历史项目文案；历史来源页只可复用结构");
  }
  if (plan.pages.some((page) => page.production_route !== "reuse_source_slide")) {
    throw new Error(
      "当前作者尚未闭合reuse_structure_rewrite_copy／compose_from_layout的当前项目文案装载；" +
      "已停止正式生产，避免历史项目文案随模板进入新项目",
    );
  }
  const starterPptx = path.resolve(args["starter-pptx"]);
  const outputPptx = path.resolve(args["out-pptx"]);
  await buildFromStarter(plan, starterPptx, outputPptx);
  await exportEvidence(
    plan,
    outputPptx,
    path.resolve(args.mapping),
    path.resolve(args["preview-dir"]),
    path.resolve(args["layout-dir"]),
    path.resolve(args.montage),
    path.resolve(args["work-dir"]),
  );
  console.log(JSON.stringify({ outputPptx, mapping: path.resolve(args.mapping), pages: plan.pages.length }, null, 2));
}


await main();
