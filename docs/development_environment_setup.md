# WenKB 开发环境搭建与运行指南

版本：v1.0<br>
日期：2026-10-24<br>
适用对象：首次搭建本地开发环境的开发者、课程演示和项目交接人员

## 1. 目的与运行结构

本文说明如何在 Windows 本地准备 WenKB 开发环境、启动前后端、检查数据库初始化，并安全地处理登录账号和模型凭据。

WenKB 本地开发时由两个进程组成：Python/FastAPI 后端默认监听 `127.0.0.1:16088`，Vue/Vite 前端默认监听 `127.0.0.1:11420`。Vite 将 `/api`、`/static` 和 `/ws` 请求转发至后端。业务关系数据默认存储在 SQLite 文件 `wenkb-server/resources/database/wenkb.db`；上传文件、文档和向量索引保存在 `wenkb-server/resources` 下。

## 2. 需要准备的软件

| 软件 | 用途 | 版本或说明 |
|---|---|---|
| Git | 获取项目代码 | 使用当前受支持版本 |
| Python | 运行后端 | 项目服务端 README 指定 Python 3.11.5；建议使用 Python 3.11 系列 |
| Node.js 和 npm | 安装并运行前端 | 使用 Node.js LTS，并记录 `node --version`、`npm --version` 输出 |
| 浏览器 | 访问开发页面 | 使用近期版本的 Chrome、Edge 或 Firefox |
| Ollama（可选） | 在本机运行 Ollama 聊天模型 | 仅当选择 Ollama 作为聊天模型供应商时需要；也可配置可访问的远端供应商 |

默认数据库为 SQLite，无需单独安装或启动 MySQL、PostgreSQL 等数据库服务。项目包含本地 `m3e-small` embedding 模型资源；聊天模型需由用户在应用设置中配置，除非使用已准备好的本地 Ollama 服务。

## 3. 获取代码并安装依赖

在 PowerShell 中进入仓库目录。以下假设仓库已克隆到当前目录；若尚未获取代码，请先使用 Git 克隆项目并进入仓库根目录。

先检查软件版本：

```powershell
git --version
py -3.11 --version
node --version
npm --version
```

创建后端虚拟环境并安装依赖：

```powershell
cd wenkb-server
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

如果 PowerShell 阻止激活脚本，可不激活虚拟环境，直接使用虚拟环境解释器运行安装命令：

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

依赖清单包含 PyTorch、模型处理组件和 `flash-attention`。Windows 上安装这些依赖可能受 Python、硬件和预编译 wheel 可用性影响；若安装失败，应先记录实际错误和适用的解决方式，不要跳过失败依赖后就认为环境已可用。

另开一个 PowerShell 窗口，回到仓库根目录安装前端依赖：

```powershell
cd wenkb-client
npm ci
```

`npm ci` 按 `package-lock.json` 安装依赖。若没有锁文件或需要有意更新依赖，才使用 `npm install`；不要在普通搭建过程中随意更新锁文件。

## 4. 数据库初始化与脚本

默认数据库是 SQLite，文件位置为 `wenkb-server/resources/database/wenkb.db`。项目随仓库提供 SQLite 基线文件。后端启动时会检查 schema 版本，并自动执行所需的 DDL/DML 升级脚本：

- 全新数据库基线脚本：`wenkb-server/server/db/upgrade/ddl/0.sql` 和 `dml/0.sql`。
- 后续版本升级脚本：对应目录中版本号高于当前数据库版本的 SQL 文件。
- 当前目标 schema 版本由 `wenkb-server/config/common.py` 中的 `DB_SCHEMA_VERSION` 指定。

正常本地启动不需要手动运行这些 SQL。不要把运行中的数据库文件覆盖为旧版本，也不要在升级失败后继续写入业务数据。若要手工验证迁移，应先备份数据库并使用副本；备份与恢复流程见[部署运维指南](deployment_guide.md)。

项目数据库基线不应包含演示者的真实账号或模型 API Key。提交数据库变更前，先检查并清理账号、密码哈希、模型凭据和其他个人数据。

## 5. 启动服务

### 5.1 启动后端

在一个 PowerShell 窗口中：

```powershell
cd wenkb-server
.\.venv\Scripts\python.exe app.py
```

后端启动后会运行数据库版本检查，并启动索引和增强任务队列。首次启动且未配置 `WENKB_JWT_SECRET` 时，会自动生成随机密钥并保存到 `wenkb-server/resources/jwt_secret.key`，后续启动会复用该文件。密钥文件已被 Git 忽略，不要提交、复制到公开材料或随意删除；更换密钥会使现有登录凭证失效。需要外部管理密钥时，可设置至少 32 字节的 `WENKB_JWT_SECRET`，但不要把实际值写入仓库文档。

健康检查地址：`http://127.0.0.1:16088/health`。确认返回健康状态后，再启动前端。

