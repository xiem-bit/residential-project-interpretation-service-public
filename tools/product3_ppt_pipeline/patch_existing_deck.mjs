import crypto from "node:crypto";
import fs from "node:fs/promises";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
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
  return objects;
}

function requirePage(pageById, pageId) {
  const page = pageById.get(pageId);
  if (!page) throw new Error(`页面ID不存在：${pageId}`);
  return page;
}

function requireObjectAnchor(page, role) {
  const anchor = page.objects?.[role];
  if (!anchor || Array.isArray(anchor)) {
    throw new Error(`页面${page.page_id}不存在可直接定位的对象角色：${role}`);
  }
  return anchor;
}

function contentTypeFor(filePath) {
  const suffix = path.extname(filePath).toLowerCase();
  if (suffix === ".png") return "image/png";
  if (suffix === ".jpg" || suffix === ".jpeg") return "image/jpeg";
  if (suffix === ".webp") return "image/webp";
  throw new Error(`不支持的替换图片格式：${suffix}`);
}

async function readArrayBuffer(filePath) {
  const bytes = await fs.readFile(filePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function movePage(presentation, pages, pageId, targetIndex) {
  const currentIndex = pages.findIndex((page) => page.page_id === pageId);
  if (currentIndex < 0) throw new Error(`页面ID不存在：${pageId}`);
  if (targetIndex < 0 || targetIndex >= pages.length) throw new Error(`目标页序越界：${targetIndex + 1}`);
  if (currentIndex === targetIndex) return;
  const [page] = pages.splice(currentIndex, 1);
  pages.splice(targetIndex, 0, page);
  presentation.resolve(page.slide_anchor).moveTo(targetIndex);
}

async function applyOperations(presentation, pages, request) {
  const pageById = new Map(pages.map((page) => [page.page_id, page]));
  const applied = [];
  for (const operation of request.operations || []) {
    if (operation.op === "replace_notes") {
      const page = requirePage(pageById, operation.page_id);
      if (typeof operation.text !== "string" || !operation.text.trim()) throw new Error("备注修订须提供实际讲解内容");
      presentation.slides.getItem(pages.indexOf(page)).speakerNotes.textFrame.setText(operation.text);
      applied.push({ ...operation });
      continue;
    }
    if (operation.op === "replace_image") {
      const page = requirePage(pageById, operation.page_id);
      const semanticAllowlist = operation.expected_semantic_ids || [];
      if (semanticAllowlist.length && !semanticAllowlist.includes(page.semantic_id)) {
        throw new Error(`页面${page.page_id}语义${page.semantic_id}不在换图允许范围内`);
      }
      const role = operation.role || "main_image";
      const anchor = requireObjectAnchor(page, role);
      const target = presentation.resolve(anchor);
      if (!target || typeof target.replace !== "function") throw new Error(`对象${anchor}不是可替换图片`);
      const assetPath = path.resolve(operation.asset_path);
      target.replace({
        blob: await readArrayBuffer(assetPath),
        contentType: contentTypeFor(assetPath),
        alt: operation.alt || operation.asset_id || path.basename(assetPath),
        ...(operation.fit ? { fit: operation.fit } : {}),
      });
      const bindings = typeof page.asset_bindings === "object" && page.asset_bindings ? page.asset_bindings : {};
      page.asset_bindings = {
        ...bindings,
        [role]: {
          asset_id: operation.asset_id || "",
          asset_path: assetPath,
          asset_sha256: await sha256File(assetPath),
        },
      };
      applied.push({ ...operation, asset_path: assetPath });
      continue;
    }
    if (operation.op === "replace_text") {
      const page = requirePage(pageById, operation.page_id);
      const anchor = requireObjectAnchor(page, operation.role);
      const target = presentation.resolve(anchor);
      if (!target?.text || typeof target.text.replace !== "function") throw new Error(`对象${anchor}不是可编辑文本`);
      target.text.replace(operation.find, operation.replace);
      applied.push({ ...operation });
      continue;
    }
    if (operation.op === "move_page") {
      const targetIndex = Number(operation.target_order) - 1;
      if (!Number.isInteger(targetIndex)) throw new Error("move_page需要整数target_order");
      movePage(presentation, pages, operation.page_id, targetIndex);
      applied.push({ ...operation });
      continue;
    }
    throw new Error(`不支持的修订动作：${operation.op}`);
  }
  return applied;
}

async function exportNotesOnly(presentation, pages, request, outputPptx, mappingPath, workDir, applied, parentMapping) {
  // SDK编辑备注；只回装备注正文，避免导入再导出改变已认可的前台对象。
  await fs.mkdir(workDir, { recursive: true });
  await fs.mkdir(path.dirname(outputPptx), { recursive: true });
  const donor = path.join(workDir, "notes-sdk.pptx");
  const candidate = path.join(workDir, "notes-candidate.pptx");
  await (await PresentationFile.exportPptx(presentation)).save(donor);
  const replacements = applied.map(op => ({ order: pages.findIndex(p => p.page_id === op.page_id) + 1, text: op.text }));
  const python = process.env.RUNTIME_PYTHON;
  const skillDir = process.env.PRESENTATIONS_SKILL_DIR;
  if (!python || !path.isAbsolute(python) || !skillDir || !path.isAbsolute(skillDir)) throw new Error("备注修订需要当前演示文稿运行环境与Skill绝对路径");
  const preserved = JSON.parse(execFileSync(python, ["-c", `
import sys,json,posixpath,hashlib,copy
from zipfile import ZipFile
from xml.etree import ElementTree as E
parent,donor,target,raw=sys.argv[1:]
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
def note_name(z,order):
    rel=E.fromstring(z.read(f'ppt/slides/_rels/slide{order}.xml.rels'))
    link=next(r for r in rel if r.attrib['Type'].endswith('/notesSlide'))
    target=link.attrib['Target']
    return target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('ppt/slides',target))
def body(root):
    return next(s for s in root.findall('.//p:sp',ns) if (s.find('p:nvSpPr/p:nvPr/p:ph',ns) is not None and s.find('p:nvSpPr/p:nvPr/p:ph',ns).get('type')=='body'))
changes={}
with ZipFile(parent) as old, ZipFile(donor) as new:
    for item in json.loads(raw):
        name=note_name(old,item['order']); source=E.fromstring(old.read(name))
        target_body=body(source); donor_body=body(E.fromstring(new.read(note_name(new,item['order']))))
        text_body=donor_body.find('p:txBody',ns)
        actual=''.join(text_body.itertext())
        expected=''.join(item['text'].split())
        if ''.join(actual.split())!=expected: raise RuntimeError('SDK备注与批准输入不一致')
        target_body.remove(target_body.find('p:txBody',ns)); target_body.append(copy.deepcopy(text_body))
        changes[name]=E.tostring(source,encoding='utf-8',xml_declaration=True)
    with ZipFile(target,'w') as output:
        for member in old.infolist(): output.writestr(member,changes.get(member.filename,old.read(member.filename)))
with ZipFile(parent) as old, ZipFile(target) as new:
    assert old.namelist()==new.namelist()
    changed=[name for name in old.namelist() if old.read(name)!=new.read(name)]
    assert set(changed)==set(changes), '前台或其他文件发生变化'
print(json.dumps({'changed_members':changed,'unchanged_members':len(old.namelist())-len(changed),'front_members_identical':True}))
`, request.parent_pptx, donor, candidate, JSON.stringify(replacements)], { encoding: "utf8" }));
  const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href);
  await finalizePresentation({
    workspaceDir: path.dirname(workDir), candidatePath: candidate, finalPath: outputPptx,
    pythonExecutable: python,
    integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
    layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
    explicitTotalSlideCount: pages.length, requiredNativeTableOwnerSlides: [], requiredNativeChartOwnerSlides: [],
    verifyArtifactToolImport: true, receiptPath: path.join(workDir, "notes-finalization.json"),
  });
  // finalizer只作校验与复制，仍以最终实际文件确认字节相同。
  if (await sha256File(candidate) !== await sha256File(outputPptx)) throw new Error("备注定稿改变了已核对候选文件");
  const mapping = { ...parentMapping, assembly_version: request.assembly_version, parent_pptx: request.parent_pptx,
    parent_deck_sha256: parentMapping.output_deck_sha256, output_pptx: outputPptx,
    output_deck_sha256: await sha256File(outputPptx), applied_operations: applied,
    validation_scope: "speaker_notes_only; visible pages and existing visual evidence preserved", notes_preservation: preserved,
    pages: pages.map(p => ({ ...p, ...(applied.find(op => op.page_id === p.page_id) ? { speaker_notes: applied.find(op => op.page_id === p.page_id).text } : {}) })) };
  await fs.mkdir(path.dirname(mappingPath), { recursive: true });
  await fs.writeFile(mappingPath, JSON.stringify(mapping, null, 2) + "\n");
  await fs.writeFile(path.join(workDir, "notes-preservation.json"), JSON.stringify(preserved, null, 2) + "\n");
}

async function exportEvidence(presentation, pages, request, outputPptx, mappingPath, previewDir, layoutDir, workDir, applied) {
  await Promise.all([
    fs.mkdir(path.dirname(outputPptx), { recursive: true }),
    fs.mkdir(previewDir, { recursive: true }),
    fs.mkdir(layoutDir, { recursive: true }),
    fs.mkdir(workDir, { recursive: true }),
  ]);
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outputPptx);
  const finalPresentation = await PresentationFile.importPptx(await FileBlob.load(outputPptx));
  if (finalPresentation.slides.items.length !== pages.length) throw new Error("修订版重新导入页数异常");
  const mappedPages = [];
  for (let index = 0; index < pages.length; index += 1) {
    const slide = finalPresentation.slides.getItem(index);
    const number = String(index + 1).padStart(3, "0");
    const previewPath = path.join(previewDir, `slide-${number}.png`);
    const layoutPath = path.join(layoutDir, `slide-${number}.layout.json`);
    await writeBlob(previewPath, await slide.export({ format: "png", scale: 1 }));
    await writeBlob(layoutPath, await slide.export({ format: "layout", scale: 1 }));
    const layout = JSON.parse(await fs.readFile(layoutPath, "utf8"));
    const page = pages[index];
    mappedPages.push({
      ...page,
      order: index + 1,
      slide_anchor: layout.slide?.aid || "",
      slide_creation_id: String(slide.creationId || ""),
      slide_layout_id: layout.slide?.layoutId || "",
      slide_layout_name: layout.slide?.layoutName || "",
      master_layout_id: layout.slide?.masterLayoutId || "",
      objects: mapObjectRoles(layout, page.semantic_id),
      preview_path: previewPath,
      layout_path: layoutPath,
    });
  }
  const mapping = {
    schema: "product3.production_map.v0.2",
    project_id: request.project_id,
    assembly_version: request.assembly_version,
    fixture_only: Boolean(request.fixture_only),
    parent_pptx: path.resolve(request.parent_pptx),
    parent_deck_sha256: await sha256File(path.resolve(request.parent_pptx)),
    output_deck_sha256: await sha256File(outputPptx),
    output_pptx: outputPptx,
    page_count: mappedPages.length,
    applied_operations: applied,
    pages: mappedPages,
  };
  await fs.mkdir(path.dirname(mappingPath), { recursive: true });
  await fs.writeFile(mappingPath, `${JSON.stringify(mapping, null, 2)}\n`, "utf8");
  await fs.writeFile(path.join(workDir, "patch-audit.txt"), [
    `parent=${mapping.parent_pptx}`,
    `output=${outputPptx}`,
    `operations=${applied.length}`,
    "scope=focused local revision; no chapter 1/4 generation",
  ].join("\n") + "\n", "utf8");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  for (const key of ["request", "out-pptx", "mapping", "preview-dir", "layout-dir", "work-dir"]) {
    if (!args[key]) throw new Error(`缺少参数--${key}`);
  }
  const request = await loadJson(path.resolve(args.request));
  if (request.schema !== "product3.patch_request.v0.1") throw new Error("修订请求schema不受支持");
  if (!request.fixture_only && request.status !== "approved_for_production") {
    throw new Error("正式修订请求必须是approved_for_production");
  }
  const parentPptx = path.resolve(request.parent_pptx);
  const parentMapping = await loadJson(path.resolve(request.parent_mapping));
  if (await sha256File(parentPptx) !== parentMapping.output_deck_sha256) {
    throw new Error("父版PPTX与父版映射哈希不一致");
  }
  const presentation = await PresentationFile.importPptx(await FileBlob.load(parentPptx));
  const pages = [...parentMapping.pages].sort((left, right) => left.order - right.order);
  if (presentation.slides.items.length !== pages.length) throw new Error("父版页数与映射不一致");
  const applied = await applyOperations(presentation, pages, request);
  if (applied.length && applied.every(op => op.op === "replace_notes")) {
    await exportNotesOnly(presentation, pages, request, path.resolve(args["out-pptx"]), path.resolve(args.mapping), path.resolve(args["work-dir"]), applied, parentMapping);
  } else await exportEvidence(
    presentation,
    pages,
    request,
    path.resolve(args["out-pptx"]),
    path.resolve(args.mapping),
    path.resolve(args["preview-dir"]),
    path.resolve(args["layout-dir"]),
    path.resolve(args["work-dir"]),
    applied,
  );
  console.log(JSON.stringify({
    outputPptx: path.resolve(args["out-pptx"]),
    mapping: path.resolve(args.mapping),
    pages: pages.length,
    operations: applied.length,
  }, null, 2));
}

await main();
