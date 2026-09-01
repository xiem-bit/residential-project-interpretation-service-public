# Output and state contract

## Base required run files

1. `project-contract.md`
2. `fact-conflict-gap-register.json`
3. `product1-competition-study.md`
4. `semantic-core.json`
5. `super-competitiveness-plan.json`
6. `product-enablement-matrix.json`
7. `production-receipt.json`

## Conditional files

- Product 2: `product2-buyer-decision-study.md`
- Product 3: `product3-chapter2-contract.json`, `product3-chapter3-contract.json`, `ue-solution-handoff.json`
- Product 4: `product4-value-framework-contract.json`
- Product 5: `product5-interaction-blueprint.json`
- Material semantic change only: `change-impact-registry.json`

Only enabled product files may exist. Disabled products are explained in the project contract and enablement matrix; they do not get empty placeholders. Markdown reports begin with a JSON summary block and retain human-readable analysis below it.

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

`rules_loaded → project_identity_closed → product1_complete → semantic_core_frozen → minimum_three_sc_pass → cross_product_consistency_pass`

Add `product2_complete`, `ue_solution_bridge_pass`, `product4_contract_pass` or `product5_blueprint_pass` only for enabled branches. The public machine verifier can reject structural and reference defects; it cannot set `human_business_accepted`, publication, adoption or business-effect states.

## Carrier separation

Store presentation, web, XMind, rendering and publication outcomes only under `adapter_statuses`. Never infer a business state from them.
