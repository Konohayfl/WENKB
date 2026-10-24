# WenKB 接口设计说明书

版本：v0.1  
日期：2026-09-02  
阶段：接口设计  
范围：本文件基于需求分析、概要设计、详细设计与数据库设计说明，定义 WenKB 目标产品的对外接口契约、请求响应格式、接口分组、状态语义与调用约束，不绑定具体实现代码。

## 1. 文档目的

本文用于统一 WenKB 各业务模块的接口边界，便于前端联调、后端实现、测试编写与后续版本演进。

接口设计关注以下内容：

- 接口按业务域如何分组。
- 每个接口的用途、请求参数与响应结构。
- 统一返回格式、分页格式、文件上传格式与流式返回格式。
- 模型配置、知识库、数据集、聊天、搜索、文档集之间如何协作。
- 接口错误如何返回、如何重试、如何保持历史数据可追溯。

## 2. 设计依据

- 需求分析说明书
- 概要设计说明书
- 详细设计说明书
- 数据库设计说明书

本文件遵循“先需求、后设计、再实现”的顺序，只描述目标产品应提供的接口契约，不以任何具体代码文件作为设计前提。

## 3. 接口设计原则

- 职责单一：一个接口只负责一个清晰的业务动作。
- 资源分组：按系统配置、知识库、数据集、聊天、搜索、文档集拆分接口。
- 契约稳定：请求字段和返回字段尽量保持稳定，避免随意改名。
- 统一返回：成功、失败、分页、流式返回遵循统一格式。
- 可追踪：所有写操作都应带上操作者和时间信息。
- 可重试：索引、增强、引用生成等异步动作应可重试。
- 可扩展：后续新增模型供应商、数据源类型和编排能力时，接口结构应便于扩展。

## 4. 通用约定

### 4.1 请求约定

- 普通业务接口采用 JSON 请求体。
- 文件上传接口采用 `multipart/form-data`。
- 列表查询接口采用查询对象 + 分页对象的组合。
- 写接口统一携带当前登录用户上下文。
- 时间字段统一使用 `YYYY-MM-DD HH:MM:SS` 或可序列化的时间字符串。
- ID 字段统一使用字符串类型。

### 4.2 统一返回格式

成功响应：

```json
{
  "code": "0000",
  "success": true,
  "data": {},
  "msg": "操作成功"
}
```

失败响应：

```json
{
  "code": "9999",
  "success": false,
  "data": null,
  "msg": "发生内部错误"
}
```

分页响应应额外返回：

- `total`：总条数。
- `size`：每页大小。
- `page`：当前页码。
- `pages`：总页数。

### 4.3 错误约定

| code | 含义 |
|---|---|
| `0000` | 成功 |
| `9998` | 业务异常 |
| `9999` | 系统异常 |

### 4.4 流式返回约定

聊天问答采用 SSE 或等价流式方式返回，事件类型统一为：

| 事件类型 | 含义 |
|---|---|
| `chat_message_entity` | 发送初始消息实体 |
| `chat_message_chunk` | 增量回答片段 |
| `chat_message_quote` | 引用来源 |
| `chat_message_error` | 流式过程错误 |

### 4.5 分页约定

分页请求使用统一分页对象，核心字段为：

- `pageNum`：页码。
- `pageSize`：每页条数。
- `orderName`：排序字段。
- `orderValue`：排序方向。

## 5. 接口总览

| 业务域 | 说明 |
|---|---|
| 系统能力 | 健康检查 |
| 用户认证 | 账号注册、登录与 JWT 签发 |
| 系统配置 | 模型供应商、模型、参数、首选项、文件上传 |
| 知识库 | 知识库、知识库设置、知识问答对 |
| 数据集 | 导入、目录、分段、摘要、三元组、索引错误 |
| 聊天 | 对话、消息、引用、重生成 |
| 搜索 | 语义搜索与历史记录 |
| 文档集 | 文档集、文档、版本、转数据集 |

## 6. 系统配置接口

