# AI-DTS 制造偏差处理方案自动生成系统
# Code Wiki 文档

## 1. 项目概览

AI-DTS (制造偏差处理方案自动生成系统) 是一个基于多智能体架构的工业智能化系统，用于自动分析制造过程中的尺寸偏差数据并生成标准化的处理方案。

### 1.1 核心功能

- **自动计算偏心量**：基于勾股定理计算零件偏差的偏心量
- **智能规则匹配**：结合知识图谱和向量检索技术匹配处理规则
- **方案自动生成**：利用大语言模型推理生成处理方案
- **标准化文档输出**：自动生成Word格式的处理方案报告
- **人机协同**：支持人工审核和确认处理方案

### 1.2 技术栈

| 技术类别 | 技术/库 | 版本 | 用途 |
|---------|---------|------|------|
| 大语言模型 | GLM-4 | - | 方案推理生成 |
| 多智能体框架 | LangGraph | ≥0.0.50 | 智能体协调与工作流管理 |
| 知识图谱 | Neo4j | ≥5.0.0 | 规则存储与精确匹配 |
| 向量数据库 | ChromaDB | ≥0.4.0 | 语义相似检索 |
| Web界面 | Gradio | ≥4.0.0 | 用户交互界面 |
| 文档生成 | python-docx | ≥1.0.0 | Word报告生成 |
| 配置管理 | python-dotenv | ≥1.0.0 | 环境变量管理 |

## 2. 项目结构

### 2.1 目录结构

```
/workspace/
├── agents/                    # 智能体模块
│   ├── __init__.py
│   ├── agents.py             # 五个核心智能体实现
│   ├── llm.py                # GLM大模型接口
│   └── orchestrator.py       # 多智能体协调器
├── config/                    # 配置模块
│   ├── .env.example          # 环境变量示例
│   ├── __init__.py
│   └── settings.py           # 系统配置
├── data/                      # 规则数据
│   ├── 序号1到4对应的规则.txt
│   └── 序号5到8对应的规则 .txt
├── knowledge/                 # 知识管理模块
│   ├── __init__.py
│   ├── knowledge_graph.py    # Neo4j知识图谱接口
│   ├── vector_store.py       # ChromaDB向量库接口
│   ├── verify_kg.py          # 知识图谱验证
│   └── verify_vs.py          # 向量库验证
├── tests/                     # 测试模块
│   └── test_e2e.py           # 端到端测试
├── tools/                     # 工具模块
│   ├── __init__.py
│   ├── calculations.py       # 偏心量计算工具
│   ├── doc_generator.py      # Word报告生成
│   └── rule_parser.py        # 规则解析器
├── app.py                     # 命令行入口
├── web_app.py                 # Web界面入口
├── requirements.txt           # 依赖清单
└── README.md                  # 项目说明文档
```

### 2.2 模块职责表

