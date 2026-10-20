# WenKB 测试成绩书手动运行与截图指南

版本：v0.1
日期：2026-10-20
对应工作簿：[测试成绩书](../outputs/wenkb-test-book-in-progress/第14小组_基于大模型的个人知识库系统_测试成绩书.xlsx)

## 1. 目的与范围

本指南用于手动取得测试成绩书“运行”页末尾的项目实际运行截图。操作内容是启动冒烟检查和主要页面核验，不代替 [测试计划](test_plan.md) 中的 48 条核心用例，也不能据此将项目整体标记为通过。

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

在一个新的 PowerShell 窗口中，将 `<隔离后端目录>` 替换成上一节显示的完整目录：

```powershell
$repoRoot = 'E:\111学习\4.1大四上\校内实习\wenkb-main'
Set-Location '<隔离后端目录>'
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

使用 Windows 截图工具或 `Win+Shift+S` 截取实际界面。建议先将 PNG 保存在 `outputs/wenkb-test-book-in-progress/evidence/`，命名为 `S01-health.png` 至 `S06-search-chat.png`，然后在 Excel“运行”页把图片粘贴到同编号区域，并填写实际结果、日期和执行者。也可直接在 Excel 中插入图片；保持地址栏或页面标题等必要上下文可辨认。

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

在工作簿“运行”页末尾：

1. 填写项目版本、Git 提交、操作系统、浏览器、执行者和执行日期。
2. 对 S01 至 S06 逐项填写结果、日期、执行者及截图编号/文件名。未操作的项目保持“待人工执行”；确实因环境依赖无法继续时记录“阻塞”及原因。
3. 将对应实际截图贴入同编号空白区域；如图片遮挡标题或其他内容，缩小图片或移动到本编号区域。
4. “运行”页的 S01 至 S06 是运行证据，不进入 48 条核心用例的汇总。测试计划用例须在“测试项目”页逐条执行并回填，不能用首页、健康接口或几张截图代替。

## 8. 停止与清理

完成截图后，在前端和后端终端分别按 `Ctrl+C` 停止服务。确认 PNG 已保存或已粘贴进工作簿后，只清理本轮创建的唯一临时目录 `wenkb-scorebook-run-<本次时间戳>`；不要删除仓库中的 `wenkb-server/resources`、数据库、向量库或上传文件。
