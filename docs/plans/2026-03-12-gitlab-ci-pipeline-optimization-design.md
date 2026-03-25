# GitLab CI Pipeline Optimization 设计

## 目标

- 新建一个可复用的 Codex skill，用于端到端执行 GitLab 慢 pipeline 优化
- 覆盖从“筛选最慢 pipeline”到“提交真实 CI 优化并发起 Draft MR”的完整流程
- 用通用约束表达替代项目特例，避免 skill 被单一仓库经验绑死

## 触发条件

- 用户要在 GitLab 中定位慢 pipeline、解释瓶颈、提出或直接落优化
- 用户希望通过 MR 和新 pipeline 直接验证优化是否生效
- 用户明确要求按项目去重、批量推进多个仓库或自动指派 owner

## 设计原则

- 只收录高复用、跨项目稳定的流程与判断标准
- 优先写“如何做”和“何时触发”，不写项目私有细节
- 将容易变化或只适合做案例的内容放到 `references/`
- 强调“先分析关键路径，再落低风险改动，再用 MR pipeline 验证”

## 核心工作流

1. 选定时间窗口，找出最慢 pipeline，并按项目去重
2. 拉取 pipeline、job、trace，识别关键路径与瓶颈类别
3. 仅优先选择低风险、可在 MR pipeline 里直接观察差异的改动
4. 优先复用本地现有仓库，不默认重新 clone
5. 同步提交真实 CI 配置与说明文档，而不是只发提案
6. 创建 Draft MR，写清已落地改动、预期收益、验证方式
7. 指派最近 30 天 commit 最多的人，并回读新 pipeline 结果
8. 若新 pipeline 暴露配置兼容性问题，继续修到能跑或明确标记阻塞

## 通用约束

- 以实际慢 pipeline 所在的 `project/ref/target branch` 为准，不默认跟随默认分支
- 如果分析对象跑在非默认分支，先校正本地分支基线和 MR target branch，再做优化
- 不把项目私有环境假设写死进 skill，环境问题抽象成依赖/SDK/凭证/镜像能力等通用类别
- 每次修改后都要做项目原生验证，例如 GitLab CI lint、脚本语法检查、最小构建验证
- MR 描述必须区分“已落地改动”“预期收益”“后续可选项”

## 资源设计

- `SKILL.md`：端到端流程、判断标准、输出要求
- `references/optimization-playbook.md`：常见慢点类型、低风险优化动作、MR 更新清单
- `agents/openai.yaml`：提供可读的展示名、简介和默认调用提示
