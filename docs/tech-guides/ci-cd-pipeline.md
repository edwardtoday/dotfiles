### CI/CD：自动化构建与部署（GitLab CI 方案）

采用 GitOps 工作流，通过 **GitLab CI/CD** 自动化实现从代码到生产的全流程。

1. **源码：** 代码托管在 **GitLab 仓库**，每次推送或合并请求会自动触发 CI/CD 流水线。
2. **构建（`.gitlab-ci.yml`）：** 在仓库根目录创建 `.gitlab-ci.yml`，定义流水线各阶段。常见流程如下：
    * 安装依赖（如 `npm install`、`pip install`）
    * 运行所有测试
    * 构建前后端 Docker 镜像
    * 推送版本化镜像到 **GitLab Container Registry** 或其他镜像仓库（如 AWS/GCP/阿里云等）
3. **部署：** 可以在 `.gitlab-ci.yml` 中定义多环境部署阶段（如 `dev`、`staging`、`prod`），并通过环境变量、安全凭据自动部署到目标环境（如 Kubernetes、ECS、Cloud Run 等）。
    * **交付流水线：** 支持多阶段部署与审批（如 `dev` -> `staging` -> `prod`），可配置手动/自动发布与回滚。
    * **目标环境：** 每个环境可对应不同的云服务或集群。
    * **优势：** 实现安全、可审计、一键发布与回滚，支持丰富的权限与审批机制。

> 参考 [GitLab CI/CD 官方文档](https://docs.gitlab.com/ee/ci/) 获取 `.gitlab-ci.yml` 配置示例和最佳实践。
