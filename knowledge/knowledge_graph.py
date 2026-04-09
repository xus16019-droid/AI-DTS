import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from config import settings
from tools.rule_parser import Rule, RuleParser


class KnowledgeGraph:
    
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.driver = None
    
    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            print(f"[OK] 成功连接到Neo4j: {self.uri}")
            return True
        except Exception as e:
            print(f"[ERROR] 连接Neo4j失败: {e}")
            return False
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("[OK] 数据库已清空")
    
    def create_indexes(self):
        with self.driver.session() as session:
            session.run("CREATE INDEX IF NOT EXISTS FOR (r:Rule) ON (r.rule_id)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (rg:RuleGroup) ON (rg.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Condition) ON (c.condition_id)")
            print("[OK] 索引创建完成")
    
    def create_rule_group(self, name: str, description: str = ""):
        with self.driver.session() as session:
            session.run(
                "MERGE (rg:RuleGroup {name: $name}) SET rg.description = $description",
                name=name,
                description=description
            )
    
    def create_rule(self, rule: Rule):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (rg:RuleGroup {name: $rule_group})
                CREATE (r:Rule {
                    rule_id: $rule_id,
                    solution: $solution,
                    raw_text: $raw_text
                })
                CREATE (r)-[:BELONGS_TO]->(rg)
                """,
                rule_group=rule.rule_group,
                rule_id=rule.rule_id,
                solution=rule.solution,
                raw_text=rule.raw_text
            )
            
            for i, condition in enumerate(rule.conditions):
                condition_id = f"{rule.rule_id}_cond_{i}"
                
                if condition.condition_type == "supervisor":
                    session.run(
                        """
                        MATCH (r:Rule {rule_id: $rule_id})
                        CREATE (c:SupervisorCondition {
                            condition_id: $condition_id,
                            operator: $operator,
                            value: $value,
                            description: $description
                        })
                        CREATE (r)-[:HAS_CONDITION]->(c)
                        """,
                        rule_id=rule.rule_id,
                        condition_id=condition_id,
                        operator=condition.operator,
                        value=condition.value,
                        description=condition.description
                    )
                
                elif condition.condition_type == "deviation":
                    min_val = condition.value[0] if condition.operator == "range" else condition.value
                    max_val = condition.value[1] if condition.operator == "range" else condition.value
                    
                    session.run(
                        """
                        MATCH (r:Rule {rule_id: $rule_id})
                        CREATE (c:DeviationCondition {
                            condition_id: $condition_id,
                            operator: $operator,
                            min_value: $min_value,
                            max_value: $max_value,
                            description: $description
                        })
                        CREATE (r)-[:HAS_CONDITION]->(c)
                        """,
                        rule_id=rule.rule_id,
                        condition_id=condition_id,
                        operator=condition.operator,
                        min_value=float(min_val) if isinstance(min_val, (int, float)) else 0,
                        max_value=float(max_val) if isinstance(max_val, (int, float)) else 0,
                        description=condition.description
                    )
                
                elif condition.condition_type == "hinge_type":
                    session.run(
                        """
                        MATCH (r:Rule {rule_id: $rule_id})
                        CREATE (c:HingeCondition {
                            condition_id: $condition_id,
                            operator: $operator,
                            value: $value,
                            description: $description
                        })
                        CREATE (r)-[:HAS_CONDITION]->(c)
                        """,
                        rule_id=rule.rule_id,
                        condition_id=condition_id,
                        operator=condition.operator,
                        value=condition.value,
                        description=condition.description
                    )
                
                elif condition.condition_type == "sequence_group":
                    session.run(
                        """
                        MATCH (r:Rule {rule_id: $rule_id})
                        CREATE (c:SequenceCondition {
                            condition_id: $condition_id,
                            value: $value,
                            description: $description
                        })
                        CREATE (r)-[:HAS_CONDITION]->(c)
                        """,
                        rule_id=rule.rule_id,
                        condition_id=condition_id,
                        value=condition.value,
                        description=condition.description
                    )
    
    def import_rules(self, rules: List[Rule], clear_existing: bool = True):
        if clear_existing:
            self.clear_database()
        
        self.create_indexes()
        
        rule_groups = set(rule.rule_group for rule in rules)
        for group in rule_groups:
            self.create_rule_group(group)
        
        for rule in rules:
            self.create_rule(rule)
        
        print(f"[OK] 成功导入 {len(rules)} 条规则到知识图谱")
    
    def find_matching_rules(
        self,
        supervisor: Optional[str] = None,
        deviation: Optional[float] = None,
        hinge_type: Optional[str] = None,
        sequence_group: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            query = """
            MATCH (r:Rule)-[:HAS_CONDITION]->(c)
            WITH r, collect(c) AS conditions
            """
            
            filters = []
            params = {}
            
            if supervisor:
                filters.append("""
                EXISTS {
                    MATCH (r)-[:HAS_CONDITION]->(sc:SupervisorCondition)
                    WHERE (sc.operator = '=' AND sc.value = $supervisor)
                       OR (sc.operator = '<>' AND sc.value <> $supervisor)
                }
                """)
                params['supervisor'] = supervisor
            
            if deviation is not None:
                filters.append("""
                EXISTS {
                    MATCH (r)-[:HAS_CONDITION]->(dc:DeviationCondition)
                    WHERE (dc.operator = '<=' AND $deviation <= dc.max_value)
                       OR (dc.operator = '>' AND $deviation > dc.max_value)
                       OR (dc.operator = 'range' AND $deviation > dc.min_value AND $deviation <= dc.max_value)
                }
                """)
                params['deviation'] = deviation
            
            if hinge_type:
                filters.append("""
                (NOT EXISTS {
                    MATCH (r)-[:HAS_CONDITION]->(hc:HingeCondition)
                } OR EXISTS {
                    MATCH (r)-[:HAS_CONDITION]->(hc:HingeCondition)
                    WHERE hc.value CONTAINS $hinge_type
                })
                """)
                params['hinge_type'] = hinge_type
            
            if sequence_group:
                filters.append("""
                EXISTS {
                    MATCH (r)-[:HAS_CONDITION]->(seq:SequenceCondition)
                    WHERE seq.value = $sequence_group
                }
                """)
                params['sequence_group'] = sequence_group
            
            if filters:
                query += "WHERE " + " AND ".join(filters) + " "
            
            query += """
            RETURN r.rule_id AS rule_id,
                   r.solution AS solution,
                   r.raw_text AS raw_text,
                   [cond IN conditions WHERE labels(cond)[0] ENDS WITH 'Condition' | {
                       type: labels(cond)[0],
                       description: cond.description
                   }] AS condition_list
            """
            
            result = session.run(query, **params)
            return [dict(record) for record in result]
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r:Rule)-[:BELONGS_TO]->(rg:RuleGroup)
                OPTIONAL MATCH (r)-[:HAS_CONDITION]->(c)
                RETURN r.rule_id AS rule_id,
                       r.solution AS solution,
                       r.raw_text AS raw_text,
                       rg.name AS rule_group,
                       collect(c.description) AS conditions
            """)
            return [dict(record) for record in result]
    
    def get_statistics(self) -> Dict[str, int]:
        with self.driver.session() as session:
            stats = {}
            stats['rules'] = session.run("MATCH (r:Rule) RETURN count(r) AS count").single()['count']
            stats['rule_groups'] = session.run("MATCH (rg:RuleGroup) RETURN count(rg) AS count").single()['count']
            stats['supervisor_conditions'] = session.run("MATCH (c:SupervisorCondition) RETURN count(c) AS count").single()['count']
            stats['deviation_conditions'] = session.run("MATCH (c:DeviationCondition) RETURN count(c) AS count").single()['count']
            stats['hinge_conditions'] = session.run("MATCH (c:HingeCondition) RETURN count(c) AS count").single()['count']
            stats['sequence_conditions'] = session.run("MATCH (c:SequenceCondition) RETURN count(c) AS count").single()['count']
            stats['total_conditions'] = (stats['supervisor_conditions'] + stats['deviation_conditions'] + 
                                         stats['hinge_conditions'] + stats['sequence_conditions'])
            return stats


