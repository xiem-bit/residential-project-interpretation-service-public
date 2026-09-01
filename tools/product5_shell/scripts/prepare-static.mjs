#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "dist");
const desktop = readFileSync(path.join(dist, "index.html"), "utf8");
const mobile = desktop
  .replaceAll('src="./project-data.js"', 'src="../project-data.js"')
  .replaceAll('src="./assets/', 'src="../assets/')
  .replaceAll('href="./assets/', 'href="../assets/');

mkdirSync(path.join(dist, "m"), { recursive: true });
writeFileSync(path.join(dist, "m", "index.html"), mobile);
