# Custom CLI Tools

This file lists custom tools created to assist with development and automation tasks.

## pdfextract
**Location:** `~/.bin/pdfextract`
**Description:** Extracts specific pages or page ranges from a PDF file.
**Usage:** `pdfextract <input_file> <pages> <output_file>`
**Example:** `pdfextract input.pdf 1-5,8,10-12 output.pdf`
**Implementation:** Bash wrapper that runs the versioned repo script `~/.bin/pdfextract-core.py`, with a dedicated virtual environment bootstrapped under `~/.local/share/pdf_extract_tool/venv` on first use.

## describe-image
**Location:** `~/.bin/describe-image`
**Description:** Uses a local Ollama multimodal model to describe images and output Markdown (single image or batch directory).
**Usage:**
- `describe-image <image_file>`
- `describe-image --dir <directory>`
**Example:**
- `describe-image 路线.jpg`
- `describe-image --dir 1.8 --limit 3`
**Notes:**
- Requires `ollama` to be installed and the service running (e.g. `ollama serve`).
- Default model is `qwen3-vl:8b`; if you override `--model`, the exact model name is used, and missing models should be pulled with `ollama pull <model>`.
**Benchmarking:** For more stable speed comparisons across machines, use `--seed 1 --temperature 0 --num-predict 512` to reduce randomness.
**Tip:** Use `--quiet` when benchmarking to avoid printing long model output.
**Implementation:** Single-file Python CLI (stdlib only) that calls Ollama HTTP API and writes `image-description.md` under `--dir` by default.

## shell-startup-smoke-check
**Location:** `~/.bin/shell-startup-smoke-check`
**Description:** Verifies `zsh -ilc`, `zsh -ic`, and `bash -lc` load `SR_BASE_URL`, `set3161`, `awsus`, and `co` under a sanitized environment.
**Usage:** `shell-startup-smoke-check`
**Example:** `shell-startup-smoke-check`
**Implementation:** Bash CLI with a companion fixture test script at `bin/test-shell-startup-smoke-check`.

## codex-doctor
**Location:** `~/.bin/codex-doctor`
**Description:** Checks the local Codex environment, including `~/.codex/config.toml`, key feature flags, custom skills, MCP server command paths, and supporting `AGENTS` files.
**Usage:** `codex-doctor [--verbose]`
**Example:** `codex-doctor --verbose`
**Implementation:** Bash CLI with a companion fixture test script at `bin/test-codex-doctor`.

## codex-tmp
**Location:** `~/.bin/codex-tmp`
**Description:** Manages persistent task workspaces under `~/.codex/tmp` without sacrificing session recovery. Legacy unmanaged, active, kept, recently completed, dirty Git, linked-worktree, changed, missing-dependency, and live-session workspaces are protected. New direct-child directories created after the configured adoption cutoff are automatically marked active.
**Usage:**
- `codex-tmp create <task> [--session-id ID]`
- `codex-tmp create <task> [--budget-class default|large|exceptional] [--expected-peak-gib N]`
- `codex-tmp complete <task> [--depends-on PATH] [--note TEXT]`
- `codex-tmp compact <task> --depends-on PATH [--checkpoint TASK_PATH] --note TEXT`
- `codex-tmp migrate-legacy-compaction <task>` (explicit recovery-package upgrade for an interrupted pre-package compaction)
- `codex-tmp scratch-acquire <task>` / `scratch-check` / `scratch-release` / `scratch-clean`
- `codex-tmp clean-reproducible <task>`
- `codex-tmp release-checkpoint <task>` / `codex-tmp recovery-gc [--dry-run]`
- `codex-tmp active <task>` / `codex-tmp keep <task>`
- `codex-tmp inventory` / `codex-tmp check <task>`
- `codex-tmp status [task]`
- `codex-tmp hold <task> --until ISO-8601 --reason TEXT` / `codex-tmp hold <task> --clear`
- `codex-tmp refresh-fingerprint <task>` (explicit legacy manifest upgrade only)
- `codex-tmp adopt`
- `codex-tmp sweep --dry-run`
- `codex-tmp restore <quarantine-id-or-task-name>`
**Lifecycle:** Hooks are now producer-only: they whitelist and durably queue `session_id`, `cwd`, event name, observation time, and an internal event id, then return immediately. The single five-minute LaunchAgent dispatcher consumes the queue, adopts new direct-child task roots, refreshes leases, and runs maintenance; hooks never start a second sweeper. `lifecycle_mode=shadow` records v2 decisions without changing task content. The current `lifecycle_mode=v2-new` atomically assigns only newly created or adopted tasks to owner `v2`, generation 1; existing tasks remain `legacy` until separately verified and migrated. Switching back to `shadow` freezes v2-owned tasks and restores legacy as the effective decision without rewriting ownership. A `Stop` event refreshes only that session's short lease, while `SessionEnd` expires only that session's lease; cleanup waits for every session lease. The next dispatcher can remove verified Cargo `target` and locally installed `node_modules` output. A symlink-only `node_modules` link farm remains protected. An expired task with unique or undelivered content becomes visibly `blocked`; it is not silently deleted.