### 6.0 账号认证接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/sys/auth/regist` | 注册账号 | `username`, `nickname`, AES 加密的 `password`, `cfimpswd` | 用户 ID 与昵称 |
| POST | `/sys/auth/login` | 验证账号并登录 | `username`, AES 加密的 `password` | 用户 ID、昵称与 7 天 HS256 JWT |

认证接口不要求已有 JWT；其他受保护 API 必须校验登录凭证。注册账号唯一，密码经服务端解密后以 PBKDF2-HMAC-SHA256 哈希存储。登录失败统一返回账号或密码错误，不区分账号是否存在。

### 6.1 模型供应商与模型接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| GET | `/health` | 检查服务与数据库状态 | 无 | 健康状态 |
| POST | `/sys/model/prvd/list` | 查询全部模型供应商 | 空或筛选对象 | 供应商列表 |
| POST | `/sys/model/prvd/my/list` | 查询当前用户可用供应商 | 无 | 供应商列表 |
| GET | `/sys/model/prvd/modl/my/list/{prvdId}` | 查询供应商下当前用户可用模型 | `prvdId` | 模型列表 |
| GET | `/sys/model/prvd/param/list/{prvdId}` | 查询供应商参数定义 | `prvdId` | 参数定义列表 |
| POST | `/sys/model/param/my/list` | 查询当前用户的模型参数 | `prvdId`, `modlId` | 参数列表 |
| POST | `/sys/model/param/prvd/{prvdId}` | 保存供应商级参数 | 参数数组 | 操作结果 |
| DELETE | `/sys/model/setting/{prvdId}` | 删除供应商配置 | `prvdId` | 操作结果 |
| GET | `/sys/model/prvd/modl/{modlId}` | 查询单个模型及参数 | `modlId` | 模型与参数 |
| POST | `/sys/model/prvd/modl/{prvdId}` | 新增或保存用户模型 | 模型对象 + 参数数组 | 操作结果 |
| DELETE | `/sys/model/prvd/modl/{modlId}` | 删除用户模型 | `modlId` | 操作结果 |
| GET | `/sys/model/my/list` | 查询当前用户可用模型树 | 无 | 供应商-模型树 |

### 6.2 模型首选项接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| GET | `/sys/setting/user/{prmCd}` | 查询用户系统参数 | `prmCd` | 单个参数 |
| POST | `/sys/setting/user` | 保存用户系统参数 | 参数对象 | 保存后的参数 |

### 6.3 文件上传接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/sys/file/upload` | 上传通用文件 | `multipart/form-data`，字段 `file` | 文件元数据 |

规则：

- 敏感模型参数在保存前应进行加密。
- 回显敏感参数时应脱敏或不返回原值。
- 文件上传响应应返回文件 ID、名称、路径、类型和大小，便于后续导入业务复用。

## 7. 知识库接口

### 7.1 知识库基础接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| GET | `/knb/repository/{id}` | 查询单个知识库 | `id` | 知识库详情 |
| POST | `/knb/repository/list` | 查询全部知识库 | 空或筛选对象 | 知识库列表 |
| POST | `/knb/repository/my/list` | 查询当前用户知识库 | 空或筛选对象 | 知识库列表 |
| POST | `/knb/repository` | 新建知识库 | 知识库对象 | 新建结果 |
| PUT | `/knb/repository` | 修改知识库 | 知识库对象 | 操作结果 |
| DELETE | `/knb/repository/{id}` | 删除知识库 | `id` | 操作结果 |
| PUT | `/knb/repository/name` | 修改名称 | 知识库对象 | 操作结果 |
| PUT | `/knb/repository/desc` | 修改介绍 | 知识库对象 | 操作结果 |
| PUT | `/knb/repository/auth/range` | 修改权限范围 | 知识库对象 | 操作结果 |
| DELETE | `/knb/repository/chat/clear/{id}` | 清空知识库聊天 | `id` | 操作结果 |

