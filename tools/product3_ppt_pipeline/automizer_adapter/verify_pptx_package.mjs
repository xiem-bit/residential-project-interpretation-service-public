import path from "node:path";
import { inspectPptxPackage } from "./pptx_package_safety.mjs";


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


async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.pptx) throw new Error("需要--pptx");
  const inspection = await inspectPptxPackage(path.resolve(args.pptx));
  const expectedSlides = args["expected-slides"] === undefined
    ? null
    : Number(args["expected-slides"]);
  if (expectedSlides !== null && (!Number.isInteger(expectedSlides) || expectedSlides < 1)) {
    throw new Error("--expected-slides必须是正整数");
  }
  const failures = [];
  if (inspection.unreachable_parts.length) {
    failures.push(`存在${inspection.unreachable_parts.length}个未引用OOXML部件`);
  }
  if (inspection.broken_internal_relationships.length) {
    failures.push(`存在${inspection.broken_internal_relationships.length}个损坏的内部关系`);
  }
  if (inspection.local_path_hits.length) {
    failures.push(`存在${inspection.local_path_hits.length}处本机路径痕迹`);
  }
  if (expectedSlides !== null && inspection.visible_slide_count !== expectedSlides) {
    failures.push(`可见页数${inspection.visible_slide_count}与期望${expectedSlides}不一致`);
  }
  const report = {
    schema: "pptx.package_safety_report.v0.1",
    status: failures.length ? "fail" : "pass",
    pptx: path.basename(args.pptx),
    expected_slide_count: expectedSlides,
    visible_slide_count: inspection.visible_slide_count,
    package_file_count: inspection.file_count,
    unreachable_part_count: inspection.unreachable_parts.length,
    unreachable_parts_by_category: inspection.unreachable_parts_by_category,
    broken_internal_relationship_count: inspection.broken_internal_relationships.length,
    local_path_hit_count: inspection.local_path_hits.length,
    external_relationship_count: inspection.external_relationship_count,
    failures,
  };
  console.log(JSON.stringify(report, null, 2));
  if (failures.length) process.exitCode = 1;
}


await main();
