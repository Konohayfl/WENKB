import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const outputDir = path.join(root, "outputs", "wenkb-test-book-in-progress");
const outputPath = path.join(outputDir, "第14小组_基于大模型的个人知识库系统_测试成绩书.xlsx");
const previewDir = path.join(os.tmpdir(), "wenkb-test-book-previews");
const font = "Microsoft YaHei";

const colors = {
  ink: "#1F2937",
  muted: "#64748B",
  navy: "#17365D",
  blue: "#DCE6F1",
  blueLight: "#F3F7FB",
  green: "#E2F0D9",
  amber: "#FFF2CC",
  red: "#FCE4D6",
  border: "#A6A6A6",
  white: "#FFFFFF",
};

const tc = (plan, requirements, title, priority, preconditions, steps, expected, notes) => ({
  plan, requirements, title, priority, preconditions, steps, expected, notes,
});

const testCases = [
  tc("TP-001", "NFR-001/NFR-003", "后端与数据库健康检查", "高", "Windows 本地环境已安装依赖；数据库服务或文件可访问。", "1. 启动后端。\n2. 请求 /health。\n3. 分别在数据库可用和不可用条件下检查响应。", "正常条件返回明确健康状态；数据库不可用时返回可识别失败状态，不输出敏感配置。", "记录 HTTP 状态、响应摘要和服务日志编号。"),
  tc("TP-001", "NFR-001", "前端入口与后端连接反馈", "高", "后端和前端均已启动；准备一次后端不可达场景。", "1. 打开浏览器端和桌面端入口。\n2. 进入模型、知识库和聊天页面。\n3. 停止后端并观察连接提示及恢复行为。", "服务可用时页面可进入；后端不可达时显示明确错误或重试状态，不把连接失败显示为正常。", "记录浏览器/桌面端入口及连接状态截图。"),
  tc("TP-001", "NFR-001/NFR-005", "数据库版本升级启动", "高", "准备上一受支持版本的可恢复数据库副本并记录关键数据数量。", "1. 从旧版本数据库副本启动服务。\n2. 检查升级日志和数据库版本。\n3. 重启一次并核对关键记录。", "迁移按版本顺序完成；版本号更新；重启不重复破坏数据；失败时保留可追踪错误。", "仅在副本执行，保存迁移日志及升级前后记录数量。"),
  tc("TP-001", "NFR-007", "Windows 中文路径文件读写", "中", "准备存放在含中文和空格路径下的可解析文档。", "1. 将文档放在中文目录。\n2. 上传并索引。\n3. 检查文件名、路径、读取和检索结果。", "文件路径可读写；导入记录可追溯；中文文件名和目录名不导致服务异常。", "记录测试文件名和数据集 ID，不复制敏感文件内容。"),

  tc("TP-002", "FR-001/FR-002", "供应商与模型清单维护", "高", "准备可用模型供应商及其支持的模型类型。", "1. 查看内置供应商。\n2. 新增一个用户模型并编辑名称/类型。\n3. 重新读取列表。", "供应商和模型列表可查询；新增模型保存后可重新读取；聊天模型和 embedding 模型按类型区分。", "记录供应商、模型 ID 和模型类型。"),
  tc("TP-002", "FR-001/NFR-004", "供应商参数保存与 API Key 脱敏", "高", "使用专用测试凭据，不得使用生产 API Key。", "1. 保存供应商服务地址和测试 API Key。\n2. 重新查询参数。\n3. 检查持久化加密标记和界面回显。", "参数保存成功；敏感值加密保存；查询或界面回显不暴露完整 API Key。", "记录脱敏格式和参数加密状态，不记录真实密钥。"),
  tc("TP-002", "FR-003", "默认 LLM 选择与后续调用", "高", "至少配置两个可用聊天模型并准备可识别的测试提示。", "1. 将模型 A 设为默认 LLM 并保存。\n2. 发起问答或增强任务。\n3. 切换为模型 B 后再次发起任务。", "保存的默认模型在后续问答/增强中生效；切换后使用新选择，模型调用结果可追踪。", "用服务日志或可控模型响应确认实际调用模型。"),
  tc("TP-002", "FR-003/NFR-003", "缺省或不可用模型异常提示", "高", "准备未设置默认 LLM 和模型服务不可达两种配置。", "1. 未配置默认 LLM 时发起问答。\n2. 配置无效服务地址后发起任务。\n3. 检查页面提示和日志。", "系统明确提示模型未配置或不可用；失败上下文可追踪；API Key 等敏感值不进入错误信息。", "记录错误类型、用户提示和日志编号。"),

  tc("TP-003", "FR-004", "知识库创建与私有默认值", "高", "已配置可用 embedding 模型；当前测试用户可创建知识库。", "1. 填写知识库名称和介绍。\n2. 选择 embedding 模型并保存。\n3. 重新查询知识库及其可见性。", "知识库创建成功并绑定所选 embedding 模型；新建知识库默认私有；详情可重新读取。", "记录知识库 ID、模型 ID 和权限范围。"),
  tc("TP-003", "FR-004", "知识库必填项校验", "高", "使用专用测试环境。", "1. 分别留空知识库名称和 embedding 模型。\n2. 尝试保存。\n3. 检查列表和数据库中是否产生无效记录。", "缺少必填项时拒绝创建并给出明确提示；不产生名称或索引模型缺失的知识库。", "记录每种输入的提示和保存结果。"),
  tc("TP-003", "FR-005", "问答参数范围与持久化", "高", "已有测试知识库；可查询和修改其问答设置。", "1. 按数据库设计范围设置 topK、上下文数、历史轮数、温度和阈值边界。\n2. 保存并重新读取。\n3. 提交越界值。", "合法范围值可保存并在重新读取后保持一致；越界值被校验；后续问答使用已保存参数。", "记录输入边界、保存值和请求侧验证结果。"),
  tc("TP-003", "FR-004/FR-005", "已有索引时切换 embedding 模型", "高", "测试知识库至少有一个已建立的向量索引。", "1. 修改该知识库绑定的 embedding 模型。\n2. 检查提示或重建任务。\n3. 按提示完成或取消操作并检查检索。", "模型不一致风险被提示；确认切换后触发或要求重建；取消时不破坏原有可检索索引。", "保存切换前后模型 ID、提示和索引状态。"),

  tc("TP-004", "FR-007", "常见文档格式导入", "高", "准备文本型 PDF、DOCX、MD、TXT、PPT/PPTX 各一份样本。", "1. 分别导入各格式文件。\n2. 检查数据集类型、文件名和上传状态。\n3. 检查解析结果是否可供后续切分。", "需求范围内的常见格式建立正确数据集记录；不支持或无法解析的样本显示失败原因，不显示为 ready。", "记录样本格式、文件 ID 和数据集 ID。"),
  tc("TP-004", "FR-007/NFR-006", "批量导入与重复文件名", "中", "准备多份文件，其中两份文件名相同但内容不同，使用隔离测试库。", "1. 批量上传多份文件。\n2. 检查每份上传响应的 ID、名称、类型和大小。\n3. 对相同文件名样本检查数据集关联。", "批量结果可逐项追踪；同名文件不会静默覆盖另一文件；失败项不会被汇总成成功状态。", "保留上传响应摘要和同名样本的区分方式。"),
  tc("TP-004", "FR-008", "多 URL 格式校验与标题读取", "高", "准备多个有效静态网页 URL 和一个格式错误 URL。", "1. 按每行一个 URL 输入多个链接。\n2. 检查格式校验。\n3. 获取网页标题并保存数据集。", "有效 URL 可保存并尽力获取标题；格式错误 URL 被识别；链接和数据集关系可重新查询。", "记录 URL 测试编号、标题和数据集 ID，不记录需授权访问的私有链接。"),
  tc("TP-004", "FR-007/FR-008/NFR-003", "不可访问链接与不可解析文件", "高", "准备不可访问 URL、空文件和损坏文档，使用隔离测试库。", "1. 导入上述异常样本。\n2. 查看数据集状态和索引错误信息。\n3. 检查其他正常数据集仍可使用。", "异常样本失败原因可查询且不会变为 ready；单个异常不导致服务整体退出或阻断其他数据集。", "保存错误类型、提示和日志编号。"),

  tc("TP-005", "FR-009", "仅启用数据集进入索引队列", "高", "准备两个新导入数据集，一个启用、一个停用。", "1. 保持两个数据集初始状态并观察队列。\n2. 确认停用数据集不进入索引。\n3. 启用后观察其状态和队列。", "只有启用的数据集进入索引队列；停用数据集不被后台任务提前索引；启用后可继续处理。", "记录启用标志、状态和队列日志。"),
  tc("TP-005", "FR-009/NFR-002", "索引状态流转与界面响应", "高", "准备内容较多但可解析的文档并启用数据集。", "1. 观察 new、order、index、ready 状态。\n2. 索引运行期间继续操作其他页面。\n3. 查看完成时间和界面状态刷新。", "索引状态可追踪；后台处理不阻塞主要界面操作；完成后数据集进入 ready。", "记录状态时间线和页面响应现象，不预设性能数值。"),
  tc("TP-005", "FR-009/FR-015", "成功索引后参与检索", "高", "准备含唯一可识别短句的文本型文件并成功索引。", "1. 确认数据集 ready。\n2. 用文件中的唯一短句执行搜索。\n3. 从聊天问题中验证相关片段可被检索。", "已索引内容可参与搜索/问答；结果来源指向正确数据集和文件。", "记录查询、命中片段和来源对象 ID。"),
  tc("TP-005", "FR-009/NFR-003", "索引失败记录与恢复重试", "高", "准备一个可控失败样本及修复后的正常版本。", "1. 触发索引失败。\n2. 查看失败状态和错误上下文。\n3. 修复输入后重试。\n4. 检查 ready 状态和错误解决记录。", "失败原因可查询；重试后状态可恢复；成功后旧有效错误被标记解决或清理。", "保留失败和恢复两个阶段的错误编号。"),

  tc("TP-006", "FR-011", "摘要生成及状态跟踪", "中", "数据集主索引已 ready；默认 LLM 可用。", "1. 触发摘要生成。\n2. 观察摘要状态。\n3. 查看生成摘要内容和所属数据集。", "摘要任务按状态推进；生成内容可查询；来源数据集关联正确；失败时保留原因。", "记录摘要 ID、状态和模型错误（如有）。"),
  tc("TP-006", "FR-011/NFR-003", "人工摘要增删改与向量同步", "中", "已有可用数据集；准备一条非敏感摘要文本。", "1. 新增人工摘要。\n2. 修改其内容。\n3. 搜索新旧摘要词句。\n4. 删除摘要并再次搜索。", "摘要来源标记为人工；修改后检索使用新内容；删除后关系记录和对应向量均不再返回。", "记录摘要 ID 和更新/删除后的搜索结果。"),
  tc("TP-006", "FR-012", "自动与人工 Q&A 维护", "高", "数据集主索引已 ready；默认 LLM 可用。", "1. 生成自动 Q&A。\n2. 手工新增一组 Q&A。\n3. 检查来源标记、列表和候选问题。\n4. 修改或删除一条记录。", "自动和人工来源可区分；Q&A 可查询维护；候选问题与检索使用最新有效内容。", "记录 Q&A ID、来源类型和候选列表结果。"),
  tc("TP-006", "FR-013", "三元组抽取、去重与检索同步", "中", "数据集主索引已 ready；准备包含明确实体关系的文本。", "1. 触发三元组抽取。\n2. 核对主体、关系、客体。\n3. 重复提交同一关系并执行编辑、删除。\n4. 检查检索同步。", "三元组字段完整且按规则去重；修改和删除后关系数据与向量索引一致。", "记录三元组 ID、三字段和检索结果。"),

  tc("TP-007", "FR-014", "知识库选择与对话持久化", "高", "已有两个 ready 知识库；已配置可用默认 LLM。", "1. 选择知识库 A 并新建对话。\n2. 发送一个问题。\n3. 切换到知识库 B 并创建另一对话。\n4. 刷新页面后读取对话列表。", "每个对话绑定正确知识库；消息和对话可重新读取；切换知识库不串用其他库的资料。", "记录知识库 ID、对话 ID 和消息 ID。"),
  tc("TP-007", "FR-014/NFR-002", "流式回答与生成中断回退", "高", "准备正常模型和可控中断模型响应。", "1. 提交问题并观察增量事件。\n2. 中断一次生成。\n3. 重新读取消息记录和前端最终内容。", "正常回答流式返回；中断后显示兜底消息或明确错误；最终内容与消息记录一致。", "记录流式事件顺序、消息最终状态和日志编号。"),
  tc("TP-007", "FR-005/FR-014", "多轮历史及上下文参数", "高", "知识库已设置 maxHistory、maxCtx 和检索参数；准备可区分的多轮问题。", "1. 创建多轮对话并提及一个唯一值。\n2. 后续问题引用该值。\n3. 调整历史轮数和上下文片段数后重复验证。", "上下文按知识库设置生效；历史消息不被设置修改追溯性改写；参数变化影响后续请求。", "记录配置值和模型可观察到的上下文差异。"),
  tc("TP-007", "FR-015", "引用字段与历史引用快照", "高", "准备包含文件名、数据集 ID 可识别的已索引资料。", "1. 提出可由该资料回答的问题。\n2. 核对引用中的数据集、文件、类型、相似度和片段。\n3. 重新打开历史消息核对引用。", "答案引用含计划要求的来源字段；历史消息保留对应引用快照；引用能追溯到稳定来源对象。", "保存消息 ID、引用对象 ID 和脱敏截图。"),

  tc("TP-008", "FR-016", "关键词与自然语言语义搜索", "中", "已有内容差异明确的 ready 数据集。", "1. 使用资料中的关键词搜索。\n2. 使用同义自然语言查询。\n3. 调整 TopK/相似度设置后比较结果。", "搜索可处理关键词或自然语言；结果相关且受检索设置影响；未索引内容不被错误返回。", "记录查询文本、TopK、阈值和结果来源。"),
  tc("TP-008", "FR-016", "搜索结果来源与跳转", "中", "已有至少两个可区分来源的索引结果。", "1. 执行能命中两来源的搜索。\n2. 检查结果的知识库、数据集和片段来源。\n3. 点击结果跳转目标详情。", "每条结果包含来源信息；跳转目标与结果对象一致；目标不可用时给出明确反馈。", "记录来源 ID、跳转目标和页面结果。"),
  tc("TP-008", "FR-016/NFR-001", "搜索历史、删除与无结果状态", "中", "准备一个有效查询和一个明确无匹配查询。", "1. 执行两种查询。\n2. 查看搜索历史。\n3. 删除一条历史。\n4. 刷新后检查历史和无结果反馈。", "历史可保存和删除；无结果查询不会显示伪造内容或错误来源；页面提示明确。", "记录历史 ID、结果条数和无结果页面截图。"),
  tc("TP-008", "FR-016/FR-009", "未就绪或停用数据集搜索隔离", "中", "准备一个 ready 数据集、一个未索引数据集和一个停用数据集。", "1. 让三个数据集包含不同唯一短句。\n2. 分别搜索各短句。\n3. 完成索引或重新启用后重复查询。", "只有满足索引和启用规则的数据集参与检索；状态改变后搜索范围按规则更新。", "记录每个短句的命中情况和数据集状态。"),

  tc("TP-009", "FR-017", "文档集与文档基本维护", "中", "当前测试用户可创建文档集和文档。", "1. 创建文档集。\n2. 新建文档并填写标题和正文。\n3. 修改标题和正文后重新读取。", "文档集、文档可创建和编辑；修改结果持久化；列表和详情保持一致。", "记录文档集 ID 和文档 ID。"),
  tc("TP-009", "FR-017", "文档内容版本快照", "中", "已有一篇包含可识别正文的文档。", "1. 记录当前内容和版本号。\n2. 修改正文并保存。\n3. 查看版本列表和历史内容。", "内容修改生成可追溯版本快照；版本顺序明确；旧版本内容未被覆盖。", "记录文档 ID、版本号和修改前后内容摘要。"),
  tc("TP-009", "FR-017/FR-009", "文档转数据集与来源版本", "中", "已有可访问文档和可写知识库；准备一份可索引文档。", "1. 将文档转为目标知识库数据集。\n2. 检查来源文档和版本标识。\n3. 启用并完成索引后执行搜索。", "转入前校验知识库存在性和权限；数据集关联正确文档版本；索引 ready 后可检索。", "记录文档、版本、数据集 ID 和检索来源。"),
  tc("TP-009", "FR-017/NFR-003", "文档及版本删除清理", "中", "准备包含多个版本和另一篇无关文档的文档集。", "1. 删除一个文档并检查版本。\n2. 删除一个文档集并检查其文档和版本。\n3. 确认无关文档仍存在。", "删除文档/文档集时关联版本按规则清理；其他文档集和文档不受影响。", "保存删除前后对象清单。"),

  tc("TP-010", "FR-009~FR-013/NFR-003", "数据集删除及派生对象清理", "高", "在可恢复测试知识库中准备数据集、分段、摘要、自动 Q&A、三元组、错误记录和向量。", "1. 记录对象和向量清单。\n2. 删除数据集。\n3. 查询关系数据、文件资源和向量集合。\n4. 搜索原有唯一内容。", "数据集删除后其分段、摘要、自动 Q&A、三元组、错误记录、文件和向量无残留；其他数据集不受影响。", "仅使用备份可恢复数据；保存删除前后对象清单。"),
  tc("TP-010", "FR-004/FR-014~FR-016", "知识库删除及关联对象清理", "高", "在可恢复测试环境中准备包含数据集、聊天、引用、搜索历史和向量的知识库。", "1. 记录关联对象。\n2. 删除知识库。\n3. 检查数据集、聊天、搜索历史、引用和向量集合。\n4. 检查另一知识库。", "被删知识库的关联对象按设计清理且无脏引用或向量；其他知识库数据保持完整。", "仅在可恢复测试数据上执行，保存删除前后清单。"),
  tc("TP-010", "FR-006/NFR-003", "删除目录后数据集归回未分类", "中", "同一知识库中准备一个目录及至少一个归属该目录的数据集。", "1. 删除目录。\n2. 查询原数据集目录标识和列表位置。\n3. 检查数据集本身和索引。", "目录删除不删除数据集；数据集目录标识清空并回到未分类；索引内容不受影响。", "记录目录 ID、数据集 ID 和目录字段前后值。"),
  tc("TP-010", "FR-010/NFR-003", "分段编辑删除与向量同步", "高", "已有 ready 数据集和包含唯一词句的分段。", "1. 编辑分段中的唯一词句并保存。\n2. 搜索新旧词句。\n3. 删除该分段并再次搜索。", "修改后对应向量更新；删除后向量移除；其他分段仍可检索。", "记录分段 ID、新旧搜索结果和向量对象状态。"),

  tc("TP-011", "FR-004/NFR-004", "私有知识库列表隔离", "高", "测试环境可模拟两个不同用户；用户 A 创建私有知识库。", "1. 使用用户 A 查询知识库列表。\n2. 使用用户 B 查询列表。\n3. 尝试通过用户 B 的界面打开该知识库。", "私有知识库只对所属用户可见；列表和直接访问保持一致，不泄露名称或内容。", "记录用户标识、列表结果和访问响应。"),
  tc("TP-011", "FR-004/NFR-004", "公开知识库可见范围", "中", "测试环境可模拟两个用户；准备公开和私有知识库。", "1. 使用创建者和另一用户分别查询。\n2. 检查公开对象可见性。\n3. 检查公开对象写操作权限。", "公开知识库按设计对其他用户可见；读取与修改权限分别遵循规则；私有对象仍不可见。", "记录可见对象 ID 和读写权限结果。"),
  tc("TP-011", "NFR-004", "越权写操作拒绝且不修改数据", "高", "准备另一用户拥有的知识库、数据集、文档和聊天对象。", "1. 以无权限用户提交编辑和删除请求。\n2. 检查响应错误类型。\n3. 重新以对象所有者查询数据。", "写操作返回明确业务错误；数据库和向量数据未被修改；错误响应不泄露敏感内容。", "记录请求对象 ID、错误码和所有者复查结果。"),
  tc("TP-011", "NFR-004", "无权限直接读取对象", "高", "测试环境可模拟两个用户；准备私有知识库、数据集、聊天和搜索历史。", "1. 以另一用户按对象 ID 请求详情。\n2. 查询关联的消息、引用和历史。\n3. 检查响应体和日志。", "未授权对象不可读取；关联消息、引用和搜索记录不泄露；失败原因可追踪。", "保存接口响应摘要，避免记录私有正文。"),

  tc("TP-012", "P0/TP-001~TP-010", "核心业务端到端回归", "高", "准备可恢复测试环境、默认模型、文档和网页样本。", "1. 启动并创建知识库。\n2. 导入、启用和索引资料。\n3. 执行增强、问答、搜索和引用回溯。\n4. 删除测试数据并核对清理。", "核心闭环各步骤完成；引用来源正确；删除后无残留；本轮变更未引入主链路回退。", "记录版本、每步对象 ID 和失败/回归项。"),
  tc("TP-012", "NFR-003/NFR-005", "数据库与向量数据一致性", "高", "准备隔离测试库和可查询关系库/向量库的验证方式。", "1. 新增并索引一条测试内容。\n2. 修改分段/增强对象。\n3. 删除对象并检查两侧数据。", "关系数据与向量数据在操作完成后保持一致；异常可定位并可按维护流程重建。", "保存对象 ID、查询结果和一致性检查记录。"),
  tc("TP-012", "NFR-007", "浏览器、桌面端与常见路径兼容", "中", "Windows 环境可分别启动浏览器端和 Tauri 桌面端；准备中文路径样本。", "1. 在浏览器和桌面端登录/进入工作区。\n2. 执行知识库列表、导入和问答关键操作。\n3. 检查窗口尺寸变化和中文路径文件。", "两种入口的主要功能可用；内容不被裁切；中文路径可访问；不出现明显横向溢出或未处理错误。", "记录系统/浏览器版本、窗口尺寸和截图。"),
  tc("TP-012", "NFR-003/NFR-005", "静态文档与测试基线一致性", "中", "测试计划、需求、设计、接口和操作手册均为当前审查版本。", "1. 核对 FR/TP 编号和功能范围。\n2. 核对状态术语、错误恢复、引用和删除规则。\n3. 检查测试用例执行字段未预填通过结论。", "文档范围、术语和状态规则一致；工作簿覆盖测试计划 TP-001 至 TP-012；未执行用例不显示为通过。", "记录发现的文档差异、责任文档和修订建议。"),
];

