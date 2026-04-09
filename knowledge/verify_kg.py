import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neo4j import GraphDatabase
from config import settings
from tools.rule_parser import RuleParser


def verify_knowledge_graph():
    print("\n" + "=" * 70)
    print("知识图谱验证报告")
    print("=" * 70)
    
    print("\n" + "-" * 70)
    print("第一部分：规则解析结果验证")
    print("-" * 70)
    
    parser = RuleParser()
    rules = parser.parse_directory(str(settings.DATA_DIR))
    
    print(f"\n[1.1] 规则总数: {len(rules)} 条")
    
    rule_groups = {}
    for rule in rules:
        if rule.rule_group not in rule_groups:
            rule_groups[rule.rule_group] = []
        rule_groups[rule.rule_group].append(rule)
    
    print(f"\n[1.2] 规则组分布:")
    for group_name, group_rules in rule_groups.items():
        print(f"    {group_name}: {len(group_rules)} 条规则")
        for rule in group_rules:
            print(f"      - {rule.rule_id}")
            print(f"        条件数: {len(rule.conditions)}")
            for c in rule.conditions:
                print(f"          * {c.condition_type}: {c.description}")
            print(f"        方案: {rule.solution[:60]}..." if len(rule.solution) > 60 else f"        方案: {rule.solution}")
    
    print("\n" + "-" * 70)
    print("第二部分：Neo4j知识图谱数据验证")
    print("-" * 70)
    
    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )
    
    with driver.session() as session:
        print("\n[2.1] 规则组节点:")
        result = session.run("MATCH (rg:RuleGroup) RETURN rg.name AS name ORDER BY name")
        rule_groups_in_db = [r['name'] for r in result]
        for rg in rule_groups_in_db:
            print(f"    - {rg}")
        
        print("\n[2.2] 规则节点详情:")
        result = session.run("""
            MATCH (r:Rule)-[:BELONGS_TO]->(rg:RuleGroup)
            RETURN r.rule_id AS rule_id, r.solution AS solution, rg.name AS rule_group
            ORDER BY r.rule_id
        """)
        rules_in_db = list(result)
        print(f"    规则总数: {len(rules_in_db)} 条")
        
        for r in rules_in_db:
            print(f"\n    [{r['rule_id']}]")
            print(f"      所属规则组: {r['rule_group']}")
            print(f"      方案: {r['solution'][:50]}..." if len(r['solution']) > 50 else f"      方案: {r['solution']}")
            
            cond_result = session.run("""
                MATCH (rule:Rule {rule_id: $rule_id})-[:HAS_CONDITION]->(c)
                RETURN labels(c)[0] AS type, c.description AS description
            """, rule_id=r['rule_id'])
            
            conditions = list(cond_result)
            print(f"      条件数: {len(conditions)}")
            for c in conditions:
                print(f"        - [{c['type']}] {c['description']}")
        
        print("\n[2.3] 条件节点统计:")
        condition_types = ['SupervisorCondition', 'DeviationCondition', 'HingeCondition', 'SequenceCondition']
        for cond_type in condition_types:
            result = session.run(f"MATCH (c:{cond_type}) RETURN count(c) AS count")
            count = result.single()['count']
            print(f"    {cond_type}: {count} 个")
        
        print("\n[2.4] 关系统计:")
        result = session.run("MATCH ()-[r:BELONGS_TO]->() RETURN count(r) AS count")
        print(f"    BELONGS_TO 关系: {result.single()['count']} 条")
        
        result = session.run("MATCH ()-[r:HAS_CONDITION]->() RETURN count(r) AS count")
        print(f"    HAS_CONDITION 关系: {result.single()['count']} 条")
    
    driver.close()
    
    print("\n" + "-" * 70)
    print("第三部分：数据一致性检查")
    print("-" * 70)
    
    print(f"\n[3.1] 规则数量对比:")
    print(f"    解析规则数: {len(rules)}")
    print(f"    图谱规则数: {len(rules_in_db)}")
    if len(rules) == len(rules_in_db):
        print("    [OK] 数量一致")
    else:
        print("    [ERROR] 数量不一致!")
    
    print(f"\n[3.2] 规则组数量对比:")
    print(f"    解析规则组数: {len(rule_groups)}")
    print(f"    图谱规则组数: {len(rule_groups_in_db)}")
    if len(rule_groups) == len(rule_groups_in_db):
        print("    [OK] 数量一致")
    else:
        print("    [ERROR] 数量不一致!")
    
    print(f"\n[3.3] 规则ID对比:")
    parsed_ids = set(r.rule_id for r in rules)
    db_ids = set(r['rule_id'] for r in rules_in_db)
    
    missing_in_db = parsed_ids - db_ids
    extra_in_db = db_ids - parsed_ids
    
    if missing_in_db:
        print(f"    [WARNING] 图谱中缺少的规则: {missing_in_db}")
    if extra_in_db:
        print(f"    [WARNING] 图谱中多余的规则: {extra_in_db}")
    if not missing_in_db and not extra_in_db:
        print("    [OK] 所有规则ID一致")
    
    print("\n" + "=" * 70)
    print("验证完成!")
    print("=" * 70)


if __name__ == "__main__":
    verify_knowledge_graph()
