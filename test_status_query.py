#!/usr/bin/env python3
"""
测试机器人状态查询API。
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


async def test_status_query():
    """测试状态查询API。"""
    print("🔍 机器人状态查询测试\n")
    
    mcp = GausiumMCP("status-test")
    
    # 测试一个M线机器人的状态查询（75系列）
    test_serial = "GS-AS-0001-0005-0004-0003"  # 从之前的列表中选择一个
    
    try:
        print(f"📊 查询机器人状态: {test_serial}")
        print("   检测到75系列（M线），使用V1状态API...")
        
        status = await mcp.get_robot_status_v1(serial_number=test_serial)
        
        print("✅ 状态查询成功！")
        print(f"   数据类型: {type(status)}")
        
        if isinstance(status, dict):
            # 打印主要状态信息
            if 'robot' in status:
                robot_info = status['robot']
                print(f"   机器人名称: {robot_info.get('displayName', 'N/A')}")
                print(f"   在线状态: {robot_info.get('online', 'N/A')}")
                print(f"   电池电量: {robot_info.get('batteryLevel', 'N/A')}%")
                
                if 'position' in robot_info:
                    pos = robot_info['position']
                    print(f"   位置: ({pos.get('x', 'N/A')}, {pos.get('y', 'N/A')})")
                
                # 检查是否有任务列表（M线特有）
                if 'availableTaskPlans' in robot_info:
                    tasks = robot_info['availableTaskPlans']
                    print(f"   可用任务数量: {len(tasks)}")
                    if tasks:
                        print(f"   第一个任务: {tasks[0].get('taskDisplayName', 'N/A')}")
            
            print(f"\n   完整响应数据:")
            print(f"   {status}")
            
    except Exception as e:
        print(f"❌ 状态查询失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(test_status_query())