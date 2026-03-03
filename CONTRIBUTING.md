# CONTRIBUTING.md

## Who Should Contribute

Anyone who:
- Knows complexity theory and wants to build something
- Wants to learn complexity theory by building something
- Is a strong engineer who trusts the math people and wants to make the engine scream

## The One Rule

**Every contribution must make mathematical progress possible.** If a PR doesn't enable the agents to get closer to a verified complexity result, it doesn't belong here — yet.

Infrastructure is fine. But infrastructure exists to serve the mission.

## PR Process

1. Branch from `main`: `git checkout -b agent/lower_bound_hunter/gate_elimination`
2. Write tests first
3. All Lean files must type-check before PR
4. PR description must answer: *"How does this advance the mission?"*
5. One approval required from a maintainer

## Setting Up
```bash
git clone https://github.com/GISMO-1/pvsnp-hunter
cd pvsnp-hunter
pip install -r requirements.txt
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
cd lean && lake update && lake build
python -m pytest tests/
```

## Code Style

- Black + isort for Python
- Rust fmt for Rust
- `lean4` formatting for Lean files
- Mypy strict mode — no untyped functions

## Questions

Open an issue. Tag it `question`. We answer.
