import fs from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

async function importRuntimeModule(packageName) {
  const nodeModules = process.env.RUNTIME_NODE_MODULES;
  if (!nodeModules || !path.isAbsolute(nodeModules)) {
    throw new Error("RUNTIME_NODE_MODULES必须是绝对路径");
  }
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

function safeBasename(value) {
  return String(value || "")
    .replaceAll("/", "-")
    .replaceAll("\\", "-")
    .replace(/[^\p{L}\p{N}_.-]+/gu, "-");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.plan || !args["output-dir"]) {
    throw new Error("用法：--plan <production_plan.json> --output-dir <目录>");
  }
  const planPath = path.resolve(args.plan);
  const outputDir = path.resolve(args["output-dir"]);
  const plan = JSON.parse(await fs.readFile(planPath, "utf8"));
  if (plan.schema !== "product3.production_plan.v0.1") {
    throw new Error("生产计划schema不受支持");
  }
  await fs.mkdir(outputDir, { recursive: true });
  const decks = new Map();
  const outputs = [];
  for (const page of plan.pages || []) {
    const sourceDeck = path.resolve(page.source_deck);
    if (!decks.has(sourceDeck)) {
      decks.set(sourceDeck, await PresentationFile.importPptx(await FileBlob.load(sourceDeck)));
    }
    const presentation = decks.get(sourceDeck);
    const sourceSlide = Number(page.source_slide || 0);
    if (!Number.isInteger(sourceSlide) || sourceSlide < 1 || sourceSlide > presentation.slides.items.length) {
      throw new Error(`${page.page_id}来源页号无效：${sourceSlide}`);
    }
    const sourcePageId = (page.source_page_ids || [])[0] || `${safeBasename(page.page_id)}-source`;
    const output = path.join(outputDir, `${safeBasename(sourcePageId)}.png`);
    const preview = await presentation.slides.getItem(sourceSlide - 1).export({ format: "png", scale: 1 });
    await writeBlob(output, preview);
    outputs.push({ page_id: page.page_id, source_page_id: sourcePageId, source_slide: sourceSlide, output });
  }
  await fs.writeFile(
    path.join(outputDir, "source_reference_manifest.json"),
    `${JSON.stringify({ schema: "product3.source_reference_manifest.v0.1", renderer: "Presentations", outputs }, null, 2)}\n`,
    "utf8",
  );
  console.log(JSON.stringify({ outputDir, pages: outputs.length }, null, 2));
}

await main();