### 7.2 知识库问答对接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/knb/repository/quest/list` | 查询知识库问答对 | 知识库对象 | 问答对列表 |
| POST | `/knb/repository/quest` | 新增问答对 | 问答对象 | 新增结果 |
| PUT | `/knb/repository/quest` | 修改问答对 | 问答对象 | 操作结果 |
| DELETE | `/knb/repository/quest/{qstId}` | 删除问答对 | `qstId` | 操作结果 |
| POST | `/knb/repository/guess/list` | 模糊查询候选问答 | 问答对象 | 问答建议列表 |
| POST | `/knb/repository/quest/page` | 分页查询问答对 | 问答对象 + 分页对象 | 分页结果 |

### 7.3 知识库设置接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| GET | `/knb/repository/setting/{reposId}` | 查询知识库设置 | `reposId` | 设置对象 |
| POST | `/knb/repository/setting` | 新增或修改知识库设置 | 设置对象 | 操作结果 |

规则：

- 创建知识库时必须指定 embedding 模型。
- 知识库参数修改应影响后续问答，不影响历史消息。
- 知识库名称、描述、权限、问答对和设置类写操作应先校验当前用户的知识库修改权限。
- 删除知识库前应清理其数据集、聊天、搜索等关联对象。

## 8. 数据集接口

### 8.1 数据集基础接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/knb/dataset/list` | 查询数据集列表 | 数据集对象 | 数据集列表 |
| POST | `/knb/dataset/page` | 分页查询数据集 | 数据集对象 + 分页对象 | 分页结果 |
| PUT | `/knb/dataset` | 修改数据集基本信息 | 数据集对象 | 操作结果 |
| DELETE | `/knb/dataset/{id}` | 删除数据集 | `id` | 操作结果 |
| POST | `/knb/dataset/reindex/{id}` | 重新构建索引 | `id` + 类型数组 | 操作结果 |

### 8.2 文档与链接导入接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/knb/dataset/upload/document` | 上传文档数据集 | `multipart/form-data`，字段 `file`、`reposId`、`ctlgId` | 数据集对象 |
| POST | `/knb/dataset/upload/link` | 导入网页链接数据集 | 链接数组、`reposId`、`ctlgId` | 操作结果 |
| POST | `/knb/dataset/links/title` | 批量获取网页标题 | URL 数组 | URL-标题映射 |

### 8.3 启用与构建状态接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| PUT | `/knb/dataset/enable/status` | 修改启用状态 | 数据集对象 | 操作结果 |
| PUT | `/knb/dataset/build/status` | 修改构建状态 | `dtsetId`、`buildKey`、`buildValue` | 操作结果 |

### 8.4 分段、摘要、三元组接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/knb/dataset/chunk/page` | 分页查询分段 | 分段对象 + 分页对象 | 分页结果 |
| PUT | `/knb/dataset/chunk/content` | 修改分段内容 | 分段对象 | 操作结果 |
| DELETE | `/knb/dataset/chunk/{chkId}` | 删除分段 | `chkId` | 操作结果 |
| POST | `/knb/dataset/precis/page` | 分页查询摘要 | 摘要对象 + 分页对象 | 分页结果 |
| POST | `/knb/dataset/precis` | 新增摘要 | 摘要对象 | 新增结果 |
| PUT | `/knb/dataset/precis/content` | 修改摘要内容 | 摘要对象 | 操作结果 |
| DELETE | `/knb/dataset/precis/{prcsId}` | 删除摘要 | `prcsId` | 操作结果 |
| POST | `/knb/dataset/triplet/page` | 分页查询三元组 | 三元组对象 + 分页对象 | 分页结果 |
| GET | `/knb/dataset/triplet/{dtsetId}` | 查询数据集全部三元组 | `dtsetId` | 三元组列表 |
| POST | `/knb/dataset/triplet` | 新增三元组 | 三元组对象 | 新增结果 |
| PUT | `/knb/dataset/triplet` | 修改三元组 | 三元组对象 | 操作结果 |
| DELETE | `/knb/dataset/triplet/{tpltId}` | 删除三元组 | `tpltId` | 操作结果 |

