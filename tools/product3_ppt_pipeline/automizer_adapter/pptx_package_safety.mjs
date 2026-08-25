import fs from "node:fs/promises";
import path from "node:path";
import JSZip from "jszip";


const RELATIONSHIP_TAG = /<Relationship\b[^>]*\/>/g;
const LOCAL_PATH_PATTERNS = (
  [
    ["mac_user_path", /\/Users\//],
    ["mac_application_path", /\/Applications\//],
    ["linux_home_path", /\/home\//],
    ["temporary_path", /\/(?:tmp|private\/var|var\/folders)\//],
    ["windows_user_path", /[A-Za-z]:[\\/]Users[\\/]/],
    ["local_file_url", /file:\/{2,3}/i],
  ]
);


function attributeValue(tag, name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = tag.match(new RegExp(`\\b${escaped}\\s*=\\s*(?:\"([^\"]*)\"|'([^']*)')`));
  return match ? (match[1] ?? match[2] ?? "") : "";
}


function relationshipPartForSource(sourcePart) {
  if (!sourcePart) return "_rels/.rels";
  const directory = path.posix.dirname(sourcePart);
  const prefix = directory === "." ? "" : `${directory}/`;
  return `${prefix}_rels/${path.posix.basename(sourcePart)}.rels`;
}


function sourcePartForRelationship(relsPart) {
  if (relsPart === "_rels/.rels") return "";
  const marker = "/_rels/";
  const markerIndex = relsPart.lastIndexOf(marker);
  if (markerIndex < 0 || !relsPart.endsWith(".rels")) {
    throw new Error(`无法识别OOXML关系来源：${relsPart}`);
  }
  const directory = relsPart.slice(0, markerIndex);
  const fileName = relsPart.slice(markerIndex + marker.length, -".rels".length);
  return `${directory}/${fileName}`;
}


function normalizeInternalTarget(sourcePart, target) {
  const withoutFragment = target.split("#", 1)[0].replaceAll("\\", "/");
  const resolved = withoutFragment.startsWith("/")
    ? path.posix.normalize(withoutFragment.slice(1))
    : path.posix.normalize(path.posix.join(sourcePart ? path.posix.dirname(sourcePart) : ".", withoutFragment));
  if (resolved === ".." || resolved.startsWith("../")) {
    throw new Error(`OOXML内部关系越出包根目录：${target}`);
  }
  return resolved;
}


function resolveArchivePart(archive, sourcePart, target) {
  const normalized = normalizeInternalTarget(sourcePart, target);
  if (archive.file(normalized)) return normalized;
  try {
    const decoded = decodeURI(normalized);
    if (archive.file(decoded)) return decoded;
  } catch {
    // Keep the normalized value so the caller can report a broken relationship.
  }
  return normalized;
}


function parseRelationships(xml, relsPart) {
  const sourcePart = sourcePartForRelationship(relsPart);
  return [...xml.matchAll(RELATIONSHIP_TAG)].map((match) => {
    const tag = match[0];
    return {
      tag,
      id: attributeValue(tag, "Id"),
      type: attributeValue(tag, "Type"),
      target: attributeValue(tag, "Target"),
      external: attributeValue(tag, "TargetMode").toLowerCase() === "external",
      sourcePart,
      relsPart,
    };
  });
}


async function readRelationships(archive, sourcePart) {
  const relsPart = relationshipPartForSource(sourcePart);
  const entry = archive.file(relsPart);
  if (!entry) return { relsPart, xml: "", relationships: [] };
  const xml = await entry.async("string");
  return { relsPart, xml, relationships: parseRelationships(xml, relsPart) };
}


function openingTags(xml, localName) {
  const escaped = localName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return xml.match(new RegExp(`<(?:[A-Za-z_][\\w.-]*:)?${escaped}\\b[^>]*\/?>`, "g")) ?? [];
}


function filterIdTags(xml, localName, keepIds) {
  const escaped = localName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return xml.replace(
    new RegExp(`<(?:[A-Za-z_][\\w.-]*:)?${escaped}\\b[^>]*\/?>`, "g"),
    (tag) => keepIds.has(attributeValue(tag, "r:id")) ? tag : "",
  );
}


function isRelationshipType(relationship, suffix) {
  return relationship.type.endsWith(`/${suffix}`);
}


async function requiredTargetsByType(archive, sourceParts, typeSuffix) {
  const targets = new Set();
  for (const sourcePart of sourceParts) {
    const { relationships } = await readRelationships(archive, sourcePart);
    for (const relationship of relationships) {
      if (relationship.external || !isRelationshipType(relationship, typeSuffix)) continue;
      const target = resolveArchivePart(archive, sourcePart, relationship.target);
      if (!archive.file(target)) {
        throw new Error(`OOXML内部关系缺少目标：${relationship.relsPart} -> ${relationship.target}`);
      }
      targets.add(target);
    }
  }
  return targets;
}


async function prunePresentationReferences(archive, keepSlideNumbers = null) {
  const presentationPart = "ppt/presentation.xml";
  const presentationEntry = archive.file(presentationPart);
  if (!presentationEntry) throw new Error("PPTX缺少ppt/presentation.xml");
  let presentationXml = await presentationEntry.async("string");
  const presentationRelationships = await readRelationships(archive, presentationPart);
  if (!presentationRelationships.xml) throw new Error("PPTX缺少presentation.xml.rels");

  const originalSlideTags = openingTags(presentationXml, "sldId");
  if (keepSlideNumbers !== null) {
    if (!Array.isArray(keepSlideNumbers) || !keepSlideNumbers.length) {
      throw new Error("来源PPTX至少需要保留一页");
    }
    const keepPositions = new Set(keepSlideNumbers);
    if (
      keepPositions.size !== keepSlideNumbers.length
      || keepSlideNumbers.some((position) => !Number.isInteger(position) || position < 1 || position > originalSlideTags.length)
    ) {
      throw new Error("来源PPTX保留页码无效或重复");
    }
    const keepSlideIds = new Set(
      originalSlideTags
        .filter((_, index) => keepPositions.has(index + 1))
        .map((tag) => attributeValue(tag, "r:id")),
    );
    presentationXml = filterIdTags(presentationXml, "sldId", keepSlideIds);
  }
  const visibleSlideIds = new Set(
    openingTags(presentationXml, "sldId")
      .map((tag) => attributeValue(tag, "r:id"))
      .filter(Boolean),
  );
  if (!visibleSlideIds.size) throw new Error("PPTX没有可见幻灯片");

  const visibleSlideParts = new Set();
  for (const relationship of presentationRelationships.relationships) {
    if (!visibleSlideIds.has(relationship.id) || !isRelationshipType(relationship, "slide")) continue;
    const target = resolveArchivePart(archive, presentationPart, relationship.target);
    if (!archive.file(target)) throw new Error(`可见幻灯片关系缺少目标：${relationship.target}`);
    visibleSlideParts.add(target);
  }
  if (visibleSlideParts.size !== visibleSlideIds.size) {
    throw new Error("可见幻灯片ID与内部关系数量不一致");
  }

  let removedAnnotationRelationships = 0;
  for (const slidePart of visibleSlideParts) {
    const slideRelationships = await readRelationships(archive, slidePart);
    if (!slideRelationships.xml) continue;
    const cleanedRelationships = slideRelationships.xml.replace(RELATIONSHIP_TAG, (tag) => {
      const relationship = parseRelationships(tag, slideRelationships.relsPart)[0];
      if (!relationship || relationship.external) return tag;
      if (
        isRelationshipType(relationship, "notesSlide")
        || isRelationshipType(relationship, "comments")
        || isRelationshipType(relationship, "comment")
      ) {
        removedAnnotationRelationships += 1;
        return "";
      }
      return tag;
    });
    archive.file(slideRelationships.relsPart, cleanedRelationships);
  }

  const requiredLayouts = await requiredTargetsByType(archive, visibleSlideParts, "slideLayout");
  const requiredMasters = await requiredTargetsByType(archive, requiredLayouts, "slideMaster");
  const requiredNotesSlides = new Set();
  const requiredNotesMasters = new Set();

  const keepMasterIds = new Set();
  const keepNotesMasterIds = new Set();
  let removedPresentationRelationships = 0;
  let presentationRelsXml = presentationRelationships.xml.replace(RELATIONSHIP_TAG, (tag) => {
    const relationship = parseRelationships(tag, presentationRelationships.relsPart)[0];
    if (!relationship || relationship.external) return tag;
    const target = resolveArchivePart(archive, presentationPart, relationship.target);
    if (isRelationshipType(relationship, "slide")) {
      if (visibleSlideIds.has(relationship.id)) return tag;
      removedPresentationRelationships += 1;
      return "";
    }
    if (isRelationshipType(relationship, "slideMaster")) {
      if (requiredMasters.has(target)) {
        keepMasterIds.add(relationship.id);
        return tag;
      }
      removedPresentationRelationships += 1;
      return "";
    }
    if (isRelationshipType(relationship, "notesMaster")) {
      if (requiredNotesMasters.has(target)) {
        keepNotesMasterIds.add(relationship.id);
        return tag;
      }
      removedPresentationRelationships += 1;
      return "";
    }
    if (isRelationshipType(relationship, "handoutMaster")) {
      removedPresentationRelationships += 1;
      return "";
    }
    return tag;
  });

  const originalMasterIdCount = openingTags(presentationXml, "sldMasterId").length;
  const originalNotesMasterIdCount = openingTags(presentationXml, "notesMasterId").length;
  const originalHandoutMasterIdCount = openingTags(presentationXml, "handoutMasterId").length;
  presentationXml = filterIdTags(presentationXml, "sldMasterId", keepMasterIds);
  presentationXml = filterIdTags(presentationXml, "notesMasterId", keepNotesMasterIds);
  presentationXml = filterIdTags(presentationXml, "handoutMasterId", new Set());
  archive.file(presentationPart, presentationXml);
  archive.file(presentationRelationships.relsPart, presentationRelsXml);

  let removedLayoutRelationships = 0;
  let removedLayoutIds = 0;
  for (const masterPart of requiredMasters) {
    const masterEntry = archive.file(masterPart);
    if (!masterEntry) throw new Error(`PPTX缺少所需母版：${masterPart}`);
    let masterXml = await masterEntry.async("string");
    const masterRelationships = await readRelationships(archive, masterPart);
    const keepLayoutIds = new Set();
    const masterRelsXml = masterRelationships.xml.replace(RELATIONSHIP_TAG, (tag) => {
      const relationship = parseRelationships(tag, masterRelationships.relsPart)[0];
      if (!relationship || relationship.external || !isRelationshipType(relationship, "slideLayout")) return tag;
      const target = resolveArchivePart(archive, masterPart, relationship.target);
      if (requiredLayouts.has(target)) {
        keepLayoutIds.add(relationship.id);
        return tag;
      }
      removedLayoutRelationships += 1;
      return "";
    });
    const previousCount = openingTags(masterXml, "sldLayoutId").length;
    masterXml = filterIdTags(masterXml, "sldLayoutId", keepLayoutIds);
    removedLayoutIds += previousCount - openingTags(masterXml, "sldLayoutId").length;
    archive.file(masterPart, masterXml);
    archive.file(masterRelationships.relsPart, masterRelsXml);
  }

  return {
    visible_slide_count: visibleSlideParts.size,
    required_layout_count: requiredLayouts.size,
    required_master_count: requiredMasters.size,
    required_notes_slide_count: requiredNotesSlides.size,
    required_notes_master_count: requiredNotesMasters.size,
    removed_presentation_relationships: removedPresentationRelationships,
    removed_master_ids: originalMasterIdCount - keepMasterIds.size,
    removed_notes_master_ids: originalNotesMasterIdCount - keepNotesMasterIds.size,
    removed_handout_master_ids: originalHandoutMasterIdCount,
    removed_layout_relationships: removedLayoutRelationships,
    removed_layout_ids: removedLayoutIds,
    removed_annotation_relationships: removedAnnotationRelationships,
  };
}


async function buildReachability(archive) {
  const partNames = Object.keys(archive.files).filter((name) => !archive.files[name].dir);
  const partSet = new Set(partNames);
  const reachable = new Set();
  const brokenRelationships = [];
  const externalRelationships = [];
  if (partSet.has("[Content_Types].xml")) reachable.add("[Content_Types].xml");

  const queue = [""];
  const processedSources = new Set();
  while (queue.length) {
    const sourcePart = queue.shift();
    if (processedSources.has(sourcePart)) continue;
    processedSources.add(sourcePart);
    const { relsPart, relationships } = await readRelationships(archive, sourcePart);
    if (!partSet.has(relsPart)) {
      if (!sourcePart) brokenRelationships.push({ rels: relsPart, id: "", target: "" });
      continue;
    }
    reachable.add(relsPart);
    for (const relationship of relationships) {
      if (relationship.external) {
        externalRelationships.push({ rels: relsPart, id: relationship.id, type: relationship.type });
        continue;
      }
      const target = resolveArchivePart(archive, sourcePart, relationship.target);
      if (!partSet.has(target)) {
        brokenRelationships.push({ rels: relsPart, id: relationship.id, target: relationship.target });
        continue;
      }
      if (!reachable.has(target)) {
        reachable.add(target);
        queue.push(target);
      }
    }
  }

  return {
    partNames,
    reachable,
    unreachableParts: partNames.filter((name) => !reachable.has(name)),
    brokenRelationships,
    externalRelationships,
  };
}


function partCategory(name) {
  if (/^ppt\/slides\/slide\d+\.xml$/.test(name)) return "slides";
  if (name.startsWith("ppt/notesSlides/")) return "notes";
  if (name.startsWith("ppt/media/")) return "media";
  if (name.startsWith("ppt/slideMasters/")) return "masters";
  if (name.startsWith("ppt/slideLayouts/")) return "layouts";
  if (name.startsWith("ppt/comments/")) return "comments";
  if (name.startsWith("ppt/embeddings/")) return "embeddings";
  if (name.startsWith("ppt/charts/")) return "charts";
  if (name.startsWith("ppt/theme/")) return "themes";
  return "other";
}


function countByCategory(parts) {
  const result = {};
  for (const part of parts) {
    const category = partCategory(part);
    result[category] = (result[category] ?? 0) + 1;
  }
  return result;
}


async function localPathHits(archive) {
  const hits = [];
  for (const [name, entry] of Object.entries(archive.files)) {
    if (entry.dir || !/\.(?:xml|rels|json|txt|vml)$/i.test(name)) continue;
    const text = await entry.async("string");
    for (const [pattern, expression] of LOCAL_PATH_PATTERNS) {
      if (expression.test(text)) hits.push({ part: name, pattern });
    }
  }
  return hits;
}


async function visibleSlideCount(archive) {
  const entry = archive.file("ppt/presentation.xml");
  if (!entry) return 0;
  return openingTags(await entry.async("string"), "sldId").length;
}


async function inspectArchive(archive) {
  const reachability = await buildReachability(archive);
  return {
    file_count: reachability.partNames.length,
    reachable_part_count: reachability.reachable.size,
    unreachable_parts: reachability.unreachableParts,
    unreachable_parts_by_category: countByCategory(reachability.unreachableParts),
    broken_internal_relationships: reachability.brokenRelationships,
    external_relationship_count: reachability.externalRelationships.length,
    local_path_hits: await localPathHits(archive),
    visible_slide_count: await visibleSlideCount(archive),
  };
}


async function cleanContentTypes(archive) {
  const entry = archive.file("[Content_Types].xml");
  if (!entry) throw new Error("PPTX缺少[Content_Types].xml");
  const existing = new Set(Object.keys(archive.files).filter((name) => !archive.files[name].dir));
  const xml = await entry.async("string");
  const cleaned = xml.replace(/<Override\b[^>]*\/>/g, (tag) => {
    const partName = attributeValue(tag, "PartName").replace(/^\/+/, "");
    return existing.has(partName) ? tag : "";
  });
  archive.file("[Content_Types].xml", cleaned);
}


export async function inspectPptxPackage(pptxPath) {
  const archive = await JSZip.loadAsync(await fs.readFile(pptxPath), { checkCRC32: true });
  return inspectArchive(archive);
}


export async function sanitizePptxPackage(pptxPath, options = {}) {
  const archive = await JSZip.loadAsync(await fs.readFile(pptxPath), { checkCRC32: true });
  const presentationCleanup = await prunePresentationReferences(
    archive,
    options.keepSlideNumbers ?? null,
  );
  const before = await inspectArchive(archive);
  if (before.broken_internal_relationships.length) {
    throw new Error(`starter仍有无法解析的内部关系：${before.broken_internal_relationships.length}`);
  }
  for (const part of before.unreachable_parts) archive.remove(part);
  await cleanContentTypes(archive);

  const outputBuffer = await archive.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  const verifiedArchive = await JSZip.loadAsync(outputBuffer, { checkCRC32: true });
  const after = await inspectArchive(verifiedArchive);
  if (after.unreachable_parts.length) {
    throw new Error(`starter清理后仍有未引用OOXML部件：${after.unreachable_parts.length}`);
  }
  if (after.broken_internal_relationships.length) {
    throw new Error(`starter清理后仍有损坏的内部关系：${after.broken_internal_relationships.length}`);
  }
  if (after.local_path_hits.length) {
    throw new Error(`starter包含本机路径痕迹：${after.local_path_hits.length}`);
  }
  await fs.writeFile(pptxPath, outputBuffer);
  return {
    visible_slide_count: after.visible_slide_count,
    removed_part_count: before.unreachable_parts.length,
    removed_parts_by_category: before.unreachable_parts_by_category,
    unreachable_part_count: after.unreachable_parts.length,
    broken_internal_relationship_count: after.broken_internal_relationships.length,
    local_path_hit_count: after.local_path_hits.length,
    external_relationship_count: after.external_relationship_count,
    presentation_cleanup: presentationCleanup,
  };
}
