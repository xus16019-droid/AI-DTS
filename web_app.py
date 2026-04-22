import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr
from typing import Dict, Any, List, Tuple
from datetime import datetime

from agents.orchestrator import run_workflow, AgentOrchestrator
from tools.doc_generator import generate_report
from config import settings

# 全局状态存储
workflow_states = {}


def process_deviation(
    supervisor: str,
    sequence_1: float,
    sequence_2: float,
    sequence_3: float,
    sequence_4: float,
    sequence_5: float,
    sequence_6: float,
    sequence_7: float,
    sequence_8: float,
    hinge_type: str
) -> Tuple[str, str, str, str, bool, bool]:
    input_data = {
        "supervisor": supervisor.strip() if supervisor else "",
        "hinge_type": hinge_type.strip() if hinge_type else "",
    }
    
    if sequence_1 and sequence_2:
        input_data["sequence_1"] = sequence_1
        input_data["sequence_2"] = sequence_2
    elif sequence_3 and sequence_4:
        input_data["sequence_3"] = sequence_3
        input_data["sequence_4"] = sequence_4
    
    if sequence_5 and sequence_6:
        input_data["sequence_5"] = sequence_5
        input_data["sequence_6"] = sequence_6
    elif sequence_7 and sequence_8:
        input_data["sequence_7"] = sequence_7
        input_data["sequence_8"] = sequence_8
    
    result = run_workflow(input_data)
    
    if result.get("status") == "error":
        return f"处理失败: {result.get('error', '未知错误')}", "", "", "", False, False
    
    if result.get("status") == "awaiting_human_approval":
        # 生成唯一ID来跟踪这个工作流
        workflow_id = f"{datetime.now().timestamp()}"
        workflow_states[workflow_id] = result
        
        parsed_data = result.get("parsed_data", {})
        solutions = result.get("solutions_for_approval", [])
        
        report_text = "【输入数据】\n"
        report_text += f"监理公司: {parsed_data.get('supervisor', 'N/A')}\n"
        report_text += f"铰点型号: {parsed_data.get('hinge_type', 'N/A')}\n"
        
        if "deviation_1_4" in parsed_data:
            report_text += f"序号1-4偏心量: {parsed_data['deviation_1_4']} mm ({parsed_data.get('deviation_1_4_range', 'N/A')})\n"
        
        if "deviation_5_8" in parsed_data:
            report_text += f"序号5-8偏心量: {parsed_data['deviation_5_8']} mm ({parsed_data.get('deviation_5_8_range', 'N/A')})\n"
        
        report_text += "\n【处理方案】\n"
        
        for i, sol in enumerate(solutions, 1):
            report_text += f"\n方案 {i}:\n"
            report_text += f"  规则ID: {sol.get('rule_id', 'N/A')}\n"
            report_text += f"  数据来源: {sol.get('source', 'N/A')}\n"
            report_text += f"  置信度: {sol.get('confidence', 'N/A')}\n"
            report_text += f"  处理方案: {sol.get('solution', 'N/A')}\n"
        
        return report_text, "", f"需要人工审核", workflow_id, True, False
    
    # 处理完成的情况
    parsed_data = result.get("parsed_data", {})
    solutions = result.get("final_solution", [])
    
    report_text = "【输入数据】\n"
    report_text += f"监理公司: {parsed_data.get('supervisor', 'N/A')}\n"
    report_text += f"铰点型号: {parsed_data.get('hinge_type', 'N/A')}\n"
    
    if "deviation_1_4" in parsed_data:
        report_text += f"序号1-4偏心量: {parsed_data['deviation_1_4']} mm ({parsed_data.get('deviation_1_4_range', 'N/A')})\n"
    
    if "deviation_5_8" in parsed_data:
        report_text += f"序号5-8偏心量: {parsed_data['deviation_5_8']} mm ({parsed_data.get('deviation_5_8_range', 'N/A')})\n"
    
    report_text += "\n【处理方案】\n"
    
    for i, sol in enumerate(solutions, 1):
        report_text += f"\n方案 {i}:\n"
        report_text += f"  规则ID: {sol.get('rule_id', 'N/A')}\n"
        report_text += f"  数据来源: {sol.get('source', 'N/A')}\n"
        report_text += f"  置信度: {sol.get('confidence', 'N/A')}\n"
        report_text += f"  处理方案: {sol.get('solution', 'N/A')}\n"
    
    if result.get("human_comments"):
        report_text += f"\n【审核意见】\n{result.get('human_comments')}\n"
    
    doc_path = generate_report(input_data, parsed_data, solutions)
    
    return report_text, doc_path, f"处理完成！报告已保存至: {doc_path}", "", False, True