New tasks record an advisory expected peak of 2 GiB by default, 8 GiB for large tasks, and 16 GiB for exceptional tasks. Any positive override is accepted even above the class planning level and returns a warning instead of refusing the task. Capacity pressure, reservations, corrupt caches, unrelated manifests, and deferred reconciliation are warnings only; only invalid arguments, naming/locking conflicts, or real filesystem failures may reject creation. `status` exposes the simplified `in-use`, `settling`, `recoverable`, and `blocked` states. `hold` is a reasoned, expiring exception capped at 30 days and does not protect reproducible output bytes.

A completed, externally recoverable large task can be explicitly queued with `compact`. Before deletion, `checkpoint/`, `evidence/`, standard task ledgers, and explicit `--checkpoint` paths are copied through `O_NOFOLLOW` file descriptors into a SHA-256-addressed package under `~/.local/share/codex-tmp/checkpoints`; source inode/content snapshots and the final package hash are revalidated. References are keyed by an immutable task-instance ID, so quarantining and recreating the same task name cannot release another generation's package. Object publication uses a recoverable `publishing → manifest → active` transaction. Reconciliation scans both object storage and task manifests: published orphans are released, manifest-backed interrupted publishes activate, missing objects are marked, task-purge release crashes are completed, and interrupted GC deletes finish on the next invocation. After the one-hour compaction grace, maintenance removes the task body and leaves a small `RECOVERY.md` stub. Recovery references are released when the compacted task is finally purged or by explicit `release-checkpoint`; zero-reference packages wait seven more days before bounded GC. Store quota exhaustion and package drift fail closed. `migrate-legacy-compaction` is the narrow, explicit upgrade path for a pre-package compaction already interrupted in its deleting phase.

Fenced scratch writers use the exact relative generation path returned by `scratch-acquire` and must validate their token before writing. Absolute paths, traversal, mismatched generations, symlink ancestors, and identity changes fail closed. A generation is cleaned only after all tokens are released; old tokens are invalid after cleanup. Background maintenance never deletes unfenced active data. For completed tasks it may immediately remove reproducible Cargo `target` directories and locally installed `node_modules` trees because those trees are excluded from the recovery fingerprint. A `node_modules` link farm containing only symlinks to shared runtime packages is retained: removing it reclaims no package data and breaks resumable tool resolution. Compaction and purge require live recovery dependencies, clean/live-remote Git state, filesystem containment, and no process/open-file references. Git inspection sets `GIT_OPTIONAL_LOCKS=0` and finishes before the deletion snapshot; process/FD and identity checks remain at the final deletion gate. Quarantine binds the verified source by parent directory fd, inode/device, and immutable task-instance ID. Final purge holds a hook drain/ingress fence, so an already queued recovery heartbeat wins and restores the task; only a deletion that commits first can precede a later heartbeat. Missing safety tooling fails closed. Ordinary completed work still waits 72 hours and for all owner-session heartbeats to age past 7 days before quarantine. After 14 restorable days, a first pass marks an entry `purge_pending`; physical deletion requires another sweep after a further 24-hour pending window.

**State:** Runtime metadata, capacity cache, recovery references, observations, ownership records, and logs live under private `~/.local/state/codex-tmp`. Every managed task has an immutable instance id plus an external owner/generation record bound to its device and inode. Physical cleanup revalidates that record under the stable task and ownership locks; missing, conflicting, or stale generations fail closed for that task without becoming a global admission gate. Legacy manifests missing these fields are backfilled under the task lock without changing their business status or fingerprint. Shadow observations cover every direct-child directory, including unmanaged and corrupt entries, and record legacy, v2, effective, aggressiveness, and explanation fields. Policy is configured in `~/.codex/tmp-lifecycle.json`; tmp target, pressure, and emergency levels are 10, 15, and 20 GiB. Capacity refresh uses a bounded native `du`; timeout or failure keeps the prior measurement with an explicit stale marker instead of blocking the dispatcher. `auto_adopt_after` still protects older unmanaged directories from bulk adoption, while new direct children are associated automatically. A queued session event pointing at quarantined content is consumed by the dispatcher and restores it before purge can win the final ingress fence. `sweep --dry-run` remains read-only.
**Implementation:** Standard-library Python CLI with regression tests in `tests/test_codex_tmp.py`.

## tm-exclude-dev-artifacts
**Location:** `~/.bin/tm-exclude-dev-artifacts`
**Description:** Finds reproducible package-manager installations and caches, Xcode/MacTeX trees, `node_modules`, conventionally named Python virtual environments, and Rust `target` directories, then manages fixed-path Time Machine exclusions. Rebuild instructions and manifests are in `docs/environment-rebuild.md` and `docs/rebuild/`.
**Usage:** `tm-exclude-dev-artifacts [--dry-run|--apply|--remove] [--root PATH ...]`
**Example:** `tm-exclude-dev-artifacts --apply`
**Notes:** Dry-run is the default. Use `--remove` to roll back matching exclusions. The default scan roots are `~/git` and `~/git-sansi`.
**Implementation:** Bash CLI with a companion fixture test script at `bin/test-tm-exclude-dev-artifacts`.
