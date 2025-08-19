"""
MCP连接测试
验证MCP服务器是否正常运行
"""

import asyncio
import subprocess
import time
from pathlib import Path


def test_mcp_server_installation():
    """测试MCP服务器安装"""
    try:
        # 检查npm包是否安装
        result = subprocess.run(
            ["npm", "list", "-g", "@executeautomation/playwright-mcp-server"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Playwright MCP服务器已安装")
            return True
        else:
            print("❌ Playwright MCP服务器未正确安装")
            print(f"输出: {result.stdout}")
            print(f"错误: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 检查MCP服务器安装失败: {e}")
        return False


def test_mcp_server_startup():
    """测试MCP服务器启动"""
    try:
        print("🚀 启动MCP服务器...")
        
        # 启动MCP服务器（后台运行）
        process = subprocess.Popen(
            ["npx", "@executeautomation/playwright-mcp-server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务器启动
        time.sleep(3)
        
        # 检查进程是否还在运行
        if process.poll() is None:
            print("✅ MCP服务器成功启动")
            
            # 优雅关闭服务器
            process.terminate()
            process.wait(timeout=5)
            print("✅ MCP服务器成功关闭")
            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ MCP服务器启动失败")
            print(f"输出: {stdout}")
            print(f"错误: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ MCP服务器测试失败: {e}")
        if 'process' in locals():
            try:
                process.terminate()
            except:
                pass
        return False


def test_config_files():
    """测试配置文件是否存在"""
    config_files = [
        ".claude/mcp-config.json",
        "config/playwright_config.py",
        "config/mcp_settings.py",
        ".env",
        "package.json"
    ]
    
    all_exist = True
    for file_path in config_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"✅ 配置文件存在: {file_path}")
        else:
            print(f"❌ 配置文件缺失: {file_path}")
            all_exist = False
    
    return all_exist


def main():
    """主测试函数"""
    print("🔧 开始MCP连接测试...")
    print("=" * 50)
    
    # 测试配置文件
    print("\n📁 检查配置文件:")
    config_success = test_config_files()
    
    # 测试MCP服务器安装
    print("\n📦 检查MCP服务器安装:")
    install_success = test_mcp_server_installation()
    
    # 测试MCP服务器启动
    print("\n🚀 测试MCP服务器启动:")
    startup_success = test_mcp_server_startup()
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 MCP测试结果汇总:")
    print(f"配置文件检查: {'✅ 通过' if config_success else '❌ 失败'}")
    print(f"服务器安装检查: {'✅ 通过' if install_success else '❌ 失败'}")
    print(f"服务器启动测试: {'✅ 通过' if startup_success else '❌ 失败'}")
    
    all_success = config_success and install_success and startup_success
    print(f"\n🎯 MCP总体结果: {'✅ 所有测试通过！' if all_success else '❌ 部分测试失败'}")
    
    if all_success:
        print("\n🎉 MCP环境配置完成，可以开始使用！")
        print("\n📋 后续步骤:")
        print("1. 在Claude Desktop中配置MCP服务器")
        print("2. 重启Claude Desktop")
        print("3. 开始使用Playwright MCP功能")
    
    return all_success


if __name__ == "__main__":
    main()