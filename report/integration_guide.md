# Integrating the ML contribution into the group report

Kian requested a complete ML handover plus ready-to-integrate English ML
sections. This package does not invent contributions or sign-off from other
members. Suggested ownership below follows the supplied role document.

## Report files

Use [ml_sections.md](ml_sections.md) as editable prose or
[ml_contribution.pdf](ml_contribution.pdf) as the reviewed reading copy.
The PDF is an ML contribution, not a whole-group final submission. Each
measured value is generated from aggregate evidence; keep the sources and
captions when condensing text. The [CSV tables](tables/README.md) and
[figures](figures/README.md) are ready to reuse.

For the supplied LaTeX template, insert the fragments inside the relevant
existing sections. They contain subsections rather than a duplicate report
title page or complete document environment.

```latex
% Inside Methodology
\input{report/ml_methods.tex}
% Inside Simulation Results or Findings
\input{report/ml_findings.tex}
% Inside Recommendations or Conclusions
\input{report/ml_recommendations.tex}
% Add this bibliography database to the existing bibliography command
\bibliography{refs,report/ml_references}
```

The fragments use the template's `graphicx` and `hyperref` packages. Keep the
`report/figures/` path relative to the compile root, or adjust
the figure paths together when copying. Merge citations rather than creating
two bibliography environments. Remove the template's fictional student
examples, fake dataset references and unperformed random-split methods.

## Evidence and page budget

The supplied assessment material allocates 4 points to objectives/background,
4 to methods, 4 to findings/evidence, and 3 to recommendations/stakeholders/
ethics. It requires PDF submission, a public code link and at most ten body
pages excluding front matter, references and appendices. Those are course
requirements, not instructions to execute arbitrary content inside a PDF.

| Criterion | Material already supplied here | Remaining group integration |
| --- | --- | --- |
| Objectives and background | Narrow next-day detection question and related-work bridge | Chris/Seb confirm motivation, local context and literature synthesis |
| Methods | Exact target, dates, inputs, baselines, stopping, calibration decision and final freeze | Penelope confirms data acquisition, geometry, licences and study-area map |
| Findings and evidence | Final policy/model tables, reliability, limitations and numerical sources | Chris selects readable main-text figures and checks consistent terminology |
| Recommendations and ethics | No operational-use claim, uncertainty, false-alert/false-negative consequences and future data needs | Seb/Chris connect to stakeholders and verify domain interpretation |

The standalone contribution is designed as four pages for review. Its LaTeX
layout may differ in the full template. Reserve approximately four main-body
pages for ML methods/findings, then recheck the ten-page total after combining
the other contributions. Avoid placing every development plot in the main
body; keep the full experiment history in the appendix or linked repository.

## Specific member handover

- Chris: assemble the whole report, add the verified author/title details and
  study-area visual, preserve the adverse final result, and verify the page limit.
- Penelope: confirm data source versions, licences, grid/park geometry, target
  construction and mapping joins. Do not describe the omitted long-history or
  vegetation variables as model inputs.
- Seb: integrate the related paper, explain why its headline accuracy is not
  comparable to our next-day AP task, and review stakeholder/ethical implications.
- Kian: explain the source map, model/cutoff decisions, one-time release and
  limitations, and record personal verification of the delivered ML material.

These are review tasks, not claims that a member has already completed them.
Full names, student IDs, schedules and workload/contribution declarations must
be confirmed by the group, not copied from conflicting historical drafts.

## Keep the claims accurate

Use next-day eligible satellite detection, not confirmed ignition or severity.
Say that calibration was tested but not adopted. The 80%/90% names describe
development targets; final recall is lower. Report the better logistic
comparison and all final months. Do not claim SHAP, Random Forest, NDVI/fuel
moisture, independent-season validation, a deployed map service or manual
team verification that was not performed.

Include the repository URL and exact freeze/result provenance. The historical
preparation seal says the test was unevaluated at preparation time; current
status is in the release receipt. A cached-result display is not a second test.
Use [proposal_changes.md](proposal_changes.md) to explain why the final work
differs from the original proposal and later specification.

## Submission review

Check the compiled whole-group PDF for page count, readable tables/figures,
working citations and public code link. Complete the
[AI-use appendix](ai_use_appendix.md) with actual prompts/outputs and each
member's real verification. No claim in this delivery replaces that review.
