import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.llm import GLMLLM
from config import settings

print("=" * 60)
print("GLM API 配置验证")
print("=" * 60)

print(f"\nAPI Key: {settings.GLM_API_KEY[:10]}..." if settings.GLM_API_KEY else "API Key: 未配置")
print(f"API Base: {settings.GLM_API_BASE}")
print(f"Model: {settings.GLM_MODEL}")

if settings.GLM_API_KEY and settings.GLM_API_KEY != "your_glm_api_key_here":
    print("\n正在测试API连接...")
    try:
        llm = GLMLLM()
        response = llm.chat("你好，请简单回复。")
        print(f"\n[成功] API连接正常")
        print(f"回复: {response[:100]}...")
    except Exception as e:
        print(f"\n[失败] API连接错误: {e}")
else:
    print("\n[警告] 请先在 .env 文件中配置 GLM_API_KEY")
