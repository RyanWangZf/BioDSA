# BioDSBench Python Harbor mix

These four native Harbor tasks come from `zifeng-ai/BioDSBench` revision
`e59af82ee9461db78ed399544ec8520afeb02ce5`, study `27959731`. Run
`python3 scripts/fetch_biodsbench_harbor_data.py` once before Harbor. It stages
the real public tables into each Docker build context; generated CSV files are
ignored by Git.

The agent must submit `/app/submission/analysis.py`. The separate verifier runs
that program against the same public inputs and applies the record's original
assertions. A missing or invalid submission scores zero. An infrastructure
failure produces no reward and remains a Harbor verifier error.
