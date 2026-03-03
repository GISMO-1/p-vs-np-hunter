# conjecture_engine

Fully local conjecture synthesis and validation for complexity theory. No external APIs, no API keys.

## Components

- **ConjectureTemplateEngine**: structural conjecture synthesis over circuit classes, hard functions, and lower-bound techniques.
- **ConjectureMiner**: mines `data/lower_bounds/`, `data/circuit_families/`, and `data/hard_instances/` for gaps, finite-n generalizations, and anomalies.
- **Optional Ollama support**: uses local models (`deepseek-r1`, `llama3`, `mistral`) if available; silently falls back when unavailable.
- **Small-case tester**: runs finite checks (`n=2..5`) and integrates lower-bound evidence from `lower_bound_hunter`.
- **Ranking engine**: deterministic scoring on depth, tractability, support, and P-vs-NP relevance.

Conjectures are persisted at `data/conjectures/*.json`.
