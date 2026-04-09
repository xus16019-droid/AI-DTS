import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Dict, Any, TypedDict, Optional, List
from dataclasses import dataclass, field

from tools.calculations import parse_input_data, pythagorean_calculation, determine_deviation_range
from knowledge.knowledge_graph import KnowledgeGraph
from knowledge.vector_store import VectorStore
from agents.llm import GLMLLM


class AgentState(TypedDict):
    input_data: Dict[str, Any]
    parsed_data: Optional[Dict[str, Any]]
    matched_rules: Optional[List[Dict[str, Any]]]
    vector_results: Optional[List[Dict[str, Any]]]
    solution: Optional[str]
    final_solution: Optional[str]
    document_path: Optional[str]
    error: Optional[str]
    status: str


class DataParserAgent:
    
    def __init__(self):
        self.name = "DataParserAgent"
        self.description = "数据解析与计算智能体"
    
    def process(self, state: AgentState) -> AgentState:
        print(f"\n[{self.name}] 开始处理数据...")
        
        try:
            input_data = state["input_data"]
            parsed_data = parse_input_data(input_data)
            
            print(f"  - 监理公司: {parsed_data.get('supervisor', 'N/A')}")
            print(f"  - 铰点型号: {parsed_data.get('hinge_type', 'N/A')}")
            
            if "deviation_1_4" in parsed_data:
                print(f"  - 序号1-4偏心量: {parsed_data['deviation_1_4']}mm ({parsed_data['deviation_1_4_range']})")
            
            if "deviation_5_8" in parsed_data:
                print(f"  - 序号5-8偏心量: {parsed_data['deviation_5_8']}mm ({parsed_data['deviation_5_8_range']})")
            
            state["parsed_data"] = parsed_data
            state["status"] = "parsed"
            
            print(f"[{self.name}] 数据解析完成")
            
        except Exception as e:
            state["error"] = f"数据解析错误: {str(e)}"
            state["status"] = "error"
            print(f"[{self.name}] 错误: {e}")
        
        return state


class RuleRetrievalAgent:
    
    def __init__(self):
        self.name = "RuleRetrievalAgent"
        self.description = "知识与规则检索智能体"
        self.kg = None
        self.vs = None
    
    def _init_connections(self):
        if self.kg is None:
            self.kg = KnowledgeGraph()
            self.kg.connect()
        
        if self.vs is None:
            self.vs = VectorStore()
            self.vs.connect()
            self.vs.create_collection()
    
    def process(self, state: AgentState) -> AgentState:
        print(f"\n[{self.name}] 开始检索规则...")
        
        try:
            self._init_connections()
            
            parsed_data = state["parsed_data"]
            matched_rules = []
            
            supervisor = parsed_data.get("supervisor", "")
            hinge_type = parsed_data.get("hinge_type", "")
            
            if "deviation_1_4" in parsed_data:
                deviation = parsed_data["deviation_1_4"]
                
                kg_rules = self.kg.find_matching_rules(
                    supervisor=supervisor,
                    deviation=deviation,
                    hinge_type=hinge_type,
                    sequence_group="序号1-4"
                )
                
                for rule in kg_rules:
                    rule["sequence_group"] = "序号1-4"
                    matched_rules.append(rule)
                
                print(f"  - 序号1-4知识图谱匹配: {len(kg_rules)} 条规则")
            
            if "deviation_5_8" in parsed_data:
                deviation = parsed_data["deviation_5_8"]
                
                kg_rules = self.kg.find_matching_rules(
                    supervisor=supervisor,
                    deviation=deviation,
                    hinge_type=hinge_type,
                    sequence_group="序号5-8"
                )
                
                for rule in kg_rules:
                    rule["sequence_group"] = "序号5-8"
                    matched_rules.append(rule)
                
                print(f"  - 序号5-8知识图谱匹配: {len(kg_rules)} 条规则")
            
            vector_results = []
            
            if not matched_rules or any("待提供" in r.get("solution", "") for r in matched_rules):
                print(f"  - 规则不完整，启动向量检索...")
                
                query_parts = []
                if supervisor:
                    query_parts.append(f"监理公司{supervisor}")
                if "deviation_1_4" in parsed_data:
                    query_parts.append(f"偏心量{parsed_data['deviation_1_4']}mm")
                if hinge_type:
                    query_parts.append(f"铰点型号{hinge_type}")
                
                query = " ".join(query_parts)
                vector_results = self.vs.search(query, n_results=3)
                
                print(f"  - 向量检索结果: {len(vector_results)} 条相似规则")
            
            state["matched_rules"] = matched_rules
            state["vector_results"] = vector_results
            state["status"] = "retrieved"
            
            print(f"[{self.name}] 规则检索完成")
            
        except Exception as e:
            state["error"] = f"规则检索错误: {str(e)}"
            state["status"] = "error"
            print(f"[{self.name}] 错误: {e}")
        
        return state


