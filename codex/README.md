# Codex configuration ownership

`~/.codex/config.toml` is mutable runtime state. CC Switch and Codex may update providers, models, endpoints, profiles, and related settings. Dotfiles must not replace the file wholesale.

- `config.common.toml` is a reference snapshot of portable settings, not an auto-installed replacement.
- `projects.local.toml` is per-host project trust/path state and must not be synced between Macs.
- `update-project-index.py` replaces only `[projects.*]` blocks and preserves all other bytes, including CC Switch changes.
- OAuth files, API keys, and generated runtime sections remain local.
- Both `lab` and `custom` use `SUB2API_API_KEY` for Lab inference. Keep `env_key = "SUB2API_API_KEY"` on both providers: existing threads may retain `lab` even when the runtime default is `custom`. ChatGPT sign-in is separate from the Lab API key.
