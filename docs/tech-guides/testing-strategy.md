### 测试金字塔：信心保障的测试策略

必须采用结构化的测试策略，涵盖主流语言生态（JS/TS、Python、Go、Rust）。

* **第1层：单元测试（数量最多）**
  * **目标：** 独立测试单个函数/组件。
  * **工具：**
    * **JavaScript/TypeScript：** **Jest**
    * **Python：** **Pytest**
    * **Go：** Go 内置测试框架（`testing` 包，`go test` 命令），推荐配合 [testify](https://github.com/stretchr/testify) 提升断言和 mock 能力。
    * **Rust：** **cargo test**（Rust 内置测试框架，支持单元与集成测试，推荐配合 [proptest](https://docs.rs/proptest/) 进行属性测试）
* **第2层：集成测试**
  * **目标：** 测试服务之间的交互（如 API 与数据库）。
  * **环境：** 在 CI（Cloud Build）流水线中，针对 `docker-compose.yml` 定义的有状态服务运行这些测试。
  * **Go 实践：** 在 `*_test.go` 文件中编写集成测试，可结合 [testcontainers-go](https://github.com/testcontainers/testcontainers-go) 启动依赖服务（如数据库）进行端到端集成测试。
  * **Rust 实践：** 在 `tests/` 目录下编写集成测试，利用 `cargo test` 自动发现并运行。可用 [testcontainers](https://docs.rs/testcontainers/) crate 启动依赖服务（如数据库）进行端到端集成测试。
* **第3层：端到端（E2E）测试（数量最少）**
  * **目标：** 在真实浏览器中模拟完整用户流程。
  * **工具：** **Playwright** 或 **Cypress**（适用于前端）；后端 API 可用 [restest](https://docs.rs/restest/)（Rust）、[godog](https://github.com/cucumber/godog)（Go 的 BDD/E2E 测试框架）等工具进行黑盒 E2E 测试。