### 8.5 数据集目录接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/knb/dataset/catalog/list` | 查询目录列表 | 目录对象 | 目录列表 |
| POST | `/knb/dataset/catalog` | 新增目录 | 目录对象 | 新增结果 |
| PUT | `/knb/dataset/catalog` | 修改目录 | 目录对象 | 操作结果 |
| PUT | `/knb/dataset/catalog/sort` | 调整目录顺序 | 目录数组 | 操作结果 |
| DELETE | `/knb/dataset/catalog/{id}` | 删除目录 | `id` | 操作结果 |

### 8.6 索引错误接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| GET | `/knb/dataset/index/error/{dtsetId}/{idxTyp}` | 查询索引错误 | `dtsetId`, `idxTyp` | 错误对象 |

规则：

- 文档导入后主索引默认进入待处理状态，网页链接导入可直接启用。
- 数据集目录删除后，目录下数据集应回到未分类状态。
- 修改分段、摘要或三元组后，应同步更新向量索引。
- 数据集导入、编辑、删除、重建、目录和衍生对象写操作应先校验所属知识库权限。
- 索引失败必须能返回可查询的错误信息。

## 9. 聊天接口

### 9.1 对话接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/knb/chat/list` | 查询对话列表 | 对话对象 | 对话列表 |
| POST | `/knb/chat/my/list` | 查询当前用户对话列表 | 对话对象 | 对话列表 |
| POST | `/knb/chat` | 新增对话 | 对话对象 | 新增结果 |
| PUT | `/knb/chat` | 修改对话 | 对话对象 | 操作结果 |
| DELETE | `/knb/chat/{id}` | 删除对话 | `id` | 操作结果 |
| DELETE | `/knb/chat/message/clear/{id}` | 清空对话消息 | `id` | 操作结果 |

### 9.2 消息接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/knb/chat/message/list` | 查询对话消息 | 消息对象 | 消息列表 |
| DELETE | `/knb/chat/message/{id}` | 删除消息及子消息 | `id` | 操作结果 |
| POST | `/knb/chat/remessage` | 重新生成消息 | 原消息 + 历史消息数组 | SSE 流 |
| POST | `/knb/chat/message` | 发送新消息并生成回答 | 新消息 + 历史消息数组 | SSE 流 |
| PUT | `/knb/chat/message` | 修改消息内容 | 消息对象 | 操作结果 |

### 9.3 聊天流式协议

流式响应按以下顺序输出：

1. `chat_message_entity`：发送初始助手消息实体。
2. `chat_message_chunk`：连续输出回答片段。
3. `chat_message_quote`：输出引用来源。
4. `chat_message_error`：在发生错误时输出错误信息。

### 9.4 消息与引用字段约定

消息对象至少包含：

- `mesgId`：消息 ID。
- `mesgPid`：父消息 ID。
- `reposId`：知识库 ID。
- `chatId`：对话 ID。
- `mesgCntnt`：消息内容。
- `mesgTyp`：消息类型。
- `crtRole`：创建角色。

引用对象至少包含：

- `mesgId`：所属助手消息。
- `dtsetId`：数据集 ID。
- `dtsetNm`：数据集名称。
- `fileNm`：文件名。
- `fileTyp`：文件类型。
- `score`：相似度。
- `content`：引用片段内容。

规则：

- 新用户消息应先落库，再触发流式生成。
- 重新生成应复用原消息链路，并保留历史版本。
- 结束时必须保存最终回答和引用。
- 对话、消息、清空、删除、重生成和改写操作应先校验对话及所属知识库权限。

## 10. 搜索接口

### 10.1 搜索与历史接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/knb/search` | 语义搜索 | 搜索对象 | 搜索结果列表 |
| POST | `/knb/search/hist/list` | 查询知识库搜索历史 | 历史对象 | 历史列表 |
| POST | `/knb/search/hist/my/list` | 查询当前用户搜索历史 | 历史对象 | 历史列表 |
| DELETE | `/knb/search/hist/{srchId}` | 删除搜索历史 | `srchId` | 操作结果 |

### 10.2 搜索请求与结果约定

搜索请求核心字段：

- `reposId`：知识库 ID。
- `searchTxt`：搜索文本。
- `noHist`：是否不记录历史。

搜索结果至少包含：

