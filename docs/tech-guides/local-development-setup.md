### 本地开发：高效热重载开发环境

目标是实现"内循环"无缝体验，代码变更可即时反映。

* **前端（Vite）：** 你当前的 Vite 配置已通过 `npm run dev` 提供业界最佳的 React 热重载体验，无需更改。
* **后端（Node.js/Python）：**
  * **Node.js：** 使用 `nodemon` 监听文件变更并自动重启服务。
  * **Python（FastAPI）：** 开发服务器自带热重载，使用 `uvicorn main:app --reload` 启动。
* **统一本地环境（推荐）：**
  * **工具：** 使用 `concurrently` 等工具，一条命令同时启动前后端开发服务器。
  * **容器化（`docker-compose`）：** **最佳实践**。编写 `docker-compose.yml`，定义并运行完整本地栈：前端容器、后端容器、本地 Postgres 数据库容器。
    * **优势：** 一条命令（`docker-compose up`）启动全部服务。每位开发者环境完全一致，彻底消除"只在我电脑上能跑"的问题。