function applyBase(sheet, range) {
  sheet.showGridLines = false;
  const used = sheet.getRange(range);
  used.format.font = { name: font, size: 10, color: colors.ink };
  used.format.verticalAlignment = "center";
}

function styleTitle(sheet, address, value) {
  sheet.mergeCells(address);
  const title = sheet.getRange(address.split(":")[0]);
  title.values = [[value]];
  title.format = {
    font: { name: font, size: 16, bold: true, color: colors.navy },
    horizontalAlignment: "left",
    verticalAlignment: "center",
  };
  title.format.rowHeight = 30;
}

function styleHeader(range) {
  range.format = {
    fill: colors.navy,
    font: { name: font, size: 10, bold: true, color: colors.white },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: colors.border },
  };
}

function styleBody(range) {
  range.format = {
    font: { name: font, size: 9, color: colors.ink },
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: colors.border },
  };
}

function setWidths(sheet, widths, rows) {
  for (const [column, width] of Object.entries(widths)) {
    sheet.getRange(`${column}1:${column}${rows}`).format.columnWidth = width;
  }
}

function buildCover(sheet) {
  applyBase(sheet, "A1:G38");
  setWidths(sheet, { A: 16, B: 18, C: 18, D: 18, E: 18, F: 18, G: 18 }, 38);
  styleTitle(sheet, "A7:G8", "第14小组 基于大模型的个人知识库系统");
  sheet.mergeCells("A10:G11");
  sheet.getRange("A10").values = [["测试成绩书"]];
  sheet.getRange("A10").format = {
    font: { name: font, size: 28, bold: true, color: colors.navy },
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
  sheet.getRange("A2:G3").values = [["文档编号：待编号", null, null, null, null, null, null], ["密级：待确认", null, null, null, null, null, null]];
  sheet.getRange("A2:G3").format.font = { name: font, size: 11, color: colors.ink };
  sheet.getRange("A14:B18").values = [
    ["文档状态", "执行前草案"],
    ["测试基线", "测试计划 v0.1"],
    ["项目范围", "模型、知识库、数据集、索引、增强、问答、搜索、文档集"],
    ["编制日期", new Date("2026-10-20T00:00:00")],
    ["执行状态", "未执行，待填写"],
  ];
  sheet.getRange("A14:B18").format = {
    fill: colors.blueLight,
    font: { name: font, size: 10, color: colors.ink },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: colors.border },
  };
  sheet.getRange("A14:A18").format.font = { name: font, size: 10, bold: true, color: colors.navy };
  sheet.getRange("B17").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("A21:G25").values = [
    ["编制说明", null, null, null, null, null, null],
    ["本成绩书依据需求分析、详细设计、接口设计、操作手册和测试计划整理。执行结果不得预填；每条用例执行后应补充实测结果、状态、日期、测试者和证据。", null, null, null, null, null, null],
    ["工作表说明", null, null, null, null, null, null],
    ["测试项目：核心测试用例；UI界面：页面与流程验收映射；运行：执行汇总、状态判定与缺陷记录。", null, null, null, null, null, null],
    ["来源：docs/test_plan.md、docs/requirements_analysis.md、docs/detailed_design.md、docs/api_design.md、docs/wenkb_operation_guide.md", null, null, null, null, null, null],
  ];
  sheet.mergeCells("A21:G21");
  sheet.mergeCells("A22:G22");
  sheet.mergeCells("A23:G23");
  sheet.mergeCells("A24:G24");
  sheet.mergeCells("A25:G25");
  sheet.getRange("A21:G25").format = { font: { name: font, size: 10, color: colors.muted }, wrapText: true, verticalAlignment: "center" };
  sheet.getRange("A21").format.font = { name: font, size: 10, bold: true, color: colors.navy };
  sheet.getRange("A23").format.font = { name: font, size: 10, bold: true, color: colors.navy };
  sheet.getRange("A22:G22").format.rowHeight = 42;
  sheet.getRange("A24:G24").format.rowHeight = 30;
  sheet.getRange("A25:G25").format.rowHeight = 30;
  sheet.getRange("A33:G35").values = [
    ["实习实训中心", null, null, null, null, null, null],
    ["（项目测试资料）", null, null, null, null, null, null],
    ["总页数", null, "正文", null, "附录", null, "生效日期"],
  ];
  sheet.getRange("A33:G34").format.font = { name: font, size: 11, color: colors.muted };
  sheet.getRange("A35:G35").format = { fill: colors.amber, font: { name: font, size: 9, color: colors.ink }, borders: { preset: "all", style: "thin", color: colors.border }, horizontalAlignment: "center" };
  sheet.getRange("A37:G38").values = [["编制：", null, null, null, "审批：", null, null], ["交付前检查：", "完成全部执行记录、缺陷结论和回归验证后更新封面状态。", null, null, null, null, null]];
  sheet.mergeCells("B38:D38");
  sheet.mergeCells("F38:G38");
  sheet.getRange("A37:G38").format = { font: { name: font, size: 10, color: colors.ink }, wrapText: true, borders: { preset: "all", style: "thin", color: colors.border } };
  sheet.getRange("A37:G38").format.rowHeight = 24;
}

