# WenKB 测试成绩书手动运行与截图指南

版本：v0.1
日期：2026-10-20
对应工作簿：[测试成绩书](../outputs/wenkb-test-book-in-progress/第14小组_基于大模型的个人知识库系统_测试成绩书.xlsx)

## 1. 目的与范围

本指南用于补齐测试成绩书“运行”页的 S01 至 S06 实际运行截图，不要求重复执行核心用例，也不能据截图将项目整体标记为通过。当前成绩与验证边界见[测试成绩书交接](test_scorebook_handoff.md)，原始失败和阻塞诊断见[失败与阻塞跟踪](test_execution_followup.md)。

原示例工作簿中的运行截图属于其他项目，不能作为 WenKB 证据。本指南要求截图来自本次实际启动的 WenKB 页面或健康检查响应，并在“运行”页 S01 至 S06 区域逐项粘贴。

## 2. 安全前提

后端启动时会检查并升级相对路径 `wenkb-server/resources/database/wenkb.db`。不要直接在当前工作目录启动后端，以免修改已有数据库。以下流程把后端代码复制到新的临时目录，并排除整个 `resources` 目录；启动后产生的数据库、上传文件和向量数据均留在临时副本中。

- Windows PowerShell。
- 仓库根目录可访问，且本机已有项目虚拟环境 `.venv` 和前端依赖 `wenkb-client/node_modules`；若缺少依赖，先按项目 README 和开发者手册完成准备。
- 默认端口 `16088`（后端）及 `11420`（前端）未被占用。不要自动结束不明进程。
- 不要导入个人、课程交付或生产资料；只使用新建的非敏感测试样本。
- 不要在截图中展示 API Key、访问令牌、个人文件路径或私人资料。需要配置模型时只使用专用测试凭据，并在截图前遮盖敏感字段。

## 3. 建立隔离后端副本

在仓库根目录打开 PowerShell，先确认默认端口没有占用：

```powershell
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalPort -in 16088, 11420 }
```

若命令列出监听进程，先确认所属应用；不要结束不明进程。然后创建带时间戳的新隔离目录并复制后端代码，不复制运行资源：

```powershell
$repoRoot = (Resolve-Path '.').Path
$serverSource = Join-Path $repoRoot 'wenkb-server'
$runId = Get-Date -Format 'yyyyMMdd-HHmmss'
$runRoot = Join-Path $env:TEMP "wenkb-scorebook-run-$runId"
$runServer = Join-Path $runRoot 'wenkb-server'

New-Item -ItemType Directory -Path $runRoot | Out-Null
robocopy $serverSource $runServer /E /XD (Join-Path $serverSource 'resources') (Join-Path $serverSource '__pycache__')
if ($LASTEXITCODE -ge 8) { throw "后端代码复制失败，robocopy exit code: $LASTEXITCODE" }
Write-Host "隔离后端目录：$runServer"
```

记录输出的隔离目录路径。每次运行都使用新的时间戳目录；如果目录已经存在，请重新生成一个新路径，不要将文件复制到旧测试库中。

## 4. 启动并检查服务

受保护 API 现在需要有效 HS256 JWT。隔离手工测试需在后端进程中设置测试专用 `WENKB_JWT_SECRET`（至少 32 字节），并使用同一密钥生成短期测试用户 token；不要使用生产密钥。当前后端尚未实现前端所调用的登录/注册接口，因此可在浏览器开发者工具 Console 中仅为本地隔离环境写入 `token` 和 `info` 两个 localStorage 项后刷新页面：

```javascript
localStorage.setItem('token', '<隔离测试用户 JWT>')
localStorage.setItem('info', JSON.stringify({ id: 'scorebook-test-user', name: 'scorebook-test-user' }))
location.reload()
```

在用于生成测试凭证的 PowerShell 窗口中设置与服务完全相同的密钥，并从隔离后端目录运行以下命令：

```powershell
$repoRoot = 'E:\111学习\4.1大四上\校内实习\wenkb-main'
$env:WENKB_JWT_SECRET = '<与服务窗口完全相同的至少32字节临时密钥>'
Set-Location '<隔离后端目录>'
$testToken = (& "$repoRoot\.venv\Scripts\python.exe" -c "from server.utils.jwtutils import generate_token; print(generate_token({'id': 'scorebook-test-user', 'name': 'scorebook-test-user'}))").Trim()
Write-Host $testToken
```

将生成值作为上方 Console 命令中的 `<隔离测试用户 JWT>`。不要将 token 或密钥放入截图、工作簿或 Git。

在一个新的 PowerShell 窗口中，将 `<隔离后端目录>` 替换成上一节显示的完整目录：

