# Leaderboards

Each directory below is a complete leaderboard maintenance boundary: source and
scope documentation, pinned data preparation, native Harbor tasks, agent job
YAML, canonical scoring source, and regression tests.

| Leaderboard | Formal scope | Development/diagnostic scope | Formal job |
|---|---|---|---|
| [BioDSBench](biodsbench/README.md) | 118 Python biomedical data-analysis items | 165 R items inventoried, runtime unsupported | `biodsbench/jobs/dswizard.yaml` |
| [Biomedical Deep Research](biomedicine-deep-research/README.md) | Verifier-split exact-match and evidence-gap recall@30 across 13 ranked subsets | fit, tune, smoke, and all-split diagnostic | `biomedicine-deep-research/jobs/deepevidence.yaml` |

A benchmark folder is a leaderboard. A dataset or native subset inside it is a
Harbor task. One Harbor trial installs an agent once and processes task items in
separate child processes and workspaces. Biomedical Deep Research uses micro
accuracy over its trusted formal selection rather than averaging task rewards.