### 5.2 启动前端

在另一个 PowerShell 窗口中：

```powershell
cd wenkb-client
npm run dev
```

浏览器访问 `http://127.0.0.1:11420`。前端代理配置位于 `wenkb-client/vite.config.js`；若改动前后端端口，应同步检查代理配置。

## 6. 登录、密码和模型凭据

### 6.1 登录账号

项目没有预置登录账号或默认密码。首次运行时在登录页选择注册，使用自己的测试账号创建账户，再登录。注册密码长度要求为 8 至 128 个字符；服务端以 PBKDF2 哈希保存密码，不以明文保存。

开发环境文档和公开视频应只写“首次在登录页注册”，不要写个人密码或声称存在默认账号。录制时可使用专门的虚构演示账号，避免展示个人账户信息。

### 6.2 JWT 签名密钥

`WENKB_JWT_SECRET` 是服务端签发登录 token 使用的签名密钥，不是用户登录密码。默认情况下，服务会自动生成并复用 Git 忽略的本地文件 `wenkb-server/resources/jwt_secret.key`，开发者一般无需手工生成或提供该密钥。该密钥不得提交到 Git，也不应出现在截图、视频或公开文档中。

### 6.3 大模型 API Key

聊天和知识增强需要可用的聊天模型。登录 WenKB 后进入设置页，在模型供应商配置中填写 API Key、服务地址和模型信息，并选择默认聊天模型。API Key 属于敏感凭据：只在本地界面或本机安全配置中录入，不要写入 Markdown、源代码、Git、公开演示视频或截图。若演示需要展示配置步骤，应遮挡真实值并使用不可用的占位文本。

## 7. 首次运行验收

按以下顺序完成基础验收：

1. `http://127.0.0.1:16088/health` 返回健康状态。
2. `http://127.0.0.1:11420` 能正常打开登录页。
3. 能注册演示账号并登录。
4. 能打开模型设置页；若需验证聊天，则在本地配置可用的模型凭据。
5. 能打开知识库页面并创建或查看知识库。
6. 若要演示完整问答闭环，导入一个小型可解析文档，启用数据集并等待索引状态为 `ready`，然后提问并检查引用来源。

## 8. 常见问题

| 现象 | 检查方向 |
|---|---|
| 后端启动时报模块缺失 | 确认当前位于 `wenkb-server`，并使用该目录 `.venv` 中的 Python 安装 `requirements.txt` |
| `flash-attention` 或 PyTorch 安装失败 | 检查 Python 版本、Windows wheel 支持与依赖安装日志；按真实环境记录解决步骤 |
| 16088 或 11420 端口已占用 | 关闭占用该端口的进程，或在改端口后同步修改前端代理配置 |
| `/health` 无法访问 | 检查后端是否正常启动、端口是否正确、数据库目录是否可读写 |
| 登录 token 无效或反复回到登录页 | 检查 JWT 密钥文件是否可读写，以及不同后端实例是否使用同一个密钥；密钥变更后重新登录 |
| 登录成功但问答失败 | 检查默认聊天模型、供应商参数、API Key 和网络访问 |
| 导入资料后搜索不到 | 确认数据集已启用，且索引状态为 `ready` |

## 9. 开发验证命令

从仓库根目录运行项目测试：

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
```

若修改后端代码，再执行编译检查：

```powershell
.venv\Scripts\python.exe -m compileall -q wenkb-server/server wenkb-server/app.py
```

前端测试和构建：

```powershell
cd wenkb-client
npm test
npm run build
```

## 10. 开发环境搭建视频建议

建议录制 5 至 8 分钟，按实际操作顺序展示，不要剪辑出与文档不一致的步骤：

1. 展示项目目录和 Python、Node.js、npm 版本。
2. 展示后端与前端依赖安装命令，或展示已按文档准备完成的终端结果。
3. 启动后端并打开 `/health` 检查服务。
4. 启动前端并打开开发页面。
5. 在登录页注册演示账号并登录。
6. 展示模型设置入口，说明 API Key 由使用者自行配置；不要录入或展示真实密钥。
7. 视时间演示知识库、资料导入、索引完成和问答流程。

录制前关闭含个人信息的窗口和通知，检查终端历史、浏览器自动填充内容及桌面文件名。录制后回看一次，确认画面未泄露密码、API Key、JWT 密钥、个人数据或真实数据库内容。

## 11. 相关文档

- [开发者与用户手册](wenkb_operation_guide.md)
- [部署运维指南](deployment_guide.md)
- [数据库设计](database_design.md)
- [代码维护交接记录](code_maintenance_handoff.md)
