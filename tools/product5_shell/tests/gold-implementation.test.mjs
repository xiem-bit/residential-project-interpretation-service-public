import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

async function loadConfig() {
  const source = await readFile(path.join(root, "public/project-data.js"), "utf8");
  const sandbox = { window: {} };
  vm.runInNewContext(source, sandbox);
  return sandbox.window.__PROJECT_DATA__;
}

test("public-safe gold config contains the complete interaction model", async () => {
  const config = await loadConfig();
  assert.equal(config.schema, "residential.product5_config.v0.1");
  assert.equal(config.publication_state, "not_published");
  assert.deepEqual(
    Array.from(config.experience.chapters, (item) => item.id),
    ["home", "city", "community", "living", "advisor"],
  );
  assert.equal(config.experience.advisor.questions.length, 4);
  assert.equal(config.experience.advisor.routes.length, 3);
  for (const route of config.experience.advisor.routes) {
    assert.equal(route.reasons.length, 3);
    assert.equal(route.visit.length, 3);
    assert.equal(route.compare.length, 2);
    assert.ok(route.next.length > 20);
  }
});

test("built output keeps desktop, mobile and offline-safe entrypoints", async () => {
  const desktop = await readFile(path.join(root, "dist/index.html"), "utf8");
  const mobile = await readFile(path.join(root, "dist/m/index.html"), "utf8");
  const app = await readFile(path.join(root, "dist/assets/app.js"), "utf8");
  assert.match(desktop, /connect-src 'none'/);
  assert.match(desktop, /project-data\.js/);
  assert.match(mobile, /\.\.\/project-data\.js/);
  assert.match(app, /#\/m\//);
  assert.doesNotMatch(desktop + mobile, /(?:src|href)=["'](?:https?:)?\/\//);
});

test("public source has no client project or publication residue", async () => {
  const files = ["src/App.jsx", "src/data.js", "public/project-data.js", "README.md"];
  const text = (await Promise.all(files.map((file) => readFile(path.join(root, file), "utf8")))).join("\n");
  assert.doesNotMatch(text, /翠湖|碧桂园|云顶|ops\.myhcec|天翼云|\/Users\//);
});
