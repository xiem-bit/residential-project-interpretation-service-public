#!/usr/bin/env node
/** Independently verify a static-bundle manifest without project-specific runtime. */

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";


const [manifestPathArg, bundleRootArg] = process.argv.slice(2);
const fail = (message) => {
  throw new Error(`UE static bundle manifest rejected: ${message}`);
};
const sha256 = (value) => crypto.createHash("sha256").update(value).digest("hex");
const comparePathBytes = (left, right) => Buffer.compare(Buffer.from(left), Buffer.from(right));
const CSP = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'none'; font-src 'self' data:; media-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'self'; form-action 'none'";


if (!manifestPathArg || !bundleRootArg) fail("usage: verify_manifest.mjs MANIFEST.json BUNDLE_ROOT");
const manifestPath = path.resolve(manifestPathArg);
const outputRoot = path.dirname(manifestPath);
const bundleRoot = path.resolve(bundleRootArg);
if (!fs.statSync(manifestPath, { throwIfNoEntry: false })?.isFile()) fail("manifest is unavailable");
if (!fs.statSync(bundleRoot, { throwIfNoEntry: false })?.isDirectory()) fail("bundle root is unavailable");
if (path.dirname(bundleRoot) !== outputRoot || path.basename(bundleRoot) !== "site") {
  fail("bundle root must be the manifest sibling directory named site");
}

const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
if (manifest.manifestVersion !== "residential-ue-static-bundle.v0.2") fail("manifest version is unsupported");
if (manifest.status !== "local_bundle_verified" || manifest.passed !== true) fail("manifest is not verified");
if (manifest.publicationState !== "not_published") fail("publicationState must be not_published");
if (manifest.bundlePath !== "site" || manifest.indexPath !== "index.html" || manifest.csp !== CSP) {
  fail("bundle entrypoint or CSP is invalid");
}

const normalizeRelative = (value, label) => {
  const normalized = String(value || "").replaceAll("\\", "/").replace(/^\.\//, "");
  if (!normalized || path.posix.isAbsolute(normalized) || normalized.split("/").includes("..")) {
    fail(`${label} is unsafe`);
  }
  return normalized;
};

const actual = [];
const walk = (directory) => {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => comparePathBytes(a.name, b.name))) {
    const absolute = path.join(directory, entry.name);
    if (entry.isSymbolicLink()) fail(`symbolic link is not allowed: ${entry.name}`);
    if (entry.isDirectory()) walk(absolute);
    else if (entry.isFile()) actual.push(path.relative(bundleRoot, absolute).split(path.sep).join("/"));
    else fail(`unsupported bundle entry: ${entry.name}`);
  }
};
walk(bundleRoot);

if (!Array.isArray(manifest.files) || !manifest.files.length) fail("file manifest is missing");
const expectedPaths = manifest.files.map((file) => normalizeRelative(file.path, "file path"));
if (new Set(expectedPaths).size !== expectedPaths.length) fail("file manifest contains duplicates");
if (actual.sort(comparePathBytes).join("\n") !== [...expectedPaths].sort(comparePathBytes).join("\n")) {
  fail("bundle file set differs from the locked manifest");
}

const verified = [];
for (const file of manifest.files) {
  const relative = normalizeRelative(file.path, "file path");
  const absolute = path.resolve(bundleRoot, relative);
  if (!absolute.startsWith(`${bundleRoot}${path.sep}`)) fail(`file escaped bundle root: ${relative}`);
  const bytes = fs.readFileSync(absolute);
  const digest = sha256(bytes);
  if (file.bytes !== bytes.length || file.sha256 !== digest) fail(`file mismatch: ${relative}`);
  verified.push({ path: relative, sha256: digest });
}
for (const required of ["index.html", normalizeRelative(manifest.mobilePath, "mobile path"), "project-data.js", "assets/app.js", "assets/styles.css"]) {
  if (!verified.some((file) => file.path === required)) fail(`required file is missing: ${required}`);
}
const treeInput = verified.sort((a, b) => comparePathBytes(a.path, b.path)).map((file) => `${file.sha256}  ${file.path}\n`).join("");
if (sha256(Buffer.from(treeInput)) !== manifest.treeSha256) fail("tree hash mismatch");

const qaRelative = normalizeRelative(manifest.qa?.path, "QA path");
const qaPath = path.resolve(outputRoot, qaRelative);
if (!qaPath.startsWith(`${outputRoot}${path.sep}`) || !fs.statSync(qaPath, { throwIfNoEntry: false })?.isFile()) {
  fail("QA file is unavailable");
}
const qaBytes = fs.readFileSync(qaPath);
if (sha256(qaBytes) !== manifest.qa.sha256 || manifest.qa.result !== "passed") fail("QA mismatch");
if (!/^final result: passed$/m.test(qaBytes.toString("utf8"))) fail("QA completion marker is missing");
if (manifest.forbiddenReferenceScan?.privatePaths !== 0 || manifest.forbiddenReferenceScan?.externalResources !== 0) {
  fail("forbidden reference scan is not clean");
}
process.stdout.write(`${JSON.stringify({ status: "pass", files: verified.length, treeSha256: manifest.treeSha256 })}\n`);