function buildTestCases(sheet) {
  const lastRow = testCases.length + 4;
  const dataRange = `A5:M${lastRow}`;
  applyBase(sheet, `A1:M${lastRow}`);
  styleTitle(sheet, "A1:M1", "WenKB 核心功能测试项目");
  sheet.getRange("A2:M2").values = [["执行状态预置为“未执行”。请在执行后填写实测结果、确定结果、日期、测试者、缺陷编号和证据。", null, null, null, null, null, null, null, null, null, null, null, null]];
  sheet.mergeCells("A2:M2");
  sheet.getRange("A2:M2").format = { fill: colors.amber, font: { name: font, size: 10, color: colors.ink }, wrapText: true, verticalAlignment: "center" };
  sheet.getRange("A4:M4").values = [["用例编号", "需求/计划关联", "测试项", "优先级", "前置条件", "操作步骤", "预期结果", "实测结果", "确定结果", "测试日期", "测试者", "缺陷编号", "证据/备注"]];
  styleHeader(sheet.getRange("A4:M4"));
  const rows = testCases.map((item, index) => [
    `TC-WKB-${String(index + 1).padStart(3, "0")}`,
    `${item.plan} / ${item.requirements}`,
    item.title,
    item.priority,
    item.preconditions,
    `用例标题：${item.title}\n前置条件：${item.preconditions}\n操作步骤：${item.steps}`,
    item.expected,
    "",
    "未执行",
    null,
    "",
    "",
    item.notes,
  ]);
  sheet.getRange(dataRange).values = rows;
  styleBody(sheet.getRange(dataRange));
  sheet.getRange(`A5:D${lastRow}`).format.horizontalAlignment = "center";
  sheet.getRange(`H5:J${lastRow}`).format.horizontalAlignment = "center";
  sheet.getRange(`J5:J${lastRow}`).format.numberFormat = "yyyy-mm-dd";
  sheet.getRange(`I5:I${lastRow}`).format = { fill: colors.amber, font: { name: font, size: 9, bold: true, color: colors.ink }, horizontalAlignment: "center", verticalAlignment: "center", borders: { preset: "all", style: "thin", color: colors.border } };
  sheet.getRange(`I5:I${lastRow}`).dataValidation = { rule: { type: "list", values: ["未执行", "通过", "失败", "阻塞", "不适用"] } };
  const status = sheet.getRange(`I5:I${lastRow}`);
  status.conditionalFormats.add("containsText", { text: "未执行", format: { fill: colors.amber, font: { bold: true, color: "#7F6000" } } });
  status.conditionalFormats.add("containsText", { text: "通过", format: { fill: colors.green, font: { bold: true, color: "#375623" } } });
  status.conditionalFormats.add("containsText", { text: "失败", format: { fill: colors.red, font: { bold: true, color: "#9C0006" } } });
  status.conditionalFormats.add("containsText", { text: "阻塞", format: { fill: colors.amber, font: { bold: true, color: "#9C6500" } } });
  sheet.getRange(`D5:D${lastRow}`).format = { fill: colors.blueLight, font: { name: font, size: 9, bold: true, color: colors.navy }, horizontalAlignment: "center", verticalAlignment: "center", borders: { preset: "all", style: "thin", color: colors.border } };
  sheet.getRange(dataRange).format.rowHeight = 78;
  setWidths(sheet, { A: 15, B: 29, C: 28, D: 9, E: 34, F: 52, G: 42, H: 32, I: 11, J: 13, K: 12, L: 14, M: 31 }, lastRow);
  sheet.freezePanes.freezeRows(4);
  sheet.freezePanes.freezeColumns(1);
  const table = sheet.tables.add(`A4:M${lastRow}`, true, "WenkbTestCaseTable");
  table.style = "TableStyleMedium2";
  table.showFilterButton = true;
}

