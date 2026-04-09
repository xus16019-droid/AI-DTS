import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from typing import Dict, Any

from tools.calculations import pythagorean_calculation, determine_deviation_range, parse_input_data
from agents.orchestrator import run_workflow


class TestCalculations(unittest.TestCase):
    
    def test_pythagorean_calculation(self):
        result = pythagorean_calculation(3.0, 4.0)
        self.assertEqual(result["hypotenuse"], 5.0)
        self.assertEqual(result["side_a"], 3.0)
        self.assertEqual(result["side_b"], 4.0)
    
    def test_pythagorean_calculation_precision(self):
        result = pythagorean_calculation(1.0, 1.0)
        self.assertAlmostEqual(result["hypotenuse"], 1.4142, places=4)
    
    def test_determine_deviation_range(self):
        self.assertEqual(determine_deviation_range(3.0), "<=5mm")
        self.assertEqual(determine_deviation_range(5.0), "<=5mm")
        self.assertEqual(determine_deviation_range(7.0), "<=10mm")
        self.assertEqual(determine_deviation_range(10.0), "<=10mm")
        self.assertEqual(determine_deviation_range(15.0), "(10,18]mm")
        self.assertEqual(determine_deviation_range(18.0), "(10,18]mm")
        self.assertEqual(determine_deviation_range(20.0), ">18mm")
    
    def test_parse_input_data(self):
        input_data = {
            "supervisor": "GBB",
            "sequence_1": 3.0,
            "sequence_2": 4.0,
            "hinge_type": "1#铰点"
        }
        result = parse_input_data(input_data)
        
        self.assertEqual(result["supervisor"], "GBB")
        self.assertEqual(result["hinge_type"], "1#铰点")
        self.assertEqual(result["deviation_1_4"], 5.0)
        self.assertEqual(result["deviation_1_4_range"], "<=5mm")


class TestEndToEnd(unittest.TestCase):
    
    def test_workflow_gbb_deviation_5mm(self):
        input_data = {
            "supervisor": "GBB",
            "sequence_1": 3.0,
            "sequence_2": 4.0,
            "hinge_type": "1#铰点"
        }
        
        result = run_workflow(input_data)
        
        self.assertEqual(result["status"], "completed")
        self.assertIsNotNone(result["parsed_data"])
        self.assertEqual(result["parsed_data"]["deviation_1_4"], 5.0)
        self.assertIsNotNone(result["final_solution"])
        self.assertGreater(len(result["final_solution"]), 0)
    
    def test_workflow_gbb_deviation_15mm(self):
        input_data = {
            "supervisor": "GBB",
            "sequence_1": 9.0,
            "sequence_2": 12.0,
            "hinge_type": ""
        }
        
        result = run_workflow(input_data)
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["parsed_data"]["deviation_1_4"], 15.0)
        self.assertEqual(result["parsed_data"]["deviation_1_4_range"], "(10,18]mm")
    
    def test_workflow_sequence_5_8(self):
        input_data = {
            "supervisor": "GBB",
            "sequence_5": 4.0,
            "sequence_6": 5.0
        }
        
        result = run_workflow(input_data)
        
        self.assertEqual(result["status"], "completed")
        self.assertIsNotNone(result["parsed_data"].get("deviation_5_8"))


def run_tests():
    print("=" * 60)
    print("AI-DTS 端到端测试")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestCalculations))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
