import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.orchestrator import run_workflow


if __name__ == "__main__":
    test_data = {
        "supervisor": "GBB",
        "sequence_1": 3.0,
        "sequence_2": 4.0,
        "hinge_type": "1#铰点"
    }
    
    print("测试: GBB监理公司, 偏心量<=5mm")
    print("=" * 60)
    
    result = run_workflow(test_data)
    
    print(f"\n最终状态: {result.get('status', 'N/A')}")
