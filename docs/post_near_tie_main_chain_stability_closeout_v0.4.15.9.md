# v0.4.15.9 Post Near-Tie Main-Chain Stability Closeout

## Scope

v0.4.15.9 is a stability closeout for the v0.4.15.8 main-chain repair. It does not modify retriever code, prompts, anchors, risk supplement rules, term preservation rules, hidden seeds, scenario registry, fixtures, or eval cases.

## What Was Checked

The first attempted command was a 3-run full RAG repeat. It exceeded the local execution window before writing a complete report, so the run was stopped and no partial artifact was committed.

The validation was then narrowed to a more practical stability packet:

- `tests/targeted_main_chain_stability_v0.4.15.9_report.json`
  - 8 high-risk or recently unstable cases
  - 3 repeats
  - pass counts: `[8, 8, 8]`
  - `all_runs_full_pass=true`
  - `unstable_cases=[]`
- `tests/post_near_tie_main_chain_full_eval_v0.4.15.9_report.json`
  - single full RAG eval
  - 59/60 passed
  - retrieval stage summary: `PASS=60`
- `tests/targeted_data_export_answer_stability_v0.4.15.9_report.json`
  - `data_export_contract_trigger_001`
  - 5 repeats
  - pass counts: `[1, 1, 1, 1, 1]`
  - `all_runs_full_pass=true`

## Interpretation

The single full eval failure was `data_export_contract_trigger_001`. The evidence check passed and the expected Article 8 evidence was selected, but the answer text missed the exact keyword `补充订立` in that single run.

The follow-up 5-run targeted repeat for the same case passed every run. Therefore v0.4.15.9 treats this as output wording variance, not a retrieval or evidence-chain regression.

## Decision

No runtime patch was made in this version.

The main RAG evidence path remains stable enough to close v0.4.15 near-tie repair work:

- targeted stability packet: all pass
- single full eval retrieval stage: all pass
- data-export wording follow-up: all pass

The next engineering work should focus on answer wording stability or report-generation discipline if the project wants to eliminate single-run keyword variance. That work must not be solved by changing eval cases, prompts, anchors, hidden seeds, or risk supplement rules without a separate authorization.
