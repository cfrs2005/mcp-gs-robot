#!/usr/bin/env python3
"""
测试智能工作流引擎。
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gs_openapi.mcp.gausium_mcp import GausiumMCP


async def test_m_line_workflow():
    """测试M线工作流。"""
    print("🚀 M线智能工作流测试\n")
    
    mcp = GausiumMCP("workflow-test")
    
    # 使用一个M线机器人测试工作流
    test_serial = "GS-AS-0001-0005-0004-0003"  # 75系列M线机器人
    
    try:
        print(f"⚙️ 执行M线任务工作流: {test_serial}")
        print("   工作流步骤：状态查询 → 任务选择 → 指令执行")
        
        # 定义任务选择条件（如果有多个可用任务）
        task_criteria = {
            "cleaning_mode": "__middle_cleaning"  # 中等清洁模式
        }
        
        result = await mcp.execute_m_line_task_workflow(
            serial_number=test_serial,
            task_selection_criteria=task_criteria
        )
        
        print("✅ M线工作流执行完成！")
        print(f"   结果类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"   工作流状态: {result.get('status', 'unknown')}")
            
            # 显示各个步骤的结果
            if 'steps' in result:
                for step_name, step_result in result['steps'].items():
                    print(f"   步骤 {step_name}: {step_result.get('status', 'unknown')}")
            
            if 'message' in result:
                print(f"   详细信息: {result['message']}")
                
            print(f"\n   完整结果:")
            print(f"   {result}")
        
    except Exception as e:
        print(f"❌ M线工作流执行失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(test_m_line_workflow())