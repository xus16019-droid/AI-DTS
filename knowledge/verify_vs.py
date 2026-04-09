import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from tools.rule_parser import RuleParser
from knowledge.vector_store import VectorStore


def verify_vector_store():
    print("\n" + "=" * 70)
    print("向量数据库验证报告")
    print("=" * 70)
    
    print("\n" + "-" * 70)
    print("第一部分：规则解析结果验证")
    print("-" * 70)
    
    parser = RuleParser()
    rules = parser.parse_directory(str(settings.DATA_DIR))
    
    print(f"\n[1.1] 规则总数: {len(rules)} 条")
    
    print("\n" + "-" * 70)
    print("第二部分：ChromaDB向量库数据验证")
    print("-" * 70)
    
    vs = VectorStore()
    vs.connect()
    vs.create_collection()
    
    stats = vs.get_statistics()
    print(f"\n[2.1] 向量库统计:")
    print(f"    集合名称: {stats['collection_name']}")
    print(f"    规则数量: {stats['total_rules']}")
    
    print(f"\n[2.2] 向量库中的规则列表:")
    all_rules = vs.get_all_rules()
    for r in all_rules:
        print(f"    - {r['rule_id']}")
        print(f"      规则组: {r['metadata'].get('rule_group', 'N/A')}")
        print(f"      方案: {r['metadata'].get('solution', 'N/A')[:50]}...")
    
    print("\n" + "-" * 70)
    print("第三部分：语义检索功能测试")
    print("-" * 70)
    
    test_cases = [
        {
            "name": "测试1: 精确匹配 - 监理公司GBB, 偏心量<=5mm",
            "query": "监理公司GBB 偏心量小于等于5mm",
            "expected": "序号1-4规则组_规则1"
        },
        {
            "name": "测试2: 精确匹配 - 监理公司非GBB, 偏心量>18mm",
            "query": "监理公司不是GBB 偏心量大于18mm",
            "expected": "序号1-4规则组_规则5"
        },
        {
            "name": "测试3: 精确匹配 - 序号5-8, 偏心量>5mm",
            "query": "序号5到8 偏心量大于5mm",
            "expected": "序号5-8规则组_规则2"
        },
        {
            "name": "测试4: 模糊匹配 - 铰点型号1#",
            "query": "铰点型号1# 偏心量",
            "expected": "序号1-4规则组_规则3"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for tc in test_cases:
        print(f"\n{tc['name']}")
        print(f"    查询: \"{tc['query']}\"")
        results = vs.search(tc['query'], n_results=1)
        
        if results:
            top_result = results[0]
            print(f"    最相似规则: {top_result['rule_id']}")
            print(f"    相似度距离: {top_result['distance']:.4f}")
            print(f"    期望规则: {tc['expected']}")
            
            if top_result['rule_id'] == tc['expected']:
                print(f"    结果: [OK] 匹配正确")
                passed += 1
            else:
                print(f"    结果: [WARNING] 匹配不同（可能是语义相似）")
        else:
            print(f"    结果: [ERROR] 未找到结果")
    
    print("\n" + "-" * 70)
    print("第四部分：数据一致性检查")
    print("-" * 70)
    
    print(f"\n[4.1] 规则数量对比:")
    print(f"    解析规则数: {len(rules)}")
    print(f"    向量库规则数: {stats['total_rules']}")
    if len(rules) == stats['total_rules']:
        print("    [OK] 数量一致")
    else:
        print("    [ERROR] 数量不一致!")
    
    print(f"\n[4.2] 规则ID对比:")
    parsed_ids = set(r.rule_id for r in rules)
    vector_ids = set(r['rule_id'] for r in all_rules)
    
    missing = parsed_ids - vector_ids
    extra = vector_ids - parsed_ids
    
    if missing:
        print(f"    [WARNING] 向量库中缺少的规则: {missing}")
    if extra:
        print(f"    [WARNING] 向量库中多余的规则: {extra}")
    if not missing and not extra:
        print("    [OK] 所有规则ID一致")
    
    print("\n" + "-" * 70)
    print("第五部分：检索测试汇总")
    print("-" * 70)
    print(f"\n    精确匹配测试: {passed}/{total} 通过")
    
    print("\n" + "=" * 70)
    print("验证完成!")
    print("=" * 70)


if __name__ == "__main__":
    verify_vector_store()
