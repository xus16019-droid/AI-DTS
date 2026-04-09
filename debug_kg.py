import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neo4j import GraphDatabase
from config import settings


def debug_query():
    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )
    
    with driver.session() as session:
        print("=" * 60)
        print("检查知识图谱中的条件数据")
        print("=" * 60)
        
        print("\n[1] 检查所有 DeviationCondition:")
        result = session.run("""
            MATCH (dc:DeviationCondition)
            RETURN dc.condition_id, dc.operator, dc.min_value, dc.max_value, dc.description
        """)
        for r in result:
            print(f"  {r['dc.condition_id']}: operator={r['dc.operator']}, min={r['dc.min_value']}, max={r['dc.max_value']}")
            print(f"    描述: {r['dc.description']}")
        
        print("\n[2] 测试查询: 监理公司=GBB, 偏心量=5.0")
        
        result = session.run("""
            MATCH (r:Rule)-[:HAS_CONDITION]->(sc:SupervisorCondition)
            WHERE (sc.operator = '=' AND sc.value = 'GBB')
            RETURN r.rule_id, sc.operator, sc.value
        """)
        print("  监理公司条件匹配:")
        for r in result:
            print(f"    {r['r.rule_id']}: {r['sc.operator']} {r['sc.value']}")
        
        result = session.run("""
            MATCH (r:Rule)-[:HAS_CONDITION]->(dc:DeviationCondition)
            WHERE (dc.operator = '<=' AND 5.0 <= dc.max_value)
            RETURN r.rule_id, dc.operator, dc.max_value
        """)
        print("  偏心量条件匹配 (<=):")
        for r in result:
            print(f"    {r['r.rule_id']}: {r['dc.operator']} {r['dc.max_value']}")
        
        print("\n[3] 完整查询测试:")
        result = session.run("""
            MATCH (r:Rule)-[:HAS_CONDITION]->(c)
            WITH r, collect(c) AS conditions
            WHERE EXISTS {
                MATCH (r)-[:HAS_CONDITION]->(sc:SupervisorCondition)
                WHERE (sc.operator = '=' AND sc.value = 'GBB')
            }
            AND EXISTS {
                MATCH (r)-[:HAS_CONDITION]->(dc:DeviationCondition)
                WHERE (dc.operator = '<=' AND 5.0 <= dc.max_value)
            }
            AND EXISTS {
                MATCH (r)-[:HAS_CONDITION]->(seq:SequenceCondition)
                WHERE seq.value = '序号1-4'
            }
            RETURN r.rule_id, r.solution
        """)
        print("  匹配结果:")
        for r in result:
            print(f"    {r['r.rule_id']}: {r['r.solution'][:50]}...")
        
        print("\n[4] 检查规则1的所有条件:")
        result = session.run("""
            MATCH (r:Rule {rule_id: '序号1-4规则组_规则1'})-[:HAS_CONDITION]->(c)
            RETURN labels(c)[0] as type, c
        """)
        for r in result:
            print(f"  [{r['type']}] {dict(r['c'])}")
    
    driver.close()


if __name__ == "__main__":
    debug_query()
