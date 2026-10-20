# WenKB

WenKB 是一套面向个人与小团队的本地知识库系统，支持模型配置、知识库管理、文档与网页导入、索引构建、问答、搜索和文档集管理。

## 快速开始

### 后端

从仓库根目录执行：

```powershell
cd wenkb-server
$env:WENKB_JWT_SECRET = "<与认证服务一致的至少32字节密钥>"
python app.py
```

后端默认监听 `http://127.0.0.1:16088`，健康检查接口为 `GET /health`。
受保护 API 只接受由共享密钥签发的 HS256 JWT。当前仓库后端尚未实现前端调用的登录/注册接口，实际使用前需接入认证服务；不要将示例占位文本用作真实密钥。

### 前端

打开新的终端窗口，从仓库根目录执行：

```powershell
cd wenkb-client
npm install
npm run dev
```

前端开发服务默认运行在 `http://127.0.0.1:11420`，并代理后端 `16088` 端口。

### 验证

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
```

## 主要能力

- 模型供应商配置与默认模型选择
- 知识库创建、编辑、删除与可见性控制
- 文档、网页链接和文档集导入
- 数据集索引、摘要、Q&A 和三元组增强
- 知识库问答、引用展示和搜索
- 本地运行、维护交接和部署运维

## 文档入口

- [需求分析](docs/requirements_analysis.md)
- [概要设计](docs/architecture_design.md)
- [详细设计](docs/detailed_design.md)
- [数据库设计](docs/database_design.md)
- [接口设计](docs/api_design.md)
- [开发者与用户手册](docs/wenkb_operation_guide.md)
- [部署运维](docs/deployment_guide.md)
- [测试计划](docs/test_plan.md)
- [测试成绩书手动运行与截图指南](docs/test_scorebook_manual_run.md)
- [变更管理](docs/change_management.md)
- [代码维护交接](docs/code_maintenance_handoff.md)

## 目录说明

| 目录 | 说明 |
|---|---|
| `wenkb-server` | 后端服务、数据库迁移、模型资源和本地存储 |
| `wenkb-client` | 前端页面和桌面端工程 |
| `docs` | 需求、设计、测试、运维和维护文档 |
| `outputs` | 需求跟踪矩阵和概要设计相关交付物 |
| `tests` | 文档测试和维护测试 |

## 数据与运行约定

- 默认数据库文件：`wenkb-server/resources/database/wenkb.db`
- 默认上传目录：`wenkb-server/resources/static/upload`
- 默认文档目录：`wenkb-server/resources/documents`
- 默认向量库目录：`wenkb-server/resources/vector_store`
- 后端启动时会执行数据库版本检查与初始化
- 首次运行会自动创建所需目录和数据库文件
- 当前以本地单机部署为主，适合本机运行和小范围验证

## 常见问题

- 如果问答没有结果，先确认默认 LLM 已配置，且知识库中已有 `ready` 状态的数据集。
- 如果资料导入后无法检索，先确认索引是否完成，或者数据集是否已启用。
- 如果本地启动失败，先检查端口占用、目录权限和数据库文件可写性。
