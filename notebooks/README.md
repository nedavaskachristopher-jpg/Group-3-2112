# Cached-result notebook

[ML_Review.ipynb](ML_Review.ipynb) displays the completed revised study and its
unfavourable results. Its four executed code cells use public aggregates and
the Python standard library only. They do not read raw labels, load a model,
train or run predictions. The map is an existing cached-score figure.

Regenerate with `python -m tools.build_notebook`. Normal report regeneration is
documented in the runbook. Use `python review.py verify` after rebuilding exports.
The original executable
training notebook remains at tag `legacy-ml-2026-10-25`.
