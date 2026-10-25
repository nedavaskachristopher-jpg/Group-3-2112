# Delivery and review tests

This suite checks aggregate-derived exports, numerical provenance, broken links,
tampered CSVs and the root review entry point. Original scientific checks live
in [research/tests/](../research/tests/README.md).

- [test_handover.py](test_handover.py): report values come from evidence;
  altered CSVs, undefined-metric substitutions and invalid links are detected.
- [test_review.py](test_review.py): cached-result access rejects incomplete or
  tampered records, avoids private data and works from another directory.
- [test_applications.py](test_applications.py): private-model identity, input and
  heldout-date guards, raw tied-score decisions, no-fit inference, cache-only
  mapping and read-only notebook replay.

Run both suites with `python review.py test` from the repository root after
installing `research/requirements.txt`. Tests use synthetic fixtures or public
aggregates; they do not repeat final prediction or parse private labels.
