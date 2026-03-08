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