class SolutionGeneratorAgent:
    
    def __init__(self):
        self.name = "SolutionGeneratorAgent"
        self.description = "方案生成与推理智能体"
        self.llm = GLMLLM()
    
    def process(self, state: AgentState) -> AgentState:
        print(f"\n[{self.name}] 开始生成方案...")
        
        try:
            parsed_data = state["parsed_data"]
            matched_rules = state.get("matched_rules", [])
            vector_results = state.get("vector_results", [])
            
            solutions = []
            
            for rule in matched_rules:
                solution_text = rule.get("solution", "")
                
                if "待提供" in solution_text:
                    print(f"  - 规则 {rule.get('rule_id')} 方案待补充，使用LLM推理...")
                    
                    if self.llm.is_available():
                        llm_solution = self.llm.generate_solution(rule, parsed_data)
                        solutions.append({
                            "rule_id": rule.get("rule_id"),
                            "sequence_group": rule.get("sequence_group"),
                            "solution": llm_solution,
                            "source": "LLM推理",
                            "confidence": "中"
                        })
                    else:
                        similar_text = ""
                        if vector_results:
                            similar_text = f"\n相似规则参考: {vector_results[0].get('metadata', {}).get('solution', 'N/A')}"
                        
                        solutions.append({
                            "rule_id": rule.get("rule_id"),
                            "sequence_group": rule.get("sequence_group"),
                            "solution": f"[待人工确认] {solution_text}{similar_text}",
                            "source": "待补充",
                            "confidence": "低"
                        })
                else:
                    solutions.append({
                        "rule_id": rule.get("rule_id"),
                        "sequence_group": rule.get("sequence_group"),
                        "solution": solution_text,
                        "source": "知识图谱",
                        "confidence": "高"
                    })
            
            if not solutions and vector_results:
                print(f"  - 无精确匹配规则，使用向量检索结果...")
                for vr in vector_results[:1]:
                    solutions.append({
                        "rule_id": vr.get("rule_id"),
                        "sequence_group": vr.get("metadata", {}).get("rule_group", ""),
                        "solution": vr.get("metadata", {}).get("solution", ""),
                        "source": "向量检索",
                        "confidence": "中"
                    })
            
            if not solutions:
                solutions.append({
                    "rule_id": "无匹配",
                    "sequence_group": "N/A",
                    "solution": "未找到匹配规则，请人工审核处理",
                    "source": "默认",
                    "confidence": "低"
                })
            
            for i, sol in enumerate(solutions, 1):
                print(f"  - 方案{i}: [{sol['source']}] {sol['solution'][:50]}...")
            
            state["solution"] = solutions
            state["status"] = "generated"
            
            print(f"[{self.name}] 方案生成完成")
            
        except Exception as e:
            state["error"] = f"方案生成错误: {str(e)}"
            state["status"] = "error"
            print(f"[{self.name}] 错误: {e}")
        
        return state


