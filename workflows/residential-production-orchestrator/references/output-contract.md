# Output and state contract

## Required run files

1. `project-contract.md`
2. `fact-conflict-gap-register.json`
3. `product1-competition-study.md`
4. `product2-buyer-decision-study.md`
5. `semantic-core.json`
6. `super-competitiveness-plan.json`
7. `product-enablement-matrix.json`
8. `product3-chapter2-contract.json`
9. `product3-chapter3-contract.json`
10. `ue-solution-handoff.json`
11. `change-impact-registry.json`
12. `production-receipt.json`

The three Markdown files begin with a JSON summary block. Keep the human-readable analysis below it; do not replace the report with JSON only.

## Stable identifiers

- Evidence, facts and gaps: `E-*`, `GAP-*`, `CONFLICT-*`
- Competitors or options: `COMP-*`
- Customer decisions: `CD-*`
- Purchase tasks: `TASK-*`
- Target groups: `TG-*`
- Super competitiveness: `SC-*`
- Production items: `ITEM-*`
- UE scenes: `UE-*`
- Customer routes: `ROUTE-*`
- System modules: `MODULE-*`
- Changes: `CHANGE-*`

Reuse an ID while its meaning remains stable. When meaning changes, create a new semantic version and explicitly supersede the old judgment.

## State order

`rules_loaded → project_identity_closed → product1_complete → product2_complete_or_not_enabled → semantic_core_frozen → minimum_three_sc_pass → business_judgment_blind_review_pass → ue_solution_bridge_pass → cross_product_consistency_pass → production_path_replication_pass`

The public machine verifier may confirm all structural states except `business_judgment_blind_review_pass` and `production_path_replication_pass`. Only the independent hidden-answer protocol may set those two to pass.

## Carrier separation

Store presentation, web, XMind, rendering and publication outcomes only under `adapter_statuses`. Never infer a business state from them.
