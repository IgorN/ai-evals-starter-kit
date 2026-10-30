# Your first eval: cases, outputs and a code grader

This small teaching example uses only the Python standard library. No packages, API key or network connection are needed. Its JSON format is specific to this example, not an eval framework standard.

It includes four cases: a review defect, its clean twin, retrieval with an expected document in the top three results and a workflow gate decision about a missing caller.

## Run it

Open a terminal in this directory and run:

```sh
python3 check.py --selftest
python3 check.py
```

The first command checks the grader against eight known good and bad outputs. The second replays handwritten outputs from `demo-results.json` against `cases.json`.

Expected output: `Grader selftest: 8/8 probes` and `Code contracts passed: 4/4`.

**This is an offline replay. It does not run a model, skill, search or workflow. A score of 4/4 says nothing about the quality of an LLM.** The demo outputs were written by hand, not generated from `expected`.

Exit codes: `0` means all selected code contracts passed, `1` means a mismatch and `2` means an input or configuration error. A missing output counts as a failure. An empty dataset, duplicate IDs or incompatible dataset versions do not count as success.

## What a case contains

`input` holds the task and context. `expected` holds the expected behavior. `grader` selects how to check the output.

There are two graders in this example:

- `decision_equals`: `output.decision` must match the expected token.
- `hit_at_k`: at least one allowed `expected.any_of_doc_ids` must appear among the first `k` entries in `output.doc_ids`.

A decision token checks the decision, not whether its explanation is correct. An agent may guess the token. A retrieval hit does not establish that the final answer is correct. These checks cover part of the evaluation, not the whole system.

## Connect real results

Before connecting your retrieval system, replace the example document IDs with verified IDs that exist in your corpus and choose a matching query. Nonexistent references make a case impossible to pass.

1. Write an adapter for your skill, retrieval or workflow. It reads the case and passes **only `input`** to the system. Do not put `expected` or `grader` into the prompt. That would leak the answers.
2. Save the actual result of each run under its `case_id`. A reviewer needs `output.decision`; retrieval needs `output.doc_ids` in ranking order. Also save the explanation and trace for investigation, even though this code grader does not score them.
3. Set `kind` to `"actual_run"`. Record `model`, `prompt_version`, `config` and `dataset_version` in `metadata`. Tool or skill version, time, trial ID and cost are also useful. Do not use demo metadata for a live result.
4. Check the saved results:

```sh
python3 check.py --results actual-results.json
```

This command checks a saved file. It does not call a model. Your adapter makes the real model calls, which may have a cost.

To compare versions, use the same dataset version and comparable settings and environments. Save the baseline before changing the prompt. Repeated runs show variability. Choose the number of repeats for your task; one successful run is not a guarantee.

The English dataset version is `demo-en-1`. Preserve this value in result metadata when using these cases.

## Where a judge or human is needed

Questions about meaning need a separate criterion. For example, does the reviewer's explanation follow from the code, or do the observations support the diagnosis? `judge-rubric-template.json` contains a report and tool-observation template with a criterion, PASS/FAIL, evidence and an exact quote check. It is not executed by `check.py` and does not include a model provider.

Validate the judge against human-labeled examples. Look separately at missed errors and false alarms. An exact quote is useful, but does not guarantee that its interpretation is correct.

Add cases where information is missing and success means stopping, asking for clarification or escalating. Define allowed decisions according to your task's contract. Do not require one token when several decisions are valid.

Keep some cases held out for evaluating the next version, rather than tuning the instructions. Clean twins and edge cases help reveal whether fixing one error has turned into an “always do X” rule.

After the first useful case, you can expand the set, choose a framework, store results in a database or run checks from CI. This example does not require or implement the shared framework described in the article.