class HumanLoopAgent:
    
    def __init__(self):
        self.name = "HumanLoopAgent"
        self.description = "人机协同与进化智能体"
    
    def process(self, state: AgentState) -> AgentState:
        print(f"\n[{self.name}] 等待人工确认...")
        
        try:
            solutions = state.get("solution", [])
            
            print("\n  " + "=" * 50)
            print("  处理方案预览")
            print("  " + "=" * 50)
            
            for i, sol in enumerate(solutions, 1):
                print(f"\n  【方案 {i}】")
                print(f"  规则ID: {sol.get('rule_id', 'N/A')}")
                print(f"  序号组: {sol.get('sequence_group', 'N/A')}")
                print(f"  来源: {sol.get('source', 'N/A')}")
                print(f"  置信度: {sol.get('confidence', 'N/A')}")
                print(f"  方案内容:")
                print(f"  {sol.get('solution', 'N/A')}")
            
            print("\n  " + "=" * 50)
            
            state["final_solution"] = solutions
            state["status"] = "confirmed"
            
            print(f"[{self.name}] 方案已确认")
            
        except Exception as e:
            state["error"] = f"人机协同错误: {str(e)}"
            state["status"] = "error"
            print(f"[{self.name}] 错误: {e}")
        
        return state


class DocLayoutAgent:
    
    def __init__(self):
        self.name = "DocLayoutAgent"
        self.description = "格式化排版智能体"
    
    def process(self, state: AgentState) -> AgentState:
        print(f"\n[{self.name}] 生成处理报告...")
        
        try:
            parsed_data = state.get("parsed_data", {})
            solutions = state.get("final_solution", [])
            
            report_lines = []
            report_lines.append("=" * 60)
            report_lines.append("制造偏差处理方案报告")
            report_lines.append("=" * 60)
            
            report_lines.append("\n【输入数据】")
            report_lines.append(f"  监理公司: {parsed_data.get('supervisor', 'N/A')}")
            report_lines.append(f"  铰点型号: {parsed_data.get('hinge_type', 'N/A')}")
            
            if "deviation_1_4" in parsed_data:
                report_lines.append(f"  序号1-4偏心量: {parsed_data['deviation_1_4']}mm")
            
            if "deviation_5_8" in parsed_data:
                report_lines.append(f"  序号5-8偏心量: {parsed_data['deviation_5_8']}mm")
            
            report_lines.append("\n【处理方案】")
            
            for i, sol in enumerate(solutions, 1):
                report_lines.append(f"\n  方案 {i}:")
                report_lines.append(f"    规则ID: {sol.get('rule_id', 'N/A')}")
                report_lines.append(f"    来源: {sol.get('source', 'N/A')}")
                report_lines.append(f"    置信度: {sol.get('confidence', 'N/A')}")
                report_lines.append(f"    处理方案: {sol.get('solution', 'N/A')}")
            
            report_lines.append("\n" + "=" * 60)
            report_lines.append("报告生成完成")
            report_lines.append("=" * 60)
            
            report = "\n".join(report_lines)
            
            state["document_path"] = "output/report.txt"
            state["report"] = report
            state["status"] = "completed"
            
            print(f"[{self.name}] 报告生成完成")
            print(f"\n{report}")
            
        except Exception as e:
            state["error"] = f"文档生成错误: {str(e)}"
            state["status"] = "error"
            print(f"[{self.name}] 错误: {e}")
        
        return state


if __name__ == "__main__":
    print("智能体模块测试")
    
    test_input = {
        "supervisor": "GBB",
        "sequence_1": 3.0,
        "sequence_2": 4.0,
        "hinge_type": "1#铰点"
    }
    
    state: AgentState = {
        "input_data": test_input,
        "parsed_data": None,
        "matched_rules": None,
        "vector_results": None,
        "solution": None,
        "final_solution": None,
        "document_path": None,
        "error": None,
        "status": "init"
    }
    
    agent1 = DataParserAgent()
    agent2 = RuleRetrievalAgent()
    agent3 = SolutionGeneratorAgent()
    agent4 = HumanLoopAgent()
    agent5 = DocLayoutAgent()
    
    state = agent1.process(state)
    state = agent2.process(state)
    state = agent3.process(state)
    state = agent4.process(state)
    state = agent5.process(state)
    
    print(f"\n最终状态: {state['status']}")
