import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from agents.agents import (
    AgentState,
    DataParserAgent,
    RuleRetrievalAgent,
    SolutionGeneratorAgent,
    HumanLoopAgent,
    DocLayoutAgent
)


class AgentOrchestrator:
    
    def __init__(self):
        self.name = "AgentOrchestrator"
        self.data_parser = DataParserAgent()
        self.rule_retriever = RuleRetrievalAgent()
        self.solution_generator = SolutionGeneratorAgent()
        self.human_loop = HumanLoopAgent()
        self.doc_layout = DocLayoutAgent()
        
        self.graph = None
        self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("data_parser", self.data_parser.process)
        workflow.add_node("rule_retriever", self.rule_retriever.process)
        workflow.add_node("solution_generator", self.solution_generator.process)
        workflow.add_node("human_loop", self.human_loop.process)
        workflow.add_node("doc_layout", self.doc_layout.process)
        
        workflow.set_entry_point("data_parser")
        
        workflow.add_edge("data_parser", "rule_retriever")
        workflow.add_edge("rule_retriever", "solution_generator")
        workflow.add_edge("solution_generator", "human_loop")
        workflow.add_edge("human_loop", "doc_layout")
        workflow.add_edge("doc_layout", END)
        
        self.graph = workflow.compile()
        
        print(f"[{self.name}] 工作流构建完成")
    
    def run(self, input_data: Dict[str, Any]) -> AgentState:
        print("\n" + "=" * 60)
        print("AI-DTS 多智能体系统启动")
        print("=" * 60)
        
        initial_state: AgentState = {
            "input_data": input_data,
            "parsed_data": None,
            "matched_rules": None,
            "vector_results": None,
            "solution": None,
            "final_solution": None,
            "document_path": None,
            "error": None,
            "status": "init"
        }
        
        final_state = self.graph.invoke(initial_state)
        
        print("\n" + "=" * 60)
        print("AI-DTS 多智能体系统执行完成")
        print("=" * 60)
        
        return final_state
    
    def get_graph_visualization(self):
        try:
            from IPython.display import Image, display
            return Image(self.graph.get_graph().draw_mermaid_png())
        except Exception:
            mermaid_code = """
graph LR
    A[输入数据] --> B[数据解析Agent]
    B --> C[规则检索Agent]
    C --> D[方案生成Agent]
    D --> E[人机协同Agent]
    E --> F[文档排版Agent]
    F --> G[输出报告]
"""
            return mermaid_code


def run_workflow(input_data: Dict[str, Any]) -> Dict[str, Any]:
    orchestrator = AgentOrchestrator()
    result = orchestrator.run(input_data)
    return result


if __name__ == "__main__":
    test_cases = [
        {
            "name": "测试1: GBB监理公司, 偏心量<=5mm",
            "data": {
                "supervisor": "GBB",
                "sequence_1": 3.0,
                "sequence_2": 4.0,
                "hinge_type": "1#铰点"
            }
        },
        {
            "name": "测试2: 非GBB监理公司, 偏心量>18mm",
            "data": {
                "supervisor": "OTHER",
                "sequence_1": 15.0,
                "sequence_2": 12.0,
                "hinge_type": "1#铰点"
            }
        },
        {
            "name": "测试3: 序号5-8, 偏心量>5mm",
            "data": {
                "supervisor": "GBB",
                "sequence_5": 4.0,
                "sequence_6": 5.0
            }
        }
    ]
    
    for tc in test_cases:
        print(f"\n\n{'#'*60}")
        print(f"# {tc['name']}")
        print(f"{'#'*60}")
        
        result = run_workflow(tc["data"])
        
        print(f"\n执行状态: {result.get('status', 'N/A')}")
        if result.get("error"):
            print(f"错误信息: {result.get('error')}")
