### 代码质量与依赖管理

所有项目必须遵循以下规范。

* **代码风格与 Lint（CI 强制）：**
  * **JavaScript/TypeScript：** 使用 **ESLint**（代码检查）和 **Prettier**（格式化）。建议配置 pre-commit 钩子自动执行。
  * **Python：** 使用 **Ruff**（超快 lint 和格式化），可替代 Black、isort、Flake8 等老工具。
  * **Go：** 标准 `gofmt` 和 `golint`。
  * **Rust：** 使用 **rustfmt**（格式化）和 **clippy**（静态分析、lint）。
* **依赖管理：**
  * **Node.js：** 使用 `npm` 或 `pnpm`。所有项目**必须**提交 `package-lock.json` 或 `pnpm-lock.yaml`，确保可复现构建。
  * **Python：** 使用 **`uv`** 配合 `pyproject.toml`。`uv` 是现代、高速的 `pip` 和 `venv` 替代品，`pyproject.toml` 定义全部依赖，`uv` 基于此创建虚拟环境。
  * **Rust：** 使用 **Cargo** 进行依赖管理。**必须**提交 `Cargo.lock`，确保依赖可复现。建议使用 [cargo-edit](https://github.com/killercup/cargo-edit) 辅助管理依赖。
* **语言生态增强建议：**
  * **Node.js（TypeScript）/前端：**
    * **配置管理：** 使用 **`zod`** 校验运行时环境变量，防止配置错误，确保应用在已知良好状态下启动。
  * **Python：**
    * **配置管理：** 使用 **`pydantic`** 管理设置，提供与 `zod` 类似的优势。
    * **CLI 工具：** Python CLI 推荐用 **`Typer`** 或 **`Click`**，可声明式构建强大命令行工具。
  * **Go：**
    * **配置管理：** 使用 **`viper`** 处理配置文件、环境变量和命令行参数。
    * **CLI 工具：** 使用 **`cobra`** 构建现代 CLI 应用，许多知名工具（如 `kubectl`、`hugo`）都基于它。
  * **Rust：**
    * **配置管理：** 推荐使用 **`config`** crate（[docs](https://docs.rs/config/)）或 **`figment`** crate，支持多种配置源（文件、环境变量等），类型安全。
    * **CLI 工具：** 推荐使用 **`clap`** crate（[docs](https://docs.rs/clap/)），声明式构建强大 CLI 应用，是 Rust 生态事实标准。也可考虑 **`structopt`**（已合并入 clap 3.x）。
    * **依赖安全与升级：** 使用 **`cargo-audit`** 检查依赖安全漏洞，**`cargo-outdated`** 检查依赖更新。
