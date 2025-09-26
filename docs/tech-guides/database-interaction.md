### 后端数据访问（ORM）

* **问题：** 直接写 SQL 易出错、难维护且无类型安全。
* **解决方案：** ORM（对象关系映射）将数据库表映射为代码中的模型或 schema，提升开发效率与安全性。
* **推荐：**
  * **Node.js（TypeScript）：** **Prisma** 是现代无可争议的首选，类型安全极佳，schema 优先，查询构建器优秀。
  * **Python：** **SQLAlchemy** 是久经考验、功能强大且生态丰富的标准。与 FastAPI 搭配可构建健壮数据层。
  * **Go：** 推荐使用 **GORM**（[官网](https://gorm.io/)），是 Go 生态最流行的 ORM，API 友好、功能丰富，支持主流数据库。对于更强类型安全和编译期校验，可考虑 **ent**（[entgo.io](https://entgo.io/)），适合大型项目。
  * **Rust：** 推荐使用 **Diesel**（[官网](https://diesel.rs/)），类型安全、编译期校验强，适合对安全性和性能有高要求的项目。对于更灵活的异步场景，可考虑 **SeaORM**（[官网](https://www.sea-ql.org/SeaORM/)），支持 async/await，API 现代。
* **决策：** Node.js/TypeScript 用 Prisma，Python/FastAPI 用 SQLAlchemy，Go 用 GORM（或 ent），Rust 用 Diesel（或 SeaORM，视异步需求）。
