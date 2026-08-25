import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import test from "node:test";


const execFileAsync = promisify(execFile);
const TEST_DIR = path.dirname(fileURLToPath(import.meta.url));
const CREATE = path.resolve(TEST_DIR, "../create_manifest.mjs");
const VERIFY = path.resolve(TEST_DIR, "../verify_manifest.mjs");
const CSP = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'none'; font-src 'self' data:; media-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'self'; form-action 'none'";


async function makeFixture(marker = "safe") {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "public-ue-bundle-test-"));
  const site = path.join(root, "site");
  await fs.mkdir(path.join(site, "assets"), { recursive: true });
  await fs.mkdir(path.join(site, "m"), { recursive: true });
  await fs.writeFile(
    path.join(site, "index.html"),
    `<!doctype html><meta http-equiv="Content-Security-Policy" content="${CSP}"><script src="project-data.js"></script><script src="assets/app.js"></script>`,
  );
  await fs.writeFile(path.join(site, "m/index.html"), "<!doctype html><p>mobile</p>");
  await fs.writeFile(path.join(site, "project-data.js"), `window.fixture = ${JSON.stringify(marker)};`);
  await fs.writeFile(path.join(site, "assets/app.js"), "document.documentElement.dataset.ready = 'true';");
  await fs.writeFile(path.join(site, "assets/styles.css"), "body { color: #123; }");
  await fs.writeFile(path.join(root, "delivery-qa.md"), "final result: passed\n");
  return {
    root,
    site,
    manifest: path.join(root, "bundle-manifest.json"),
    qa: path.join(root, "delivery-qa.md"),
  };
}


async function create(fixture) {
  return execFileAsync(process.execPath, [
    CREATE,
    fixture.site,
    fixture.manifest,
    "fictional-bundle-test",
    fixture.qa,
    "m/index.html",
  ]);
}


test("portable manifest verifies and rejects a later bundle mutation", async () => {
  const fixture = await makeFixture();
  try {
    await create(fixture);
    const manifest = JSON.parse(await fs.readFile(fixture.manifest, "utf8"));
    assert.equal(manifest.qa.path, "delivery-qa.md");
    await execFileAsync(process.execPath, [VERIFY, fixture.manifest, fixture.site]);
    await fs.writeFile(path.join(fixture.site, "assets/app.js"), "document.body.textContent = 'tampered';");
    await assert.rejects(execFileAsync(process.execPath, [VERIFY, fixture.manifest, fixture.site]));
  } finally {
    await fs.rm(fixture.root, { recursive: true, force: true });
  }
});


test("manifest creation rejects a private absolute path in bundle text", async () => {
  const fixture = await makeFixture("/Users/example/private-source");
  try {
    await assert.rejects(create(fixture), (error) => {
      assert.match(error.stderr, /forbidden references/);
      return true;
    });
  } finally {
    await fs.rm(fixture.root, { recursive: true, force: true });
  }
});

