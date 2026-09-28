# PREREG #216 — "confirmed" field for the facts extractor (written BEFORE any run, 2026-09-27)

**Question:** does adding a `"confirmed"` list (known facts the chat shows are still true) let the
extractor refresh facts, without hurting new-fact extraction or output-length safety?
**Arms:** HEAD = shipped `sys` (amadeus.html by anchor). ARM = HEAD transformed in memory by
`dev/facts_arm_probe.js` (`armPrompt`): schema gains `,"confirmed":["<exact KNOWN FACT text>"]` after
`facts`; one sentence says what goes there and not to repeat it in `facts`; the empty answer becomes
`{"facts":[],"confirmed":[]}`. temp 0.2, num_ctx 8192, format json, seeds 1000..1029 (paired).
**Fixtures** (in the probe): `real` (4800 chars, 3 new facts, no known), `mention` (10 known facts;
chat re-mentions K1–K3 in other words, adds 1 new dated fact, never touches K4–K10) as `mention-close`
(4800 chars, num_predict 800) and `mention-idle` (last 12 lines, 500), `light` (no facts, same 10
known, 500), `dense` (20 facts, 40 known, 800).
**Matching:** a confirmed string counts only if `_normFact` equals a known fact exactly (the shipped
matcher). Paraphrases count as "no match" and are reported.

| # | Fixture | Pass level for ARM |
|---|---|---|
| 1 | real @800 | 3/3 new facts in ≥29/30; 0/30 cut |
| 2 | mention-close @800 | mean recall of K1–K3 ≥70%; false confirms (K4–K10) ≤5% of 210 slots; new fact in ≥29/30; 0/30 cut |
| 3 | mention-idle @500 | same as 2 |
| 4 | light @500 | `facts` empty in ≥29/30; false confirms ≤5% of 300 slots |
| 5 | dense @800 | ≤2/30 cut |
HEAD is run on 1–4 for comparison (dense HEAD is already measured: 1/30 cut, backlog #202).
**Decision:** all 5 pass → ship A+B. Any fail → ship A + refresh on duplicate/replace only (B without
the prompt change), and report. No re-runs to "rescue" an arm; a changed arm is a new pre-registration.

## RESULTS (2026-09-27, n=30 per cell, seeds 1000–1029, app closed) — ARM FAILS; decision branch applies
| # | Fixture | HEAD | ARM | Pass level | Verdict |
|---|---|---|---|---|---|
| 1 | real @800 | 30/30 all 3, 0 cut, eval 138 | 30/30 all 3, 0 cut, eval 193 | ≥29, 0 cut | pass — but ARM copied HIS LINES into `confirmed` (no known facts existed) |
| 2 | mention-close @800 | recall 0, FP 0, new 30/30 | recall 1.00, **FP 1.00**, new 30/30, 0 cut | FP ≤5% | **FAIL** |
| 3 | mention-idle @500 | recall 0, FP 0, new 30/30 | recall 1.00, **FP 1.00**, new 30/30, 0 cut | FP ≤5% | **FAIL** |
| 4 | light @500 | empty 30/30 | empty 30/30, FP 0 | ≥29, FP ≤5% | pass |
| 5 | dense @800 | 1/30 cut (backlog #202) | **27/30 cut**, eval 800, 26.6s median | ≤2/30 | **FAIL** |
Raw: `dev/facts_arms/216_*.json`. In cells 2–3 every run returned all 10 known facts as confirmed —
gemma4 treats "confirmed" as "known and not contradicted", not "mentioned again". It confirms nothing
only when the chat has no fact talk at all (cell 4).
**Decision (pre-registered):** ship A + refresh on duplicate/replace only. No rescue re-run.
**Consequence found while reading the results:** without a working confirmation, `seen` almost never
moves, so an A note saying "last MENTIONED" would be false for a fact he talks about weekly. A's
wording must say what the data can support: when the fact was LEARNED (or last replaced).
