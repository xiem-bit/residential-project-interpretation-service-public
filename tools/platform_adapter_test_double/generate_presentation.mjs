#!/usr/bin/env node
/** Generate a deliberately simple editable PPTX to prove the adapter round-trip. */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { sanitizePptxPackage } from "../product3_ppt_pipeline/automizer_adapter/pptx_package_safety.mjs";


const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ADAPTER_DIR = path.resolve(SCRIPT_DIR, "../product3_ppt_pipeline/automizer_adapter");
const requireFromAdapter = createRequire(path.join(ADAPTER_DIR, "package.json"));
const PptxGenJS = requireFromAdapter("pptxgenjs");


function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (!item.startsWith("--")) continue;
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) args[item.slice(2)] = true;
    else {
      args[item.slice(2)] = value;
      index += 1;
    }
  }
  return args;
}


function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}


function assertRequest(request) {
  if (request.schema !== "residential.presentation_request.v0.1") {
    throw new Error("unsupported presentation request schema");
  }
  if (!Array.isArray(request.pages) || !request.pages.length) {
    throw new Error("presentation request has no pages");
  }
  const pageIds = request.pages.map((page) => String(page.page_id || ""));
  if (pageIds.some((value) => !value) || new Set(pageIds).size !== pageIds.length) {
    throw new Error("presentation request page ids are missing or duplicated");
  }
  if (request.artifact_requirements?.editable !== true) {
    throw new Error("test adapter only accepts editable presentation requests");
  }
}


function addPage(pptx, page, index, total) {
  const slide = pptx.addSlide();
  const accent = ["315B63", "C97855", "6C7A52"][index % 3];
  slide.background = { color: "F5F1E8" };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 0.24,
    h: 7.5,
    line: { color: accent, transparency: 100 },
    fill: { color: accent },
  });
  slide.addText(`${page.page_id}  ·  ${page.role}`, {
    x: 0.72,
    y: 0.48,
    w: 11.7,
    h: 0.35,
    fontFace: "Arial",
    fontSize: 10,
    bold: true,
    color: accent,
    margin: 0,
    breakLine: false,
  });
  slide.addText(page.title, {
    x: 0.72,
    y: 1.05,
    w: 11.25,
    h: 1.1,
    fontFace: "Arial",
    fontSize: 26,
    bold: true,
    color: "1F2A2E",
    margin: 0,
    valign: "mid",
    breakLine: false,
    fit: "shrink",
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.72,
    y: 2.42,
    w: 11.2,
    h: 2.2,
    rectRadius: 0.08,
    line: { color: "D8D0C2", width: 1 },
    fill: { color: "FFFFFF", transparency: 4 },
  });
  slide.addText(page.key_message, {
    x: 1.02,
    y: 2.78,
    w: 10.6,
    h: 1.45,
    fontFace: "Arial",
    fontSize: 20,
    color: "26363B",
    margin: 0.04,
    valign: "mid",
    breakLine: false,
    fit: "shrink",
  });
  slide.addText(`视觉任务：${page.visual_brief}`, {
    x: 0.72,
    y: 4.98,
    w: 11.2,
    h: 0.75,
    fontFace: "Arial",
    fontSize: 12,
    color: "556268",
    margin: 0,
    breakLine: false,
    fit: "shrink",
  });
  slide.addText(`证据 ${page.evidence_refs.join(" / ")}`, {
    x: 0.72,
    y: 6.28,
    w: 9.5,
    h: 0.35,
    fontFace: "Arial",
    fontSize: 9,
    color: "687277",
    margin: 0,
    breakLine: false,
  });
  slide.addText(`${index + 1} / ${total}`, {
    x: 10.9,
    y: 6.28,
    w: 1,
    h: 0.35,
    fontFace: "Arial",
    fontSize: 9,
    color: "687277",
    align: "right",
    margin: 0,
    breakLine: false,
  });
}


async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.request || !args.out || !args.response) {
    throw new Error("usage: generate_presentation.mjs --request request.json --out result.pptx --response response.json");
  }
  const requestPath = path.resolve(args.request);
  const outputPath = path.resolve(args.out);
  const responsePath = path.resolve(args.response);
  const responseDir = path.dirname(responsePath);
  if (path.dirname(outputPath) !== responseDir) {
    throw new Error("output and response must share one directory so all returned paths remain relative");
  }

  const requestBytes = await fs.readFile(requestPath);
  const request = JSON.parse(requestBytes.toString("utf8"));
  assertRequest(request);
  await fs.mkdir(responseDir, { recursive: true });

  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Residential Competitiveness Public Core";
  pptx.company = "Fictional RC1 Fixture";
  pptx.subject = "Platform adapter contract round-trip";
  pptx.title = `${request.project_id} fictional adapter output`;
  pptx.lang = "zh-CN";
  pptx.theme = {
    headFontFace: "Arial",
    bodyFontFace: "Arial",
    lang: "zh-CN",
  };
  request.pages.forEach((page, index) => addPage(pptx, page, index, request.pages.length));
  await pptx.writeFile({ fileName: outputPath });
  const packageSafety = await sanitizePptxPackage(outputPath);

  const preview = {
    schema: "residential.presentation_text_snapshot.v0.1",
    notice: "Interface test evidence only; formal visual review was not performed.",
    pages: request.pages.map((page, index) => ({
      page_id: page.page_id,
      slide_number: index + 1,
      title: page.title,
      key_message: page.key_message,
      visual_brief: page.visual_brief,
      acceptance: page.acceptance,
    })),
  };
  const previewPath = path.join(responseDir, "presentation-preview.json");
  await fs.writeFile(previewPath, `${JSON.stringify(preview, null, 2)}\n`, "utf8");

  const artifactBytes = await fs.readFile(outputPath);
  const response = {
    schema: "residential.presentation_response.v0.1",
    status: "test_double_complete",
    producer: {
      kind: "platform_contract_test_double",
      platform: "standard_node_pptxgenjs",
      formal_visual_renderer: false,
    },
    request_sha256: sha256(requestBytes),
    artifact: {
      path: path.basename(outputPath),
      media_type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      editable: true,
      slide_count: request.pages.length,
      sha256: sha256(artifactBytes),
    },
    page_mapping: request.pages.map((page, index) => ({
      page_id: page.page_id,
      slide_number: index + 1,
      object_ids: [`${page.page_id}:title`, `${page.page_id}:message`, `${page.page_id}:evidence`],
      super_competitiveness_refs: page.super_competitiveness_refs,
    })),
    visual_evidence: {
      kind: "text_snapshot",
      path: path.basename(previewPath),
      sha256: sha256(await fs.readFile(previewPath)),
      formal_visual_review: "not_evaluated_test_double",
    },
    qa: {
      contract_roundtrip: "pass",
      editable_pptx_created: true,
      package_safety: packageSafety,
    },
    gaps: [
      {
        code: "FORMAL_VISUAL_REVIEW_REQUIRED",
        responsibility: "selected_platform_adapter_or_human",
        blocking_for_contract_roundtrip: false,
        blocking_for_real_client_delivery: true,
        message: "Replace this test double with the selected platform and return page previews plus formal visual review evidence.",
      },
    ],
  };
  await fs.writeFile(responsePath, `${JSON.stringify(response, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify({ status: response.status, slides: request.pages.length })}\n`);
}


await main();