- 来源 ID。
- 来源名称。
- 来源类型。
- 相似度分数。
- 命中文本内容。

规则：

- 搜索优先走语义检索。
- 需要时可保留关键词过滤能力作为扩展。
- 搜索历史应支持按用户查询和删除。
- 搜索与历史删除应先校验当前用户对所属知识库的访问权限。

## 11. 文档集接口

### 11.1 文档集接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| GET | `/doc/docset/{id}` | 查询单个文档集 | `id` | 文档集详情 |
| POST | `/doc/docset/list` | 查询全部文档集 | 空或筛选对象 | 文档集列表 |
| POST | `/doc/docset/my/list` | 查询当前用户文档集 | 空或筛选对象 | 文档集列表 |
| POST | `/doc/docset` | 新增文档集 | 文档集对象 | 新增结果 |
| PUT | `/doc/docset` | 修改文档集 | 文档集对象 | 操作结果 |
| DELETE | `/doc/docset/{id}` | 删除文档集 | `id` | 操作结果 |
| PUT | `/doc/docset/name` | 修改名称 | 文档集对象 | 操作结果 |
| PUT | `/doc/docset/desc` | 修改介绍 | 文档集对象 | 操作结果 |
| PUT | `/doc/docset/auth/range` | 修改权限范围 | 文档集对象 | 操作结果 |

### 11.2 文档接口

| 方法 | 路径 | 用途 | 请求 | 响应 |
|---|---|---|---|---|
| POST | `/doc/document/list/{id}` | 查询文档集下文档列表 | `id` | 文档列表 |
| POST | `/doc/document` | 新增文档 | 文档对象 | 新增结果 |
| PUT | `/doc/document` | 修改文档 | 文档对象 | 操作结果 |
| DELETE | `/doc/document/{id}` | 删除文档 | `id` | 操作结果 |
| GET | `/doc/document/{id}` | 查询文档详情 | `id` | 文档详情 |
| PUT | `/doc/document/content` | 修改文档内容 | 文档对象 | 操作结果 |
| POST | `/doc/document/to/dataset` | 文档转数据集 | 转换表单 | 操作结果 |
| GET | `/doc/document/reposid/list/{docId}` | 查询文档关联知识库 | `docId` | 知识库 ID 列表 |

### 11.3 文档对象约定

文档对象至少包含：

- `setId`：文档集 ID。
- `docId`：文档 ID。
- `docTtl`：文档标题。
- `docTyp`：文档类型。
- `docCntnt`：文档内容。
- `docPid`：父文档 ID。
- `docPath`：文档路径。

规则：

- 文档内容更新应保留版本轨迹。
- 文档转数据集后，数据集应记录来源文档与版本。
- 文档集名称、描述、权限和文档标题写操作应先校验文档集修改权限。

## 12. 接口协作约束

- 模型配置接口负责提供可用模型，知识库接口负责绑定 embedding 模型。
- 数据集接口负责导入与构建，聊天接口负责检索增强问答。
- 搜索接口与聊天接口共享同一知识检索能力。
- 文档集接口可在后续作为知识加工入口，与数据集接口形成转换链路。
- 删除知识库或数据集时，必须同步考虑聊天、引用和向量索引的一致性。

## 13. 可测试性设计

接口设计完成后，应至少覆盖以下测试点：

- 模型供应商和模型列表是否可查询。
- 敏感参数保存后是否加密、回显是否脱敏。
- 知识库创建与设置保存是否正确。
- 文档导入、网页导入、目录管理是否正确。
- 数据集分段、摘要、Q&A、三元组的增删改查是否正确。
- 聊天 SSE 是否按约定输出消息、片段、引用和错误。
- 搜索历史是否按用户可查、可删。
- 文档集转数据集是否保留来源关系。

## 14. 验收标准

接口设计文档完成后，应满足：

- 覆盖系统配置、知识库、数据集、聊天、搜索和文档集主要接口。
- 明确统一返回、分页和 SSE 流式协议。
- 明确关键请求字段、响应字段和状态语义。
- 能作为前后端联调、接口测试和后续扩展的契约基线。
