### AWS 全栈开发与部署架构（含中国区与全球区差异）

本节梳理了应用从本地开发到生产部署、运维的完整生命周期，适配 AWS 全球区与中国区（由光环新网/西云数据运营）的实际差异。

#### 其他关键云服务：基础保障

这些服务是生产级应用的必备项，均有全球区与中国区版本，API 基本一致，但部分服务在中国区上线略有延迟，需关注[官方文档](https://www.amazonaws.cn/en/new/)。

* **Secrets Manager（密钥管理）：** 存储所有敏感信息（数据库密码、第三方 API 密钥等）。ECS/EKS/Lambda 等服务运行时可安全访问。
* **IAM（身份与访问管理）：** 强制执行**最小权限原则**。服务和开发者只应拥有所需权限。中国区与全球区 IAM 策略语法一致，但账号体系隔离。
* **CloudWatch（日志与监控）：** 所有服务可自动输出日志到 CloudWatch。可配置仪表盘和告警，监控健康与性能。
* **VPC & PrivateLink/Endpoint：** **关键**，用于让服务通过私网安全、低延迟地访问 RDS/ElastiCache/S3 等资源。中国区 VPC 功能与全球区一致。
* **WAF（Web 应用防火墙）：** 保护前端免受常见 Web 攻击和 DDoS。中国区支持 AWS WAF，部分高级功能上线略有延迟。

#### 语言专用 AWS SDK

应用代码**必须**使用官方 AWS SDK 访问云服务。这些 SDK 负责认证（IAM 角色/STS）、重试、并提供惯用接口。中国区与全球区 SDK 用法一致，仅 endpoint 区分（如 `amazonaws.com.cn`）。

* **Node.js（TypeScript）：** 使用 `@aws-sdk/client-[SERVICE]`（如 `@aws-sdk/client-s3`、`@aws-sdk/client-sqs`）。
* **Python：** 使用 `boto3`（如 `boto3.client('s3')`、`boto3.client('sns')`）。
* **Go：** 使用 `github.com/aws/aws-sdk-go-v2/service/[service]`。

#### 通用要求：AWS CLI

每位开发者**必须**安装并配置 **AWS CLI**，并完成凭证认证（支持 profile 区分中国区与全球区）。这是所有手动和脚本化云操作的基础工具。

* **全球区 endpoint：** `amazonaws.com`
* **中国区 endpoint：** `amazonaws.com.cn`
* **配置 profile 示例：**

  ```sh
  aws configure --profile aws-cn
  aws configure --profile aws-global
  ```
