#!/usr/bin/env python3
"""
Gausium OpenAPI MCP 基础测试脚本。

测试核心功能而不需要启动完整的MCP服务器。
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gs_openapi.core.client import GausiumAPIClient
from gs_openapi.core.endpoints import get_endpoint, ALL_ENDPOINTS
from gs_openapi.workflows.task_engine import TaskExecutionEngine
from gs_openapi.auth.token_manager import TokenManager


def test_endpoints_config():
    """测试端点配置。"""
    print("🔧 测试端点配置...")
    
    print(f"✅ 总计 {len(ALL_ENDPOINTS)} 个端点已配置")
    
    # 测试几个关键端点
    key_endpoints = [
        'list_robots',
        'get_robot_status_v1', 
        'get_robot_status_v2',
        'submit_temp_site_task',
        'get_map_subareas'
    ]
    
    for name in key_endpoints:
        try:
            endpoint = get_endpoint(name)
            print(f"✅ {name}: {endpoint.method.value} {endpoint.full_path}")
        except KeyError:
            print(f"❌ {name}: 端点未找到")


async def test_token_manager():
    """测试Token管理器（不实际调用API）。"""
    print("\n🔐 测试Token管理器...")
    
    try:
        token_manager = TokenManager()
        print("✅ TokenManager 初始化成功")
        
        # 检查是否需要环境变量
        required_vars = ['GS_CLIENT_ID', 'GS_CLIENT_SECRET', 'GS_OPEN_ACCESS_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"⚠️  缺少环境变量: {', '.join(missing_vars)}")
            print("   需要设置这些变量才能实际调用API")
        else:
            print("✅ 所有必需的环境变量已设置")
            
    except Exception as e:
        print(f"❌ TokenManager 初始化失败: {e}")


async def test_api_client():
    """测试API客户端（不实际调用API）。"""
    print("\n🌐 测试API客户端...")
    
    try:
        # 测试客户端初始化
        async with GausiumAPIClient() as client:
            print("✅ GausiumAPIClient 初始化成功")
            
            # 测试端点解析
            try:
                endpoint = get_endpoint('list_robots')
                formatted_path = endpoint.full_path
                print(f"✅ 端点路径格式化: {formatted_path}")
            except Exception as e:
                print(f"❌ 端点解析失败: {e}")
                
    except Exception as e:
        print(f"❌ API客户端测试失败: {e}")


def test_task_engine():
    """测试任务执行引擎。"""
    print("\n⚙️  测试任务执行引擎...")
    
    try:
        engine = TaskExecutionEngine()
        print("✅ TaskExecutionEngine 初始化成功")
        
        # 测试辅助方法
        test_data = {"key1": "value1", "key2": "value2"}
        criteria = {"key1": "value1"}
        
        if engine._matches_criteria(test_data, criteria):
            print("✅ 匹配条件逻辑正常工作")
        else:
            print("❌ 匹配条件逻辑有问题")
            
    except Exception as e:
        print(f"❌ 任务引擎测试失败: {e}")


def test_imports():
    """测试所有关键模块导入。"""
    print("\n📦 测试模块导入...")
    
    modules = [
        ('gs_openapi.core.client', 'GausiumAPIClient'),
        ('gs_openapi.core.endpoints', 'ALL_ENDPOINTS'), 
        ('gs_openapi.auth.token_manager', 'TokenManager'),
        ('gs_openapi.workflows.task_engine', 'TaskExecutionEngine'),
        ('gs_openapi.mcp.gausium_mcp', 'GausiumMCP')
    ]
    
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: {e}")


async def main():
    """主测试函数。"""
    print("🚀 Gausium OpenAPI MCP 基础功能测试\n")
    
    # 执行所有测试
    test_imports()
    test_endpoints_config()
    await test_token_manager()
    await test_api_client()
    test_task_engine()
    
    print("\n📋 测试总结:")
    print("- 如果所有测试显示 ✅，说明代码结构正确")
    print("- 要实际调用API，需要设置环境变量:")
    print("  export GS_CLIENT_ID='your_client_id'")
    print("  export GS_CLIENT_SECRET='your_client_secret'") 
    print("  export GS_OPEN_ACCESS_KEY='your_access_key'")
    print("- 然后可以运行: python main.py")


if __name__ == "__main__":
    asyncio.run(main())