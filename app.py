"""
AI-DTS: 制造偏差处理方案自动生成系统
主应用入口
"""

from config import settings
from tools.rule_parser import RuleParser


def main():
    print("=" * 60)
    print("AI-DTS 制造偏差处理方案自动生成系统")
    print("=" * 60)
    
    print("\n[1] 加载规则数据...")
    parser = RuleParser()
    rules = parser.parse_directory(str(settings.DATA_DIR))
    print(f"    成功加载 {len(rules)} 条规则")
    
    for rule in rules:
        print(f"\n    - {rule.rule_id} ({rule.rule_group})")
        for c in rule.conditions:
            print(f"      条件: {c.description}")
        print(f"      方案: {rule.solution[:50]}..." if len(rule.solution) > 50 else f"      方案: {rule.solution}")
    
    print("\n[2] 检查配置...")
    if settings.GLM_API_KEY:
        print("    [OK] GLM API Key 已配置")
    else:
        print("    [!!] GLM API Key 未配置，请检查 .env 文件")
    
    print("\n[3] 系统初始化完成，等待后续开发...")
    print("=" * 60)


if __name__ == "__main__":
    main()
