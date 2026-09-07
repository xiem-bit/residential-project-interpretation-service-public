# Output and state contract

## Files by task

Base: `project-contract.md`, `fact-conflict-gap-register.json`, `product-enablement-matrix.json`, `production-receipt.json`.

- Product 1 only when enabled: `product1-competition-study.md`, `product1-competition-summary.json`.
- Product 2 only when enabled: `product2-buyer-decision-study.md`, `product2-buyer-decision-summary.json`.
- Complete Product 2 or UE solution: `semantic-core.json`, `super-competitiveness-plan.json` from current or authorized existing research.
- Product 3: chapter 2/3 contracts and `ue-solution-handoff.json`.
- Product 5: current interaction blueprint.

Disabled products have no empty files. Retain necessary judgments, page purpose, production items, scripts and assembly confirmation in existing inputs; these are not five new documents or approvals. Client prose and backend machine summaries stay separate.

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

## States for enabled work

Only record states corresponding to the enabled work. Product 1 does not require a semantic-core freeze, three SCs or UE proof.

Add `product2_complete`, `ue_solution_bridge_pass` or `product5_blueprint_pass` only for enabled branches. The public machine verifier can reject structural and reference defects; it cannot set `human_business_accepted`, publication, adoption or business-effect states.

## Carrier separation

Store presentation, web, rendering and publication outcomes only under `adapter_statuses`. Never infer a business state from them.
