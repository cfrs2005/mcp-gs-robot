#!/usr/bin/env python3
"""
Gausium OpenAPI MCP 直接API测试脚本。

直接调用API函数进行测试，而不通过MCP服务器。
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


async def test_api_calls():
    """测试实际的API调用。"""
    print("🚀 Gausium OpenAPI 直接API测试\n")
    
    # 创建MCP实例
    mcp = GausiumMCP("test-instance")
    
    try:
        print("📋 测试机器人列表API...")
        result = await mcp.list_robots(page=1, page_size=5)
        print(f"✅ 机器人列表调用成功")
        print(f"   返回数据类型: {type(result)}")
        if isinstance(result, dict) and 'data' in result:
            robots = result['data']
            print(f"   机器人数量: {len(robots) if robots else 0}")
            if robots:
                first_robot = robots[0]
                print(f"   第一个机器人序列号: {first_robot.get('serialNumber', 'N/A')}")
        else:
            print(f"   返回数据: {result}")
            
    except Exception as e:
        print(f"❌ 机器人列表API调用失败: {e}")
        return False
    
    # 如果有机器人，测试状态查询
    if isinstance(result, dict) and 'data' in result and result['data']:
        try:
            # 获取第一个机器人的序列号进行状态测试
            first_robot = result['data'][0]
            serial_number = first_robot.get('serialNumber')
            
            if serial_number:
                print(f"\n🔍 测试机器人状态查询 (序列号: {serial_number})...")
                
                # 根据序列号判断是M线还是S线
                if any(series in serial_number for series in ['M', '40', '50', '75']):
                    print("   检测到M线机器人，使用V1状态API...")
                    status_result = await mcp.get_robot_status_v1(serial_number=serial_number)
                else:
                    print("   检测到S线机器人，使用V2状态API...")  
                    status_result = await mcp.get_robot_status_v2(serial_number=serial_number)
                
                print(f"✅ 状态查询成功")
                print(f"   状态数据类型: {type(status_result)}")
                if isinstance(status_result, dict):
                    if 'batteryLevel' in str(status_result):
                        print("   包含电池信息 ✅")
                    if 'position' in str(status_result) or 'location' in str(status_result):
                        print("   包含位置信息 ✅")
                        
        except Exception as e:
            print(f"❌ 状态查询失败: {e}")
    
    print("\n📋 测试总结:")
    print("- 如果看到 ✅ 说明API调用成功")
    print("- 如果看到 ❌ 检查网络连接和API凭证")
    print("- MCP服务器已准备就绪，可以在Claude Desktop中使用！")
    return True


if __name__ == "__main__":
    asyncio.run(test_api_calls())