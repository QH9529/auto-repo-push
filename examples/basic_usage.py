#!/usr/bin/env python3
"""
基本使用示例
展示如何使用Auto Repo Push工具
"""

import subprocess
import sys
from pathlib import Path


def run_example():
    """运行示例"""
    print("🎯 Auto Repo Push 使用示例")
    print("=" * 50)
    
    # 示例1：基本用法
    print("\n📝 示例1：基本用法")
    print("python github_upload.py --repo user/repo --path ./source")
    
    # 示例2：自定义提交信息
    print("\n📝 示例2：自定义提交信息")
    print("python github_upload.py --repo user/repo --path ./source --message 'feat: 添加新功能'")
    
    # 示例3：预览模式
    print("\n📝 示例3：预览模式（不实际执行）")
    print("python github_upload.py --repo user/repo --path ./source --dry-run")
    
    # 示例4：强制推送
    print("\n📝 示例4：强制推送")
    print("python github_upload.py --repo user/repo --path ./source --force")
    
    # 示例5：指定分支
    print("\n📝 示例5：指定分支")
    print("python github_upload.py --repo user/repo --path ./source --branch develop")
    
    # 示例6：详细输出
    print("\n📝 示例6：详细输出")
    print("python github_upload.py --repo user/repo --path ./source --verbose")
    
    print("\n" + "=" * 50)
    print("💡 提示：")
    print("1. 确保已配置SSH密钥并添加到GitHub/AtomGit")
    print("2. 确保已配置Git用户信息")
    print("3. 使用 --dry-run 参数预览操作")
    print("4. 首次使用建议先用预览模式检查")
    
    print("\n🚀 快速开始：")
    print("1. 克隆或下载此项目")
    print("2. 运行: python github_upload.py --repo your-username/your-repo --path /path/to/your/project")
    print("3. 按提示操作")


def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("❌ 需要Python 3.6或更高版本")
        return False
    print(f"✅ Python版本: {sys.version}")
    
    # 检查git是否安装
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Git版本: {result.stdout.strip()}")
        else:
            print("❌ Git未安装")
            return False
    except FileNotFoundError:
        print("❌ Git未安装或不在PATH中")
        return False
    
    return True


if __name__ == "__main__":
    if check_environment():
        run_example()
    else:
        print("❌ 环境检查失败，请先安装必要的工具")
        sys.exit(1)