def approve_solution(workflow_id: str, comments: str) -> Tuple[str, str, str, bool, bool]:
    if workflow_id not in workflow_states:
        return "错误: 未找到对应的工作流", "", "", False, False
    
    state = workflow_states[workflow_id]
    solutions = state.get("solutions_for_approval", [])
    
    # 创建协调器并处理审核
    orchestrator = AgentOrchestrator()
    result = orchestrator.approve_solution(state, solutions, comments)
    
    if result.get("status") == "error":
        return f"审核处理失败: {result.get('error', '未知错误')}", "", "", False, False
    
    parsed_data = result.get("parsed_data", {})
    approved_solutions = result.get("final_solution", [])
    
    report_text = "【输入数据】\n"
    report_text += f"监理公司: {parsed_data.get('supervisor', 'N/A')}\n"
    report_text += f"铰点型号: {parsed_data.get('hinge_type', 'N/A')}\n"
    
    if "deviation_1_4" in parsed_data:
        report_text += f"序号1-4偏心量: {parsed_data['deviation_1_4']} mm ({parsed_data.get('deviation_1_4_range', 'N/A')})\n"
    
    if "deviation_5_8" in parsed_data:
        report_text += f"序号5-8偏心量: {parsed_data['deviation_5_8']} mm ({parsed_data.get('deviation_5_8_range', 'N/A')})\n"
    
    report_text += "\n【处理方案】\n"
    
    for i, sol in enumerate(approved_solutions, 1):
        report_text += f"\n方案 {i}:\n"
        report_text += f"  规则ID: {sol.get('rule_id', 'N/A')}\n"
        report_text += f"  数据来源: {sol.get('source', 'N/A')}\n"
        report_text += f"  置信度: {sol.get('confidence', 'N/A')}\n"
        report_text += f"  处理方案: {sol.get('solution', 'N/A')}\n"
    
    if result.get("human_comments"):
        report_text += f"\n【审核意见】\n{result.get('human_comments')}\n"
    
    input_data = state.get("input_data", {})
    doc_path = generate_report(input_data, parsed_data, approved_solutions)
    
    # 清理工作流状态
    del workflow_states[workflow_id]
    
    return report_text, doc_path, "审核完成！报告已生成", False, True


def create_interface():
    with gr.Blocks(title="AI-DTS 制造偏差处理方案自动生成系统") as demo:
        gr.Markdown("""
        # AI-DTS 制造偏差处理方案自动生成系统
        
        本系统基于知识图谱和大语言模型，自动分析制造偏差数据并生成处理方案。
        
        **使用说明**：
        1. 填写监理公司名称
        2. 填写序号数值（序号1-4或序号5-8，至少填写一组）
        3. 选择铰点型号（如有）
        4. 点击"生成处理方案"按钮
        5. 对于需要人工审核的方案，填写审核意见并点击"确认方案"
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 输入数据")
                
                supervisor = gr.Textbox(
                    label="监理公司",
                    placeholder="例如: GBB",
                    value="GBB"
                )
                
                gr.Markdown("**序号1-4数值**（填写序号1和2，或序号3和4）")
                with gr.Row():
                    sequence_1 = gr.Number(label="序号1", value=None)
                    sequence_2 = gr.Number(label="序号2", value=None)
                with gr.Row():
                    sequence_3 = gr.Number(label="序号3", value=None)
                    sequence_4 = gr.Number(label="序号4", value=None)
                
                gr.Markdown("**序号5-8数值**（填写序号5和6，或序号7和8）")
                with gr.Row():
                    sequence_5 = gr.Number(label="序号5", value=None)
                    sequence_6 = gr.Number(label="序号6", value=None)
                with gr.Row():
                    sequence_7 = gr.Number(label="序号7", value=None)
                    sequence_8 = gr.Number(label="序号8", value=None)
                
                hinge_type = gr.Dropdown(
                    label="铰点型号",
                    choices=["", "1#铰点", "2#铰点", "3#铰点"],
                    value=""
                )
                
                submit_btn = gr.Button("生成处理方案", variant="primary", size="lg")
            
            with gr.Column(scale=1):
                gr.Markdown("### 处理结果")
                
                status_output = gr.Textbox(label="状态", interactive=False)
                
                report_output = gr.Textbox(
                    label="处理方案报告",
                    lines=15,
                    interactive=False
                )
                
                doc_output = gr.File(label="下载Word报告", visible=True)
                
                # 人工审核部分
                workflow_id = gr.Textbox(label="工作流ID", visible=False)
                
                approval_section = gr.Column(visible=False)
                with approval_section:
                    gr.Markdown("### 人工审核")
                    comments = gr.Textbox(
                        label="审核意见",
                        placeholder="请输入审核意见（可选）",
                        lines=3
                    )
                    approve_btn = gr.Button("确认方案", variant="secondary", size="lg")
        
        # 创建状态管理函数
        def handle_process_deviation(*args):
            result = process_deviation(*args)
            report_text, doc_path, status, wf_id, approval_visible, doc_visible = result
            
            # 更新组件状态
            approval_section.visible = approval_visible
            doc_output.visible = doc_visible
            
            if doc_path:
                doc_output.value = doc_path
            
            return report_text, status, wf_id
        
        def handle_approve_solution(workflow_id, comments):
            result = approve_solution(workflow_id, comments)
            report_text, doc_path, status, approval_visible, doc_visible = result
            
            # 更新组件状态
            approval_section.visible = approval_visible
            doc_output.visible = doc_visible
            
            if doc_path:
                doc_output.value = doc_path
            
            return report_text, status
        
        submit_btn.click(
            fn=handle_process_deviation,
            inputs=[
                supervisor,
                sequence_1, sequence_2, sequence_3, sequence_4,
                sequence_5, sequence_6, sequence_7, sequence_8,
                hinge_type
            ],
            outputs=[report_output, status_output, workflow_id]
        )
        
        approve_btn.click(
            fn=handle_approve_solution,
            inputs=[workflow_id, comments],
            outputs=[report_output, status_output]
        )
        
        gr.Markdown("""
        ---
        **注意事项**：
        - 置信度为"高"的方案来自知识图谱精确匹配，可直接参考
        - 置信度为"中"的方案来自向量检索，建议人工审核
        - 置信度为"低"的方案需要人工确认
        
        **系统版本**: v1.0.0
        """)
    
    return demo


def launch_app():
    demo = create_interface()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    launch_app()
