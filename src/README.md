# Compatibility commands

Current research code is in [research/](../research/README.md). Use
`python review.py results`, `verify` and `test` at the root for normal review.

- `python src/verify_results.py` runs the current read-only public verifier.
- `python src/predict.py` delegates to the [explicit frozen-model interface](../applications/README.md).

The legacy training, notebook, packaging and self-repairing verification scripts
are preserved at tag `legacy-ml-2026-10-25`. They are not active review commands.
No wrapper retrains, exports UBJ files or silently evaluates the final test.
