import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from config import settings
from tools.rule_parser import Rule, RuleParser


class VectorStore:
    
    def __init__(self, persist_dir: str = None):
        if persist_dir is None:
            persist_dir = str(settings.CHROMA_PERSIST_DIR)
        
        self.persist_dir = persist_dir
        self.client = None
        self.collection = None
    
    def connect(self):
        try:
            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False
                )
            )
            print(f"[OK] 成功连接到ChromaDB: {self.persist_dir}")
            return True
        except Exception as e:
            print(f"[ERROR] 连接ChromaDB失败: {e}")
            return False
    
    def clear_collection(self, collection_name: str = "rules"):
        try:
            self.client.delete_collection(name=collection_name)
            print(f"[OK] 已清空集合: {collection_name}")
        except Exception:
            pass
    
    def create_collection(self, collection_name: str = "rules"):
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "制造偏差处理规则向量库"}
        )
        print(f"[OK] 创建/获取集合: {collection_name}")
    
    def add_rules(self, rules: List[Rule], collection_name: str = "rules"):
        if self.collection is None:
            self.create_collection(collection_name)
        
        ids = []
        documents = []
        metadatas = []
        
        for rule in rules:
            doc_text = self._create_document_text(rule)
            
            ids.append(rule.rule_id)
            documents.append(doc_text)
            metadatas.append({
                "rule_group": rule.rule_group,
                "solution": rule.solution,
                "raw_text": rule.raw_text[:500]
            })
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"[OK] 成功添加 {len(rules)} 条规则到向量库")
    
    def _create_document_text(self, rule: Rule) -> str:
        parts = [f"规则ID: {rule.rule_id}"]
        parts.append(f"规则组: {rule.rule_group}")
        
        if rule.conditions:
            parts.append("条件:")
            for c in rule.conditions:
                parts.append(f"  - {c.description}")
        
        parts.append(f"处理方案: {rule.solution}")
        
        return "\n".join(parts)
    
    def search(
        self,
        query: str,
        n_results: int = 3,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        if self.collection is None:
            self.create_collection()
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "rule_id": results['ids'][0][i],
                    "document": results['documents'][0][i] if results['documents'] else "",
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0
                })
        
        return formatted_results
    
    def search_by_conditions(
        self,
        supervisor: Optional[str] = None,
        deviation: Optional[float] = None,
        hinge_type: Optional[str] = None,
        sequence_group: Optional[str] = None,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        query_parts = []
        
        if supervisor:
            query_parts.append(f"监理公司{supervisor}")
        if deviation is not None:
            query_parts.append(f"偏心量{deviation}mm")
        if hinge_type:
            query_parts.append(f"铰点型号{hinge_type}")
        if sequence_group:
            query_parts.append(f"序号组{sequence_group}")
        
        query = " ".join(query_parts) if query_parts else "制造偏差处理规则"
        
        return self.search(query, n_results)
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        if self.collection is None:
            self.create_collection()
        
        results = self.collection.get()
        
        formatted_results = []
        if results['ids']:
            for i in range(len(results['ids'])):
                formatted_results.append({
                    "rule_id": results['ids'][i],
                    "document": results['documents'][i] if results['documents'] else "",
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                })
        
        return formatted_results
    
    def get_statistics(self) -> Dict[str, Any]:
        if self.collection is None:
            self.create_collection()
        
        count = self.collection.count()
        return {
            "total_rules": count,
            "collection_name": self.collection.name if self.collection else "N/A"
        }


def build_vector_store():
    print("\n" + "=" * 60)
    print("开始构建向量数据库")
    print("=" * 60)
    
    print("\n[1] 解析规则文件...")
    parser = RuleParser()
    rules = parser.parse_directory(str(settings.DATA_DIR))
    print(f"    解析到 {len(rules)} 条规则")
    
    print("\n[2] 连接ChromaDB...")
    vs = VectorStore()
    if not vs.connect():
        return None
    
    print("\n[3] 清空并重建向量库...")
    vs.clear_collection()
    vs.create_collection()
    
    print("\n[4] 添加规则到向量库...")
    vs.add_rules(rules)
    
    print("\n[5] 验证导入结果...")
    stats = vs.get_statistics()
    print(f"    向量库中规则数量: {stats['total_rules']}")
    
    print("\n[6] 测试语义检索...")
    
    test_queries = [
        "监理公司GBB 偏心量小于5mm",
        "监理公司不是GBB 偏心量大于18mm",
        "铰点型号1# 偏心量15mm",
        "序号5到8 偏心量大于5mm"
    ]
    
    for query in test_queries:
        print(f"\n    查询: \"{query}\"")
        results = vs.search(query, n_results=2)
        for i, r in enumerate(results, 1):
            print(f"      [{i}] {r['rule_id']} (相似度距离: {r['distance']:.4f})")
            print(f"          方案: {r['metadata'].get('solution', '')[:50]}...")
    
    print("\n" + "=" * 60)
    print("向量数据库构建完成!")
    print("=" * 60)
    
    return vs


if __name__ == "__main__":
    build_vector_store()
