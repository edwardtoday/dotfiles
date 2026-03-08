# Shell Startup Smoke Check Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a repeatable smoke check command that validates `zsh -ilc`, `zsh -ic`, and `bash -lc` load the expected alias, functions, and environment variables.

**Architecture:** Add one user-facing CLI in `bin/` that runs the three shell startup modes under a sanitized environment and reports pass/fail per shell. Add one companion test script in `bin/` that creates temporary fixture homes so the smoke check can be validated without depending on the current machine state.

**Tech Stack:** Bash, zsh, POSIX shell startup files

---

### Task 1: Add the failing smoke test

**Files:**
- Create: `bin/test-shell-startup-smoke-check`
- Test: `bin/shell-startup-smoke-check`

**Step 1: Write the failing test**

- Create a bash test script that builds temporary fixture homes for `zsh` and `bash` startup files.
- Make the success fixture expose `SR_BASE_URL`, `set3161`, `awsus`, and `co`.
- Make the failure fixture omit one expected symbol so the target script must fail.

**Step 2: Run test to verify it fails**

Run: `./bin/test-shell-startup-smoke-check`
Expected: FAIL because `bin/shell-startup-smoke-check` does not exist yet.

### Task 2: Implement the smoke check command

**Files:**
- Create: `bin/shell-startup-smoke-check`
- Test: `bin/test-shell-startup-smoke-check`

**Step 1: Write minimal implementation**

- Run `zsh -ilc`, `zsh -ic`, and `bash -lc` under `env -i`.
- Check fixed expectations: `SR_BASE_URL=https://112.2.46.78:18443`, function `set3161`, function `awsus`, alias `co`.
- Print one summary line per shell and return non-zero if any shell fails.

**Step 2: Run test to verify it passes**

Run: `./bin/test-shell-startup-smoke-check`
Expected: PASS for the success fixture and FAIL for the intentional broken fixture.

### Task 3: Document the tool

**Files:**
- Modify: `README.md`
- Modify: `bin/TOOLS.md`

**Step 1: Update docs**

- Add a short usage example to `README.md`.
- Register the command in `bin/TOOLS.md` with purpose and usage.

**Step 2: Run targeted verification**

Run: `./bin/shell-startup-smoke-check`
Expected: PASS for all three shell startup modes on this machine.
