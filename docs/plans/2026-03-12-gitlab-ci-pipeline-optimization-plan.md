# GitLab CI Pipeline Optimization 实施计划

## 目标

- 在 `codex/skills/` 下新增 `gitlab-ci-pipeline-optimization`
- 让 skill 可以指导端到端完成 GitLab 慢 pipeline 的分析、优化、MR 推进与回读验证

## 实施步骤

1. 用 `init_skill.py` 初始化 skill 目录与 `agents/openai.yaml`
2. 编写 `SKILL.md` frontmatter，明确触发条件和边界
3. 在 `SKILL.md` 中写出固定工作流、输出要求、验证门槛和停止条件
4. 编写 `references/optimization-playbook.md`，收纳常见瓶颈类型与低风险优化动作
5. 校验 YAML/frontmatter/agents 元数据格式
6. 回看 skill 内容，确认没有写死 Android 等项目特例
7. 汇总生成结果、验证方式和后续维护建议

## 验证

- `ruby -e 'require "yaml"; YAML.load_file(..., aliases: true)'` 校验相关 YAML
- 读取 `SKILL.md` frontmatter，确认 `name` 与 `description` 合法
- 检查 `agents/openai.yaml` 字段是否符合引用文档约束
