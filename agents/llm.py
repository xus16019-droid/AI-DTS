import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Optional, List, Dict, Any
from zhipuai import ZhipuAI
from config import settings


class GLMLLM:
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GLM_API_KEY
        self.model = model or settings.GLM_MODEL
        self.client = None
        
        if self.api_key and self.api_key != "your_glm_api_key_here":
            self.client = ZhipuAI(api_key=self.api_key)
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        if not self.is_available():
            return "[ERROR] GLM API Key 未配置，请检查 .env 文件中的 GLM_API_KEY"
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[ERROR] GLM API 调用失败: {str(e)}"
    
    def generate_solution(
        self,
        rule_info: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> str:
        system_prompt = """你是一个制造偏差处理专家。根据提供的规则信息和输入数据，生成详细、专业的处理方案。

要求：
1. 方案要具体、可操作
2. 如果规则已有明确方案，直接使用
3. 如果规则方案为"待提供"，根据相似规则和经验给出建议方案
4. 方案要包含处理步骤和注意事项"""

        prompt = f"""请根据以下信息生成处理方案：

【规则信息】
规则ID: {rule_info.get('rule_id', 'N/A')}
规则条件: {rule_info.get('conditions', 'N/A')}
原方案: {rule_info.get('solution', 'N/A')}

【输入数据】
监理公司: {input_data.get('supervisor', 'N/A')}
偏心量: {input_data.get('deviation', 'N/A')} mm
铰点型号: {input_data.get('hinge_type', 'N/A')}

请生成详细的处理方案："""

        return self.chat(prompt, system_prompt=system_prompt)


if __name__ == "__main__":
    llm = GLMLLM()
    
    if llm.is_available():
        print("[OK] GLM LLM 初始化成功")
        
        response = llm.chat("你好，请简单介绍一下你自己。")
        print(f"回复: {response}")
    else:
        print("[WARNING] GLM API Key 未配置")