def build_knowledge_graph():
    print("\n" + "=" * 60)
    print("开始构建知识图谱")
    print("=" * 60)
    
    print("\n[1] 解析规则文件...")
    parser = RuleParser()
    rules = parser.parse_directory(str(settings.DATA_DIR))
    print(f"    解析到 {len(rules)} 条规则")
    
    print("\n[2] 连接Neo4j数据库...")
    kg = KnowledgeGraph()
    if not kg.connect():
        return None
    
    print("\n[3] 导入规则到知识图谱...")
    kg.import_rules(rules)
    
    print("\n[4] 验证导入结果...")
    stats = kg.get_statistics()
    print(f"    规则组数量: {stats['rule_groups']}")
    print(f"    规则数量: {stats['rules']}")
    print(f"    条件节点数量: {stats['total_conditions']}")
    print(f"      - 监理公司条件: {stats['supervisor_conditions']}")
    print(f"      - 偏心量条件: {stats['deviation_conditions']}")
    print(f"      - 铰点型号条件: {stats['hinge_conditions']}")
    print(f"      - 序号组条件: {stats['sequence_conditions']}")
    
    print("\n[5] 测试规则查询...")
    test_results = kg.find_matching_rules(
        supervisor="GBB",
        deviation=3.0,
        sequence_group="序号1-4"
    )
    print(f"    测试查询(GBB, 偏心量=3mm): 匹配到 {len(test_results)} 条规则")
    for r in test_results:
        print(f"      - {r['rule_id']}: {r['solution'][:50]}...")
    
    kg.close()
    print("\n" + "=" * 60)
    print("知识图谱构建完成!")
    print("=" * 60)
    
    return kg


if __name__ == "__main__":
    build_knowledge_graph()