| 模块 | 主要职责 | 文件位置 | 核心功能 |
|------|---------|---------|----------|
| 智能体协调器 | 管理多智能体工作流 | [agents/orchestrator.py](file:///workspace/agents/orchestrator.py) | 构建状态图、协调智能体执行 |
| 数据解析智能体 | 解析输入数据、计算偏心量 | [agents/agents.py](file:///workspace/agents/agents.py) | 数据验证、偏心量计算 |
| 规则检索智能体 | 从知识图谱和向量库检索规则 | [agents/agents.py](file:///workspace/agents/agents.py) | 规则匹配、语义检索 |
| 方案生成智能体 | 生成处理方案 | [agents/agents.py](file:///workspace/agents/agents.py) | LLM推理、方案合成 |
| 人机协同智能体 | 方案预览与确认 | [agents/agents.py](file:///workspace/agents/agents.py) | 方案展示、人工确认 |
| 文档排版智能体 | 生成处理报告 | [agents/agents.py](file:///workspace/agents/agents.py) | 报告生成、文档排版 |
| 知识图谱 | 规则存储与检索 | [knowledge/knowledge_graph.py](file:///workspace/knowledge/knowledge_graph.py) | 规则导入、精确匹配查询 |
| 向量存储 | 语义相似检索 | [knowledge/vector_store.py](file:///workspace/knowledge/vector_store.py) | 规则向量化、相似性搜索 |
| 规则解析器 | 解析规则文本 | [tools/rule_parser.py](file:///workspace/tools/rule_parser.py) | 规则提取、条件解析 |
| 计算工具 | 偏心量计算 | [tools/calculations.py](file:///workspace/tools/calculations.py) | 勾股定理计算、区间判断 |
| 文档生成器 | Word报告生成 | [tools/doc_generator.py](file:///workspace/tools/doc_generator.py) | 报告排版、文件输出 |
| Web界面 | 用户交互 | [web_app.py](file:///workspace/web_app.py) | 数据输入、结果展示、报告下载 |

## 3. 核心功能模块

### 3.1 多智能体系统

#### 3.1.1 智能体协调器 (AgentOrchestrator)

**功能**：基于LangGraph构建状态图，协调多个智能体按顺序执行任务。

**关键组件**：
- **状态定义**：`AgentState` 定义了工作流中的数据状态
- **节点添加**：将5个智能体作为节点添加到工作流中
- **边定义**：定义智能体执行顺序和状态流转

**状态流转**：
```
init → parsed → retrieved → generated → confirmed → completed
  │        │         │          │           │          │
  └────────┴─────────┴──────────┴───────────┴──────────┘
                          ↓
                        error (任一环节失败)
```

**使用示例**：
```python
# 运行工作流
from agents.orchestrator import run_workflow

input_data = {
    "supervisor": "GBB",
    "sequence_1": 3.0,
    "sequence_2": 4.0,
    "hinge_type": "1#铰点"
}

result = run_workflow(input_data)
print(f"执行状态: {result.get('status')}")
print(f"处理方案: {result.get('final_solution')}")
```

#### 3.1.2 数据解析智能体 (DataParserAgent)

**功能**：解析输入数据，执行勾股定理计算偏心量。

**核心方法**：
- `process()`：处理输入数据，计算偏心量
- 调用 `parse_input_data()` 解析原始输入
- 调用 `pythagorean_calculation()` 计算偏心量
- 调用 `determine_deviation_range()` 判断偏心量区间

#### 3.1.3 规则检索智能体 (RuleRetrievalAgent)

**功能**：从知识图谱和向量库中检索匹配的规则。

**核心方法**：
- `process()`：执行规则检索逻辑
- `_init_connections()`：初始化知识图谱和向量库连接
- 调用 `KnowledgeGraph.find_matching_rules()` 进行精确匹配
- 调用 `VectorStore.search()` 进行语义相似检索

**检索策略**：
1. 首先从知识图谱中进行精确规则匹配
2. 如果规则不完整（包含"待提供"），启动向量库语义检索
3. 综合两种检索结果

#### 3.1.4 方案生成智能体 (SolutionGeneratorAgent)

**功能**：基于匹配的规则和向量检索结果生成处理方案。

**核心方法**：
- `process()`：生成处理方案
- 对于完整规则：直接使用规则方案
- 对于不完整规则：使用LLM推理生成方案
- 对于无匹配规则：使用向量检索结果或默认方案

**置信度评估**：
- 高：来自知识图谱精确匹配
- 中：来自向量检索或LLM推理
- 低：无参考，需人工确认

#### 3.1.5 人机协同智能体 (HumanLoopAgent)

**功能**：展示处理方案，等待人工确认。

**核心方法**：
- `process()`：展示方案预览，记录人工确认结果

#### 3.1.6 文档排版智能体 (DocLayoutAgent)

**功能**：生成标准化的处理方案报告。

**核心方法**：
- `process()`：生成报告内容，保存为文件

### 3.2 知识管理模块

#### 3.2.1 知识图谱 (KnowledgeGraph)

**功能**：使用Neo4j存储和检索规则，支持精确匹配。

**节点类型**：
- RuleGroup：规则组
- Rule：规则
- SupervisorCondition：监理公司条件
- DeviationCondition：偏心量条件
- HingeCondition：铰点条件
- SequenceCondition：序号组条件

**关系类型**：
- BELONGS_TO：规则属于规则组
- HAS_CONDITION：规则包含条件

**核心方法**：
- `connect()`：连接Neo4j数据库
- `import_rules()`：导入规则到知识图谱
- `find_matching_rules()`：查询匹配的规则
- `get_statistics()`：获取知识图谱统计信息

#### 3.2.2 向量存储 (VectorStore)

**功能**：使用ChromaDB存储规则的向量表示，支持语义相似检索。

**核心方法**：
- `connect()`：连接ChromaDB
- `add_rules()`：添加规则到向量库
- `search()`：执行语义相似检索
- `search_by_conditions()`：基于条件执行检索

### 3.3 工具模块

#### 3.3.1 规则解析器 (RuleParser)

**功能**：解析规则文本文件，提取规则和条件。

**核心方法**：
- `parse_file()`：解析单个规则文件
- `parse_directory()`：解析目录中的所有规则文件
- `_parse_conditions()`：解析规则中的条件

#### 3.3.2 计算工具 (calculations)

**功能**：执行偏心量计算和区间判断。

**核心函数**：
- `pythagorean_calculation()`：勾股定理计算
- `determine_deviation_range()`：判断偏心量区间
- `parse_input_data()`：解析输入数据

#### 3.3.3 文档生成器 (doc_generator)

**功能**：生成Word格式的处理方案报告。

**核心函数**：
- `generate_report()`：生成并保存报告

### 3.4 Web界面

**功能**：提供用户友好的Web界面，支持数据输入和结果展示。

**核心组件**：
- `process_deviation()`：处理用户输入，执行工作流
- `create_interface()`：创建Gradio界面
- `launch_app()`：启动Web服务器

**界面功能**：
- 监理公司输入
- 序号数值输入（序号1-4或序号5-8）
- 铰点型号选择
- 处理方案展示
- Word报告下载

## 4. 核心API/类/函数

### 4.1 智能体相关

#### AgentOrchestrator 类

**功能**：多智能体协调器，管理工作流执行。

**主要方法**：
- `__init__()`：初始化智能体实例
- `_build_graph()`：构建LangGraph状态图
- `run()`：运行工作流
- `get_graph_visualization()`：获取工作流可视化

**参数**：无

**返回值**：
- `run()`：返回最终状态字典

#### DataParserAgent 类

**功能**：解析输入数据，计算偏心量。

**主要方法**：
- `process()`：处理输入数据，计算偏心量

**参数**：
- `state`：当前状态字典

**返回值**：更新后的状态字典

#### RuleRetrievalAgent 类

**功能**：从知识图谱和向量库检索规则。

**主要方法**：
- `_init_connections()`：初始化知识图谱和向量库连接
- `process()`：执行规则检索

**参数**：
- `state`：当前状态字典

**返回值**：更新后的状态字典

#### SolutionGeneratorAgent 类

**功能**：生成处理方案。

**主要方法**：
- `process()`：生成处理方案

**参数**：
- `state`：当前状态字典

**返回值**：更新后的状态字典

### 4.2 知识管理相关

#### KnowledgeGraph 类

**功能**：Neo4j知识图谱操作。

**主要方法**：
- `connect()`：连接Neo4j数据库
- `import_rules()`：导入规则到知识图谱
- `find_matching_rules()`：查询匹配的规则
- `get_statistics()`：获取知识图谱统计信息

**参数**：
- `find_matching_rules()`：supervisor, deviation, hinge_type, sequence_group

**返回值**：
- `find_matching_rules()`：匹配的规则列表
- `get_statistics()`：统计信息字典

#### VectorStore 类

**功能**：ChromaDB向量存储操作。

**主要方法**：
- `connect()`：连接ChromaDB
- `add_rules()`：添加规则到向量库
- `search()`：执行语义相似检索
- `search_by_conditions()`：基于条件执行检索

**参数**：
- `search()`：query, n_results, where
- `search_by_conditions()`：supervisor, deviation, hinge_type, sequence_group, n_results

**返回值**：
- 检索结果列表

### 4.3 工具相关

#### RuleParser 类

**功能**：解析规则文本文件。

**主要方法**：
- `parse_file()`：解析单个规则文件
- `parse_directory()`：解析目录中的所有规则文件
- `_parse_conditions()`：解析规则中的条件

**参数**：
- `parse_file()`：file_path, rule_group
- `parse_directory()`：dir_path

**返回值**：
- 规则对象列表

#### pythagorean_calculation 函数

**功能**：使用勾股定理计算偏心量。

**参数**：
- `side_a`：第一条边长度
- `side_b`：第二条边长度

**返回值**：
- 包含计算结果的字典

#### generate_report 函数

**功能**：生成处理方案报告。

**参数**：
- `input_data`：原始输入数据
- `parsed_data`：解析后的数据
- `solutions`：处理方案列表

**返回值**：
- 报告文件路径

## 5. 系统工作流程

### 5.1 完整工作流

1. **用户输入**：通过Web界面输入监理公司、序号数值、铰点型号
2. **数据解析**：DataParserAgent解析输入数据，计算偏心量
3. **规则检索**：RuleRetrievalAgent从知识图谱和向量库检索匹配规则
4. **方案生成**：SolutionGeneratorAgent基于匹配规则生成处理方案
5. **人机协同**：HumanLoopAgent展示方案，等待人工确认
6. **文档生成**：DocLayoutAgent生成标准化处理方案报告
7. **结果展示**：Web界面展示处理方案，提供报告下载

### 5.2 规则匹配流程

```
┌─────────────────────────────────────────────────────┐
│                  规则检索流程                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│   输入: parsed_data                                 │
│          │                                          │
│          ▼                                          │
│   ┌──────────────┐                                 │
│   │ 知识图谱检索  │ ──→ 精确匹配规则                │
│   │  (Neo4j)     │     (高置信度)                  │
│   └──────────────┘                                 │
│          │                                          │
│          ▼                                          │
│   ┌──────────────────────────────────┐             │
│   │ 规则是否完整？                    │             │
│   │ (是否包含"待提供"字样)            │             │
│   └──────────────────────────────────┘             │
│          │                                          │
│    ┌─────┴─────┐                                   │
│    ▼           ▼                                   │
│   完整       不完整                                  │
│    │           │                                    │
│    ▼           ▼                                    │
│  直接返回   ┌──────────────┐                        │
│            │ 向量库检索   │ ──→ 相似历史案例        │
│            │ (ChromaDB)   │     (中置信度)          │
│            └──────────────┘                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 6. 部署与运行

### 6.1 环境准备

1. **创建虚拟环境**：
   ```bash
   conda create -n ai-dts python=3.10
   conda activate ai-dts
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**：
   - 复制 `config/.env.example` 为 `config/.env`
   - 填写 GLM API Key 和 Neo4j 连接信息

### 6.2 启动方式

#### 6.2.1 命令行模式

```bash
python app.py
```

#### 6.2.2 Web界面模式

```bash
python web_app.py
```

访问地址：http://127.0.0.1:7860

### 6.3 知识图谱初始化

首次运行前，需要初始化知识图谱：

```bash
python knowledge/knowledge_graph.py
```

### 6.4 向量库初始化

首次运行前，需要初始化向量库：

```bash
python knowledge/vector_store.py
```

## 7. 测试验证

### 7.1 端到端测试

运行端到端测试：

```bash
python -m pytest tests/test_e2e.py -v
```

### 7.2 测试用例

| 用例ID | 输入数据 | 预期结果 | 置信度 |
|--------|---------|---------|--------|
| TC01 | GBB, 序号1=3, 序号2=4 | 规则1匹配：按图纸尺寸划线 | 高 |
| TC02 | OTHER, 序号1=6, 序号2=8 | 规则2匹配：按图纸尺寸划线 | 高 |
| TC03 | OTHER, 序号1=12, 序号2=10, 1#铰点 | 规则3匹配：查看后大梁报告 | 高 |
| TC04 | OTHER, 序号1=15, 序号2=12 | 规则5匹配：待提供方案 | 低 |
| TC05 | GBB, 序号1=4, 序号2=5 | 规则6匹配：待提供方案 | 低 |

## 8. 配置说明

### 8.1 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| GLM_API_KEY | GLM-4 API密钥 | - |
| GLM_MODEL | GLM模型名称 | glm-4 |
| NEO4J_URI | Neo4j连接URI | bolt://localhost:7687 |
| NEO4J_USER | Neo4j用户名 | neo4j |
| NEO4J_PASSWORD | Neo4j密码 | - |

### 8.2 配置文件

配置文件位于 `config/settings.py`，包含：
- 路径配置
- API配置
- 数据库配置

## 9. 故障排除

### 9.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|----------|
| 知识图谱连接失败 | Neo4j未启动或配置错误 | 检查Neo4j服务状态和配置 |
| GLM API调用失败 | API密钥错误或网络问题 | 检查API密钥和网络连接 |
| 规则匹配失败 | 输入数据格式错误 | 检查输入数据格式 |
| 向量库初始化失败 | ChromaDB权限问题 | 检查目录权限 |

### 9.2 日志与调试

- 系统运行时会输出详细日志
- 可通过 `print` 语句查看执行过程
- 可通过 `get_graph_visualization()` 查看工作流状态图

## 10. 未来扩展

### 10.1 功能扩展

- [ ] 完善规则5、规则6的处理方案
- [ ] 增加更多历史案例数据
- [ ] 优化向量检索的相似度算法
- [ ] 添加批量处理功能
- [ ] 实现知识图谱自动更新机制
- [ ] 添加用户反馈收集功能
- [ ] 支持多种文档模板
- [ ] 集成更多LLM模型选项

### 10.2 技术演进

```
Phase 1 (当前)          Phase 2               Phase 3
────────────────────────────────────────────────────────
基础功能实现      →    知识进化机制    →    模型微调优化
                                                              ↓
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ • 规则匹配   │      │ • 自动回写   │      │ • 领域微调   │
│ • LLM推理    │  →   │ • 反馈学习   │  →   │ • 精度提升   │
│ • 文档生成   │      │ • 规则扩展   │      │ • 性能优化   │
└──────────────┘      └──────────────┘      └──────────────┘
```

## 11. 总结

AI-DTS 制造偏差处理方案自动生成系统是一个结合了多智能体技术、知识图谱、向量检索和大语言模型的工业智能化解决方案。它通过自动化的方式处理制造过程中的尺寸偏差，减少了对人工经验的依赖，提高了处理效率和标准化程度。

系统的核心优势在于：

1. **多智能体协作**：通过分工明确的智能体协同工作，处理复杂的制造偏差问题
2. **知识管理**：结合知识图谱和向量检索，实现规则的精确匹配和相似案例的检索
3. **智能推理**：利用大语言模型处理复杂的规则推理和方案生成
4. **用户友好**：提供直观的Web界面，方便用户操作和结果查看
5. **可扩展性**：模块化设计使得系统易于扩展和维护

随着技术的不断发展，AI-DTS 系统将继续进化，为制造行业提供更加智能、高效的偏差处理解决方案。