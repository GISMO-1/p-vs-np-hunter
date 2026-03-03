# conjecture_engine

LLM-guided conjecture synthesis and validation for complexity theory.

## Components

- **ConjectureGenerator**: calls Anthropic Messages API (`claude-sonnet-4-20250514`) to request formal conjectures with falsification paths.
- **Small-case tester**: runs finite checks (`n=2..5`) and integrates lower-bound evidence from `lower_bound_hunter`.
- **Literature-aware metadata**: conjectures track related results and implications.
- **Ranking engine**: deterministic scoring on depth, tractability, support, and P-vs-NP relevance.

Conjectures are persisted at `data/conjectures/*.json`.