function buildUiMap(sheet) {
  applyBase(sheet, "A1:G16");
  styleTitle(sheet, "A1:G1", "页面与流程验收映射");
  sheet.getRange("A2:G2").values = [["本页把测试计划中的用户可见页面职责映射到测试用例，执行证据统一回填“测试项目”页。", null, null, null, null, null, null]];
  sheet.mergeCells("A2:G2");
  sheet.getRange("A2:G2").format = { fill: colors.blueLight, font: { name: font, size: 10, color: colors.muted }, wrapText: true, verticalAlignment: "center" };
  sheet.getRange("A4:G4").values = [["编号", "页面/流程", "验证点", "关联用例", "预期验收结果", "执行状态", "证据/备注"]];
  styleHeader(sheet.getRange("A4:G4"));
  const rows = [
    ["UI-01", "启动与健康检查", "服务状态、数据库连接、入口可访问性", "TP-001", "启动和 /health 状态明确，模型、知识库、聊天入口可进入。", "未执行", ""],
    ["UI-02", "模型设置页", "供应商、模型、参数、默认 LLM", "TP-002", "参数保存成功，敏感字段脱敏，默认模型可选且可生效。", "未执行", ""],
    ["UI-03", "知识库首页", "列表、新建、编辑、删除、搜索、可见性", "TP-003/TP-011", "仅展示可见对象，创建与维护入口可用，权限错误有提示。", "未执行", ""],
    ["UI-04", "知识库详情页", "目录、数据集、分段、增强、状态与重建", "TP-004~TP-006/TP-010", "导入、状态流转、增强和删除清理结果可查看。", "未执行", ""],
    ["UI-05", "聊天页", "知识库选择、对话、流式回答、引用、重生成", "TP-007", "答案与引用同时展示，消息和引用可追溯，失败可恢复。", "未执行", ""],
    ["UI-06", "搜索页", "关键词/自然语言搜索、来源、历史与跳转", "TP-008", "结果含来源，可跳转，历史可保存和删除，无结果反馈清晰。", "未执行", ""],
    ["UI-07", "文档集与运维", "文档版本、转数据集、日志和回归入口", "TP-009/TP-012", "版本可追溯，转数据集链路可用，回归结论有记录。", "未执行", ""],
  ];
  sheet.getRange("A5:G11").values = rows;
  styleBody(sheet.getRange("A5:G11"));
  sheet.getRange("A5:A11").format.horizontalAlignment = "center";
  sheet.getRange("D5:F11").format.horizontalAlignment = "center";
  sheet.getRange("F5:F11").format = { fill: colors.amber, font: { name: font, size: 9, bold: true, color: colors.ink }, horizontalAlignment: "center", verticalAlignment: "center", borders: { preset: "all", style: "thin", color: colors.border } };
  sheet.getRange("F5:F11").dataValidation = { rule: { type: "list", values: ["未执行", "通过", "失败", "阻塞", "不适用"] } };
  sheet.getRange("A5:G11").format.rowHeight = 54;
  setWidths(sheet, { A: 11, B: 20, C: 32, D: 18, E: 42, F: 11, G: 24 }, 16);
  sheet.freezePanes.freezeRows(4);
  const table = sheet.tables.add("A4:G11", true, "WenkbUiMapTable");
  table.style = "TableStyleMedium2";
}

