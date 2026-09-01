#!/usr/bin/env node
/** Create a path-portable, unpublished static-bundle manifest. */

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";


const [bundleRootArg, manifestPathArg, projectId, qaPathArg, mobilePathArg] = process.argv.slice(2);
const fail = (message) => {
  throw new Error(`UE static bundle manifest creation failed: ${message}`);
};
const sha256 = (value) => crypto.createHash("sha256").update(value).digest("hex");
const comparePathBytes = (left, right) => Buffer.compare(Buffer.from(left), Buffer.from(right));
const CSP = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'none'; font-src 'self' data:; media-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'self'; form-action 'none'";
const PRIVATE_PATTERN = /(?:\/Users\/|\/home\/|\/Applications\/|file:\/{2,3}|(?<![A-Za-z])[A-Za-z]:[\\/]|CODEX_WORKSPACE|@oai\/artifact-tool)/i;
const EXTERNAL_RESOURCE_PATTERN = /(?:src|href)\s*=\s*["']\s*(?:https?:)?\/\//i;
const TEXT_EXTENSIONS = new Set([".html", ".css", ".js", ".json", ".md", ".svg", ".txt"]);


if (!bundleRootArg || !manifestPathArg || !projectId || !qaPathArg || !mobilePathArg) {
  fail("usage: create_manifest.mjs BUNDLE_ROOT MANIFEST.json PROJECT_ID QA.md MOBILE_PATH");
}
if (!/^[a-z0-9][a-z0-9-]{2,80}$/.test(projectId)) fail("project id is invalid");

const bundleRoot = path.resolve(bundleRootArg);
const manifestPath = path.resolve(manifestPathArg);
const outputRoot = path.dirname(manifestPath);
const qaPath = path.resolve(qaPathArg);
if (path.dirname(bundleRoot) !== outputRoot || path.basename(bundleRoot) !== "site") {
  fail("bundle root must be the manifest sibling directory named site");
}
if (!fs.statSync(bundleRoot, { throwIfNoEntry: false })?.isDirectory()) fail("bundle root is unavailable");
if (!fs.statSync(qaPath, { throwIfNoEntry: false })?.isFile()) fail("QA file is unavailable");

const normalizeRelative = (value, label) => {
  const normalized = String(value || "").replaceAll("\\", "/").replace(/^\.\//, "");
  if (!normalized || path.posix.isAbsolute(normalized) || normalized.split("/").includes("..")) {
    fail(`${label} is unsafe`);
  }
  return normalized;
};
const mobilePath = normalizeRelative(mobilePathArg, "mobile path");
const qaRelative = normalizeRelative(path.relative(outputRoot, qaPath), "QA path");
if (path.resolve(outputRoot, qaRelative) !== qaPath) fail("QA file escaped output root");

const files = [];
const forbiddenHits = [];
const walk = (directory) => {
  const entries = fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => comparePathBytes(a.name, b.name));
  for (const entry of entries) {
    const absolute = path.join(directory, entry.name);
    if (entry.isSymbolicLink()) fail(`symbolic link is not allowed: ${entry.name}`);
    if (entry.isDirectory()) {
      walk(absolute);
      continue;
    }
    if (!entry.isFile()) fail(`unsupported bundle entry: ${entry.name}`);
    const relative = path.relative(bundleRoot, absolute).split(path.sep).join("/");
    const bytes = fs.readFileSync(absolute);
    if (TEXT_EXTENSIONS.has(path.extname(relative).toLowerCase())) {
      const text = bytes.toString("utf8");
      if (PRIVATE_PATTERN.test(text)) forbiddenHits.push(`${relative}:private_path`);
      if (EXTERNAL_RESOURCE_PATTERN.test(text)) forbiddenHits.push(`${relative}:external_resource`);
    }
    files.push({ path: relative, bytes: bytes.length, sha256: sha256(bytes) });
  }
};
walk(bundleRoot);
if (forbiddenHits.length) fail(`forbidden references: ${forbiddenHits.join(", ")}`);
if (!files.length) fail("bundle is empty");

const fileMap = new Map(files.map((file) => [file.path, file]));
for (const required of ["index.html", mobilePath, "project-data.js", "assets/app.js", "assets/styles.css"]) {
  if (!fileMap.has(required)) fail(`required bundle file is missing: ${required}`);
}
const indexText = fs.readFileSync(path.join(bundleRoot, "index.html"), "utf8");
if (!indexText.includes(CSP)) fail("index.html CSP does not match the locked offline policy");

const qaBytes = fs.readFileSync(qaPath);
const qaText = qaBytes.toString("utf8");
if (!/^final result: passed$/m.test(qaText)) fail("QA completion marker is missing");

const sortedFiles = files.sort((a, b) => comparePathBytes(a.path, b.path));
const treeInput = sortedFiles.map((file) => `${file.sha256}  ${file.path}\n`).join("");
const manifest = {
  manifestVersion: "residential-ue-static-bundle.v0.2",
  status: "local_bundle_verified",
  passed: true,
  publicationState: "not_published",
  projectId,
  bundlePath: "site",
  indexPath: "index.html",
  mobilePath,
  csp: CSP,
  treeSha256: sha256(Buffer.from(treeInput)),
  files: sortedFiles,
  qa: { path: qaRelative, sha256: sha256(qaBytes), result: "passed" },
  forbiddenReferenceScan: { privatePaths: 0, externalResources: 0 },
};
fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
process.stdout.write(`${manifest.treeSha256}\n`);
