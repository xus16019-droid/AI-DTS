import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Condition:
    condition_type: str
    operator: str
    value: Any
    description: str = ""


@dataclass
class Rule:
    rule_id: str
    rule_group: str
    conditions: List[Condition] = field(default_factory=list)
    logic: str = "AND"
    solution: str = ""
    raw_text: str = ""


class RuleParser:
    
    def __init__(self):
        self.rules: List[Rule] = []
    
    def parse_file(self, file_path: str, rule_group: str) -> List[Rule]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_content(content, rule_group)
    
    def parse_content(self, content: str, rule_group: str) -> List[Rule]:
        rules = []
        
        rule_pattern = r'规则(\d+)：(.+?)(?=规则\d+：|规则\d+结论：|$)'
        conclusion_pattern = r'规则(\d+)结论：(.+?)(?=规则\d+：|规则\d+结论：|$)'
        
        rule_matches = re.findall(rule_pattern, content, re.DOTALL)
        conclusion_matches = re.findall(conclusion_pattern, content, re.DOTALL)
        
        conclusions_dict = {num: text.strip() for num, text in conclusion_matches}
        
        for rule_num, rule_text in rule_matches:
            rule_id = f"{rule_group}_规则{rule_num}"
            solution = conclusions_dict.get(rule_num, "")
            
            conditions = self._parse_conditions(rule_text, rule_group)
            
            rule = Rule(
                rule_id=rule_id,
                rule_group=rule_group,
                conditions=conditions,
                solution=solution,
                raw_text=rule_text.strip()
            )
            rules.append(rule)
        
        return rules
    
    def _parse_conditions(self, rule_text: str, rule_group: str) -> List[Condition]:
        conditions = []
        
        supervisor_match = re.search(r'监理公司\s*=\s*(\w+)', rule_text)
        if supervisor_match:
            conditions.append(Condition(
                condition_type="supervisor",
                operator="=",
                value=supervisor_match.group(1),
                description=f"监理公司为{supervisor_match.group(1)}"
            ))
        
        supervisor_not_match = re.search(r'监理公司\s*<>\s*(\w+)', rule_text)
        if supervisor_not_match:
            conditions.append(Condition(
                condition_type="supervisor",
                operator="<>",
                value=supervisor_not_match.group(1),
                description=f"监理公司不为{supervisor_not_match.group(1)}"
            ))
        
        deviation_patterns = [
            (r'偏心量[）\)]\s*≤\s*(\d+)mm', "<="),
            (r'偏心量[）\)]\s*＞\s*(\d+)mm', ">"),
            (r'偏心量[）\)]\s*在\s*\((\d+)[，,](\d+)\]区间', "range"),
        ]
        
        for pattern, op in deviation_patterns:
            match = re.search(pattern, rule_text)
            if match:
                if op == "range":
                    conditions.append(Condition(
                        condition_type="deviation",
                        operator="range",
                        value=(float(match.group(1)), float(match.group(2))),
                        description=f"偏心量在({match.group(1)}, {match.group(2)}]区间"
                    ))
                else:
                    conditions.append(Condition(
                        condition_type="deviation",
                        operator=op,
                        value=float(match.group(1)),
                        description=f"偏心量{op}{match.group(1)}mm"
                    ))
                break
        
        hinge_match = re.search(r'铰点型号\s*=\s*(.+?)(?=规则|$)', rule_text)
        if hinge_match:
            hinge_value = hinge_match.group(1).strip()
            conditions.append(Condition(
                condition_type="hinge_type",
                operator="=",
                value=hinge_value,
                description=f"铰点型号为{hinge_value}"
            ))
        
        if "序号1或3" in rule_text or "序号2或4" in rule_text:
            conditions.append(Condition(
                condition_type="sequence_group",
                operator="=",
                value="序号1-4",
                description="使用序号1或3、序号2或4数值计算偏心量"
            ))
        
        if "序号5或7" in rule_text or "序号6或8" in rule_text:
            conditions.append(Condition(
                condition_type="sequence_group",
                operator="=",
                value="序号5-8",
                description="使用序号5或7、序号6或8数值计算偏心量"
            ))
        
        return conditions
    
    def parse_directory(self, dir_path: str) -> List[Rule]:
        all_rules = []
        dir_path = Path(dir_path)
        
        for file_path in dir_path.glob("*.txt"):
            if "序号1到4" in file_path.name:
                rule_group = "序号1-4规则组"
            elif "序号5到8" in file_path.name:
                rule_group = "序号5-8规则组"
            else:
                rule_group = file_path.stem
            
            rules = self.parse_file(str(file_path), rule_group)
            all_rules.extend(rules)
        
        self.rules = all_rules
        return all_rules
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        result = []
        for rule in self.rules:
            rule_dict = {
                "rule_id": rule.rule_id,
                "rule_group": rule.rule_group,
                "conditions": [
                    {
                        "type": c.condition_type,
                        "operator": c.operator,
                        "value": c.value,
                        "description": c.description
                    }
                    for c in rule.conditions
                ],
                "logic": rule.logic,
                "solution": rule.solution,
                "raw_text": rule.raw_text
            }
            result.append(rule_dict)
        return result


if __name__ == "__main__":
    parser = RuleParser()
    rules = parser.parse_directory("data")
    
    for rule in rules:
        print(f"\n{'='*60}")
        print(f"规则ID: {rule.rule_id}")
        print(f"规则组: {rule.rule_group}")
        print(f"条件:")
        for c in rule.conditions:
            print(f"  - {c.description}")
        print(f"处理方案: {rule.solution}")