function buildRunSummary(sheet) {
  applyBase(sheet, "A1:H34");
  styleTitle(sheet, "A1:H1", "测试执行汇总与缺陷记录");
  sheet.getRange("A3:B7").values = [
    ["测试对象", "第14小组 基于大模型的个人知识库系统"],
    ["测试基线", "docs/test_plan.md v0.1（2026-09-03）"],
    ["执行版本", "待填写"],
    ["执行环境", "Windows 本地；浏览器或 Tauri；关系型数据库；向量检索环境；可访问模型服务"],
    ["测试数据", "PDF、DOCX、MD、TXT、PPT；有效/无效 URL；单轮/多轮问题；无结果查询；异常模型配置"],
  ];
  sheet.getRange("A3:B7").format = { fill: colors.blueLight, font: { name: font, size: 10, color: colors.ink }, wrapText: true, verticalAlignment: "center", borders: { preset: "all", style: "thin", color: colors.border } };
  sheet.getRange("A3:A7").format.font = { name: font, size: 10, bold: true, color: colors.navy };
  sheet.getRange("A7:B7").format.rowHeight = 38;
  sheet.getRange("A9:B9").values = [["执行汇总", "数量"]];
  styleHeader(sheet.getRange("A9:B9"));
  const caseRange = `'测试项目'!I5:I${testCases.length + 4}`;
  sheet.getRange("A10:A18").values = [["用例总数"], ["通过"], ["失败"], ["阻塞"], ["未执行"], ["不适用"], ["已判定"], ["通过率"], ["未填写结论"]];
  sheet.getRange("B10:B18").formulas = [
    [`=COUNTA('测试项目'!A5:A${testCases.length + 4})`],
    [`=COUNTIFS(${caseRange},"通过")`],
    [`=COUNTIFS(${caseRange},"失败")`],
    [`=COUNTIFS(${caseRange},"阻塞")`],
    [`=COUNTIFS(${caseRange},"未执行")`],
    [`=COUNTIFS(${caseRange},"不适用")`],
    ["=B11+B12"],
    ["=IF(B16=0,\"待执行\",B11/B16)"],
    [`=COUNTBLANK(${caseRange})`],
  ];
  styleBody(sheet.getRange("A10:B18"));
  sheet.getRange("A10:A18").format.font = { name: font, size: 10, bold: true, color: colors.navy };
  sheet.getRange("B10:B18").format = { fill: colors.blueLight, font: { name: font, size: 11, bold: true, color: colors.ink }, horizontalAlignment: "center", verticalAlignment: "center", borders: { preset: "all", style: "thin", color: colors.border } };
  sheet.getRange("B17").format.numberFormat = "0%";
  sheet.getRange("B11").conditionalFormats.add("cellIs", { operator: "greaterThan", formula: 0, format: { fill: colors.green, font: { bold: true, color: "#375623" } } });
  sheet.getRange("B12").conditionalFormats.add("cellIs", { operator: "greaterThan", formula: 0, format: { fill: colors.red, font: { bold: true, color: "#9C0006" } } });
  for (const row of [13, 14]) sheet.getRange(`B${row}`).conditionalFormats.add("cellIs", { operator: "greaterThan", formula: 0, format: { fill: colors.amber, font: { bold: true, color: "#7F6000" } } });
  sheet.getRange("B18").conditionalFormats.add("cellIs", { operator: "greaterThan", formula: 0, format: { fill: colors.red, font: { bold: true, color: "#9C0006" } } });
  sheet.getRange("A19:B19").values = [["交付判定", ""]];
  sheet.getRange("B19").formulas = [["=IF(B12>0,\"不通过：存在失败用例\",IF(B13>0,\"阻塞：需处理阻塞用例\",IF(B18>0,\"未完成：存在未填结论\",IF(B14>0,\"未完成：请先执行全部用例\",IF(B15>0,\"未完成：存在不适用项待确认\",\"通过\")))))"]];
  sheet.getRange("A19:B19").format = { fill: colors.amber, font: { name: font, size: 10, bold: true, color: colors.ink }, wrapText: true, verticalAlignment: "center", borders: { preset: "all", style: "thin", color: colors.border } };
  sheet.getRange("A19").format.font = { name: font, size: 10, bold: true, color: colors.navy };
  sheet.getRange("B19").format.horizontalAlignment = "center";
  sheet.getRange("A21:H21").values = [["执行要求", null, null, null, null, null, null, null]];
  sheet.mergeCells("A21:H21");
  sheet.getRange("A21:H21").format = { fill: colors.navy, font: { name: font, size: 10, bold: true, color: colors.white }, verticalAlignment: "center" };
  sheet.getRange("A21:H25").values = [
    ["1", "每轮测试前填写执行版本、环境和数据基线。", null, null, null, null, null, null],
    ["2", "每条用例执行后填写实测结果、确定结果、日期、测试者和证据。", null, null, null, null, null, null],
    ["3", "失败或阻塞用例必须关联缺陷编号、日志或截图，并在回归后补充结论。", null, null, null, null, null, null],
    ["4", "删除与重建测试只使用可恢复测试数据，执行前后保留对象清单。", null, null, null, null, null, null],
    ["5", "交付门禁：核心用例全部通过，高优先级缺陷清零或获得明确延期批准。", null, null, null, null, null, null],
  ];
  for (let row = 22; row <= 26; row += 1) sheet.mergeCells(`B${row}:H${row}`);
  styleBody(sheet.getRange("A22:H26"));
  sheet.getRange("A22:A26").format = { fill: colors.blue, font: { name: font, size: 10, bold: true, color: colors.navy }, horizontalAlignment: "center", verticalAlignment: "center", borders: { preset: "all", style: "thin", color: colors.border } };
  sheet.getRange("A22:H26").format.rowHeight = 26;
  sheet.getRange("A29:G29").values = [["缺陷编号", "关联用例", "严重级别", "问题描述", "处理结论", "责任人", "关闭日期"]];
  styleHeader(sheet.getRange("A29:G29"));
  sheet.getRange("A30:G34").values = Array.from({ length: 5 }, () => ["", "", "", "", "", "", null]);
  styleBody(sheet.getRange("A30:G34"));
  sheet.getRange("C30:C34").dataValidation = { rule: { type: "list", values: ["高", "中", "低"] } };
  sheet.getRange("G30:G34").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("A30:G34").format.rowHeight = 25;
  setWidths(sheet, { A: 18, B: 56, C: 15, D: 38, E: 28, F: 14, G: 14, H: 14 }, 34);
  sheet.freezePanes.freezeRows(9);
  const table = sheet.tables.add("A29:G34", true, "WenkbDefectTable");
  table.style = "TableStyleMedium2";
}

const workbook = Workbook.create();
const cover = workbook.worksheets.add("文件封面");
const tests = workbook.worksheets.add("测试项目");
const ui = workbook.worksheets.add("UI界面");
const run = workbook.worksheets.add("运行");

buildCover(cover);
buildTestCases(tests);
buildUiMap(ui);
buildRunSummary(run);

workbook.recalculate();

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
for (const sheet of [cover, tests, ui, run]) {
  const preview = await workbook.render({ sheetName: sheet.name, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheet.name}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
if (!formulaErrors.ndjson.includes('"matched":0') && !formulaErrors.ndjson.includes("Cell search matched 0 entries")) {
  throw new Error(`Formula error scan failed: ${formulaErrors.ndjson}`);
}

const summary = await workbook.inspect({
  kind: "table",
  sheetId: "运行",
  range: "A9:B17",
  include: "values,formulas",
  tableMaxRows: 12,
  tableMaxCols: 4,
  maxChars: 4000,
});
console.log(summary.ndjson);

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(`Saved ${outputPath}`);
