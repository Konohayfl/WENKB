# WenKB

WenKB 是一套面向个人与小团队的本地知识库系统，支持模型配置、知识库管理、文档与网页导入、索引构建、问答、搜索和文档集管理。

## 快速开始

### 后端

从仓库根目录执行：

```powershell
cd wenkb-server
$env:WENKB_JWT_SECRET = "<至少32字节的随机密钥>"
python app.py
```

后端默认监听 `http://127.0.0.1:16088`，健康检查接口为 `GET /health`。
系统支持数据库持久化的多用户注册与登录；密码以 PBKDF2 哈希存储。受保护 API 只接受由 `WENKB_JWT_SECRET` 签发的 HS256 JWT，该密钥至少 32 字节。数据库 schema 版本 6 新增用户表，旧数据库会在后端启动时自动升级。不要将含真实账号的运行数据库或密钥提交到版本库。

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

- 完整文档清单与分类见 [AGENTS.md](AGENTS.md)。
- 开发者与用户操作见 [操作手册](docs/wenkb_operation_guide.md)。
- 部署、备份与恢复见 [部署运维指南](docs/deployment_guide.md)。
- 测试基线见 [测试计划](docs/test_plan.md)。

## 目录说明

| 目录 | 说明 |
|---|---|
| `wenkb-server` | 后端服务、数据库迁移、模型资源和本地存储 |
| `wenkb-client` | 前端页面和桌面端工程 |
| `docs` | 需求、设计、测试、运维和维护文档 |
| `outputs` | 需求跟踪矩阵和概要设计相关交付物 |
| `tests` | 文档测试和维护测试 |

## 常见问题

- 如果问答没有结果，先确认默认 LLM 已配置，且知识库中已有 `ready` 状态的数据集。
- 如果资料导入后无法检索，先确认索引是否完成，或者数据集是否已启用。
- 如果本地启动失败，先检查端口占用、目录权限和数据库文件可写性。
