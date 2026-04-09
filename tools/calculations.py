import math
from typing import Dict, Any, Tuple, Optional


def pythagorean_calculation(side_a: float, side_b: float) -> Dict[str, Any]:
    """
    勾股定理计算斜长（偏心量）
    
    Args:
        side_a: 直角边A的长度（序号1或3、序号5或7的数值）
        side_b: 直角边B的长度（序号2或4、序号6或8的数值）
    
    Returns:
        包含计算结果的字典
    """
    hypotenuse = math.sqrt(side_a ** 2 + side_b ** 2)
    
    return {
        "side_a": side_a,
        "side_b": side_b,
        "hypotenuse": round(hypotenuse, 4),
        "formula": f"C = sqrt({side_a}^2 + {side_b}^2) = {round(hypotenuse, 4)}mm"
    }


def calculate_deviation(
    sequence_1_or_3: float,
    sequence_2_or_4: float,
    sequence_5_or_7: Optional[float] = None,
    sequence_6_or_8: Optional[float] = None
) -> Dict[str, Any]:
    """
    计算偏心量
    
    Args:
        sequence_1_or_3: 序号1或3的数值
        sequence_2_or_4: 序号2或4的数值
        sequence_5_or_7: 序号5或7的数值（可选）
        sequence_6_or_8: 序号6或8的数值（可选）
    
    Returns:
        包含所有偏心量计算结果的字典
    """
    results = {}
    
    if sequence_1_or_3 is not None and sequence_2_or_4 is not None:
        result_1_4 = pythagorean_calculation(sequence_1_or_3, sequence_2_or_4)
        results["序号1-4偏心量"] = result_1_4
    
    if sequence_5_or_7 is not None and sequence_6_or_8 is not None:
        result_5_8 = pythagorean_calculation(sequence_5_or_7, sequence_6_or_8)
        results["序号5-8偏心量"] = result_5_8
    
    return results


def determine_deviation_range(deviation: float) -> str:
    """
    判断偏心量所属区间
    
    Args:
        deviation: 偏心量数值
    
    Returns:
        区间描述字符串
    """
    if deviation <= 5:
        return "<=5mm"
    elif deviation <= 10:
        return "<=10mm"
    elif deviation <= 18:
        return "(10,18]mm"
    else:
        return ">18mm"


def parse_input_data(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析输入数据并计算偏心量
    
    Args:
        input_dict: 输入数据字典，包含：
            - supervisor: 监理公司名称
            - sequence_1: 序号1数值
            - sequence_2: 序号2数值
            - sequence_3: 序号3数值
            - sequence_4: 序号4数值
            - sequence_5: 序号5数值
            - sequence_6: 序号6数值
            - sequence_7: 序号7数值
            - sequence_8: 序号8数值
            - hinge_type: 铰点型号
    
    Returns:
        标准化的数据字典，包含计算结果
    """
    result = {
        "supervisor": input_dict.get("supervisor", ""),
        "hinge_type": input_dict.get("hinge_type", ""),
        "raw_data": input_dict,
        "calculations": {}
    }
    
    seq_1_3 = input_dict.get("sequence_1") or input_dict.get("sequence_3")
    seq_2_4 = input_dict.get("sequence_2") or input_dict.get("sequence_4")
    seq_5_7 = input_dict.get("sequence_5") or input_dict.get("sequence_7")
    seq_6_8 = input_dict.get("sequence_6") or input_dict.get("sequence_8")
    
    if seq_1_3 is not None and seq_2_4 is not None:
        calc = pythagorean_calculation(float(seq_1_3), float(seq_2_4))
        deviation_range = determine_deviation_range(calc["hypotenuse"])
        result["calculations"]["序号1-4"] = {
            **calc,
            "range": deviation_range
        }
        result["deviation_1_4"] = calc["hypotenuse"]
        result["deviation_1_4_range"] = deviation_range
    
    if seq_5_7 is not None and seq_6_8 is not None:
        calc = pythagorean_calculation(float(seq_5_7), float(seq_6_8))
        deviation_range = determine_deviation_range(calc["hypotenuse"])
        result["calculations"]["序号5-8"] = {
            **calc,
            "range": deviation_range
        }
        result["deviation_5_8"] = calc["hypotenuse"]
        result["deviation_5_8_range"] = deviation_range
    
    return result


if __name__ == "__main__":
    test_input = {
        "supervisor": "GBB",
        "sequence_1": 3.0,
        "sequence_2": 4.0,
        "hinge_type": "1#铰点"
    }
    
    result = parse_input_data(test_input)
    print("解析结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