```powershell
$repoRoot = 'E:\111学习\4.1大四上\校内实习\wenkb-main'
Set-Location '<隔离后端目录>'
$env:WENKB_JWT_SECRET = '<与隔离认证测试相同的至少32字节临时密钥>'
& "$repoRoot\.venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 16088
```

保持窗口运行。此命令只绑定本机回环地址，不对局域网开放。等控制台显示服务已启动后，在浏览器打开 `http://127.0.0.1:16088/health`。成功响应应满足：HTTP 请求成功，JSON 中 `success` 为 `true`，`data.status` 与 `data.database` 均为 `ok`。也可在 PowerShell 用以下命令检查：

```powershell
$health = Invoke-RestMethod 'http://127.0.0.1:16088/health'
$health | ConvertTo-Json -Depth 5
```

如果启动、数据库或健康检查失败，保留真实错误信息，遮盖任何敏感字段后将 S01 标为“失败”或“阻塞”；不要继续填写成功结论。

## 5. 启动浏览器前端

保持后端运行，在另一个 PowerShell 窗口从仓库根目录启动前端：

```powershell
$repoRoot = 'E:\111学习\4.1大四上\校内实习\wenkb-main'
Set-Location "$repoRoot\wenkb-client"
npm run dev -- --host 127.0.0.1
```

浏览器打开 `http://127.0.0.1:11420/#/main/repository`。Vite 前端代理连接本机 `16088` 后端；不要改用未确认的其他后端实例。若页面无法加载，先检查两个服务窗口和端口，再记录现象，不要把静态页面可打开当作接口通过。

## 6. 操作与截图清单

使用 Windows 截图工具或 `Win+Shift+S` 截取实际界面。建议先将 PNG 保存在 `outputs/wenkb-test-book-in-progress/evidence/`，命名为 `S01-health.png` 至 `S06-search-chat.png`，然后在 Excel“运行”页把图片粘贴到同编号区域。保持地址栏或页面标题等必要上下文可辨认，并避免截图显示 API Key、令牌或私人资料。

| 编号 | 操作 | 截图证据与记录 |
|---|---|---|
| S01 | 打开 `/health`，确认健康状态和数据库状态；必要时同时保留后端启动终端。 | `S01-health.png`；记录 HTTP/JSON 实际结果。 |
| S02 | 打开 WenKB 浏览器工作区，检查知识库首页及主导航。 | `S02-workspace.png`；确认知识库、搜索、聊天、文档集入口真实可见。 |
| S03 | 打开“设置 > 模型设置”。 | `S03-model-settings.png`；记录模型是否已配置。密钥必须隐藏；未配置本身不等于页面启动失败。 |
| S04 | 查看知识库列表；若已准备测试 embedding 模型，可在隔离副本中新建一个带“手动测试”标记的知识库并打开详情。 | `S04-repository.png`；只记录隔离库中的真实列表/详情。未配置必要模型时，不要伪造创建成功。 |
| S05 | 如 S04 条件满足，使用非敏感 TXT/Markdown 样例导入测试资料并查看数据集状态。 | `S05-dataset.png`；保留文件名、数据集状态和可见错误，不能把未索引写成 ready。 |
| S06 | 仅当隔离库中配置了可用测试模型且资料已索引时，执行一次带来源的搜索或问答。 | `S06-search-chat.png`；记录真实回答与来源引用。缺少模型或索引时，标为“阻塞”并说明原因，或记录为未执行。 |

模型配置和索引需要额外服务，可能无法在当前机器完成。此时可完成 S01 至 S04 中不依赖模型的实际检查，并如实保留 S05/S06 的状态；不要为了截图配置生产凭据。

## 7. 回填成绩书

工作簿已记录隔离环境、执行日期、S01 至 S05 通过、S06 因缺少可用模型/索引而阻塞。只需补贴实际截图；如果新运行观察与现有状态不同，再按实际结果修订该行，不要为配合截图保留错误结论。

| 编号 | Excel“运行”页截图粘贴区域 |
|---|---|
| S01 | `A55:I61` |
| S02 | `A64:I70` |
| S03 | `A73:I79` |
| S04 | `A82:I88` |
| S05 | `A91:I97` |
| S06 | `A100:I106` |

不要重跑会重建成绩书的生成命令，以免覆盖已回填的 48 条执行结果。S01 至 S06 运行证据不进入核心用例汇总；S06 缺少真实模型与索引时贴阻塞界面或错误现象，不得伪造问答结果。

## 8. 停止与清理

完成截图后，在前端和后端终端分别按 `Ctrl+C` 停止服务。确认 PNG 已保存或已粘贴进工作簿后，只清理本轮创建的唯一临时目录 `wenkb-scorebook-run-<本次时间戳>`；不要删除仓库中的 `wenkb-server/resources`、数据库、向量库或上传文件。
