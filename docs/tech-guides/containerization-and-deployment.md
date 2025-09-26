### 部署：ECS Fargate/EKS/Lambda 实现无服务器与弹性扩缩

AWS 提供多种无服务器与弹性容器化部署方案，全球区与中国区均支持 ECS Fargate、EKS（Kubernetes）、Lambda（部分服务中国区上线略有延迟）。

* **策略：** 前后端分别部署为独立服务。
  * **前端服务：** 用 `Dockerfile` 构建 React 应用，并用轻量级 Web 服务器（如 **Nginx**）托管静态文件，部署到 ECS Fargate/EKS，或用 S3 + CloudFront 托管静态站点（推荐）。
  * **后端服务：** 用 `Dockerfile` 打包 Node.js 或 Python 应用，部署到 ECS Fargate/EKS，或用 Lambda（适合 API）。
* **通信：** 前端服务配置后端服务的公网或私网 URL 以发起 API 调用。建议用 API Gateway 统一入口。
* **安全：**
  * 前端服务可公开访问（S3+CloudFront 或 ECS/EKS 负载均衡）。
  * 后端服务应仅允许前端服务和已认证用户访问（可用 VPC、Security Group、API Gateway 授权等）。

### "本地到云端"升级路径：分步实践指南

这是从 `docker-compose` 本地开发到 AWS 生产部署的实用流程，适配全球区与中国区。

**基础：** 你有一个 `docker-compose.yml`，可启动前端、后端和本地 Postgres 数据库。

**步骤1：编写生产级 `Dockerfile`**
`docker-compose` 用的 `Dockerfile` 需升级为生产可用。需采用多阶段构建，生成小巧安全的最终镜像。前端需先构建静态资源，再拷贝到极简 Nginx 镜像中。

**步骤2：配置与密钥外部化**
这是最关键的转变。

* **本地：** 用 `.env` 和 `docker-compose` 注入环境变量（如 `DATABASE_URL=postgres://user:pass@localhost:5432/mydb`）。
* **云端：**
    1. 所有密钥（数据库密码、API 密钥）存储在 **AWS Secrets Manager**。
    2. 在 ECS/EKS/Lambda 服务定义中，将这些密钥挂载为环境变量或通过 SDK 动态读取。
    3. 应用代码**无需更改**，依然读取 `process.env.DATABASE_URL`，只是值由 AWS Secrets Manager 提供，而非 `docker-compose`。

**步骤3：用 IaC 预置云基础设施**
不要在 AWS 控制台手动创建数据库或服务。应使用**基础设施即代码（IaC）**。

* **工具：** **Terraform** 或 **AWS CloudFormation**（中国区与全球区均支持）。
* **流程：**
    1. 编写 Terraform/CloudFormation 文件，定义所有 AWS 资源：RDS Postgres、VPC 网络、Security Group、IAM 角色、ECS/EKS/Lambda 服务等。
    2. 执行 `terraform apply` 或 `aws cloudformation deploy`，以可复现、可版本化的方式创建/更新所有云资源。

**步骤4：连接数据库**

* **本地：** 后端连接 `localhost:5432`。
* **云端：** 后端服务通过 VPC 内网安全连接 RDS Postgres 的**私有 IP**。私有 IP 可由 Terraform/CloudFormation 输出，并安全地作为环境变量提供给服务。

**注意：** 中国区与全球区资源完全隔离，需分别部署与管理。部分服务（如 CloudFront、Lambda@Edge）在中国区上线略有延迟，需关注[中国区服务列表](https://www.amazonaws.cn/en/about-aws/regional-product-services/)。
