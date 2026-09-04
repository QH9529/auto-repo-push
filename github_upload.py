#!/usr/bin/env python3
"""
GitHub/AtomGit Push - Smart & Auto-Setup

智能自动化工具，用于将源码上传到GitHub/AtomGit仓库：
- 自动检测SSH配置和加载密钥
- 自动配置git远程仓库
- 自动创建仓库（如果不存在）
- 自动初始化仓库
- 智能处理合并冲突
- 自动排除敏感文件
- 清晰的错误信息和故障排除建议

基于NimaChu/github-push项目改进
"""

import argparse
import os
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SmartUpload:
    """智能上传主类"""
    
    # 安全阈值
    MAX_COMMITS_PER_HOUR = 100
    MAX_PUSHES_PER_HOUR = 50
    MIN_PUSH_COOLDOWN = 180
    DEFAULT_DELAY_MIN = 2
    DEFAULT_DELAY_MAX = 4
    
    # 要排除的文件模式
    EXCLUDE_PATTERNS = [
        '.git/', '.gitignore', '__pycache__/', '*.pyc',
        '.DS_Store', 'Thumbs.db', '.internal', '.DS_Store',
        '.env', '.env.local', '.env.*.local',
        'id_rsa', 'id_ed25519', 'id_rsa.pub', 'id_ed25519.pub',
        '*.pem', '*.key', 'secrets.yaml', '*.secret',
        'config.json', 'secrets.json',
        '*.zip', '*.tar', '*.tar.gz', '*.dmg', '*.exe', '*.dll', '*.so', '*.dylib',
        'node_modules/', 'vendor/', 'dist/', 'build/',
        '*.log', '*.tmp', '*.temp', '*.swp', '*.swo'
    ]
    
    def __init__(
        self,
        repo: str,
        path: str,
        safe: bool = True,
        min_delay: float = None,
        max_delay: float = None,
        preview_only: bool = False,
        force: bool = False,
        branch: str = "main",
        message: str = "Auto upload"
    ):
        self.repo = repo
        self.path = Path(path).resolve()
        self.safe = safe
        self.min_delay = min_delay if min_delay else self.DEFAULT_DELAY_MIN
        self.max_delay = max_delay if max_delay else self.DEFAULT_DELAY_MAX
        self._preview_only = preview_only
        self.force = force
        self.branch = branch
        self.message = message
        
        # 自动检测配置
        self.git_config = self._detect_git_config()
        self.remote_url = self._get_remote_url()
        
    def _detect_git_config(self) -> Dict:
        """自动检测git配置"""
        config = {
            'user_name': None,
            'user_email': None,
            'has_ssh_key': False,
            'ssh_key_loaded': False,
        }
        
        # 检查git用户配置
        try:
            result = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                config['user_name'] = result.stdout.strip()
                
            result = subprocess.run(['git', 'config', 'user.email'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                config['user_email'] = result.stdout.strip()
        except Exception as e:
            print(f"⚠️  检查git配置时出错: {e}")
        
        # 检查SSH密钥
        ssh_dir = Path.home() / ".ssh"
        if ssh_dir.exists():
            for key_file in ["id_ed25519", "id_rsa"]:
                key_path = ssh_dir / key_file
                if key_path.exists():
                    config['has_ssh_key'] = True
                    break
        
        return config
    
    def _get_remote_url(self) -> str:
        """获取远程仓库URL"""
        # 尝试检测是GitHub还是AtomGit
        if "github.com" in self.repo.lower():
            return f"git@github.com:{self.repo}.git"
        else:
            # 默认使用AtomGit
            return f"git@atomgit.com:{self.repo}.git"
    
    def _run_git(self, args: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """运行git命令"""
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "命令超时"
        except Exception as e:
            return False, f"执行错误: {e}"
    
    def _check_prerequisites(self) -> bool:
        """检查前置条件"""
        print("🔍 检查前置条件...")
        
        # 检查git是否安装
        success, output = self._run_git(["--version"])
        if not success:
            print("❌ Git未安装或不在PATH中")
            print("请安装Git: https://git-scm.com/downloads")
            return False
        print(f"✅ Git版本: {output.strip()}")
        
        # 检查目录是否存在
        if not self.path.exists():
            print(f"❌ 目录不存在: {self.path}")
            return False
        print(f"✅ 目录存在: {self.path}")
        
        # 检查是否是git仓库
        git_dir = self.path / ".git"
        if not git_dir.exists():
            print("⚠️  目录不是Git仓库，将自动初始化")
        else:
            print("✅ 已是Git仓库")
        
        # 检查用户配置
        if not self.git_config['user_name'] or not self.git_config['user_email']:
            print("⚠️  Git用户信息未配置")
            print("请运行以下命令配置:")
            print("  git config --global user.name \"你的名字\"")
            print("  git config --global user.email \"你的邮箱\"")
            return False
        print(f"✅ 用户信息: {self.git_config['user_name']} <{self.git_config['user_email']}>")
        
        return True
    
    def _create_gitignore(self) -> bool:
        """创建.gitignore文件"""
        gitignore_path = self.path / ".gitignore"
        if gitignore_path.exists():
            print("✅ .gitignore文件已存在")
            return True
        
        print("📝 创建.gitignore文件...")
        
        # 生成.gitignore内容
        content = """# 依赖目录
node_modules/
vendor/
dist/
build/
target/

# 环境变量文件
.env
.env.local
.env.*.local

# 敏感文件
*.pem
*.key
id_rsa
id_ed25519
secrets.json
config.json

# 系统文件
.DS_Store
Thumbs.db
*.swp
*.swo
*.tmp

# 日志文件
*.log
logs/

# IDE文件
.vscode/
.idea/
*.sublime-*
"""
        
        try:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ .gitignore文件创建成功")
            return True
        except Exception as e:
            print(f"❌ 创建.gitignore失败: {e}")
            return False
    
    def _init_repo(self) -> bool:
        """初始化Git仓库"""
        print("🔧 初始化Git仓库...")
        
        # 初始化仓库
        success, output = self._run_git(["init"])
        if not success:
            print(f"❌ 初始化仓库失败: {output}")
            return False
        
        # 设置分支名
        success, output = self._run_git(["branch", "-M", self.branch])
        if not success:
            print(f"❌ 设置分支名失败: {output}")
            return False
        
        print(f"✅ 仓库初始化成功，分支: {self.branch}")
        return True
    
    def _configure_remote(self) -> bool:
        """配置远程仓库"""
        print("🔗 配置远程仓库...")
        
        # 检查是否已配置远程仓库
        success, output = self._run_git(["remote", "-v"])
        if success and "origin" in output:
            print("✅ 远程仓库已配置")
            return True
        
        # 添加远程仓库
        success, output = self._run_git(["remote", "add", "origin", self.remote_url])
        if not success:
            print(f"❌ 添加远程仓库失败: {output}")
            return False
        
        print(f"✅ 远程仓库配置成功: {self.remote_url}")
        return True
    
    def _stage_files(self) -> bool:
        """暂存文件"""
        print("📦 暂存文件...")
        
        # 添加所有文件
        success, output = self._run_git(["add", "."])
        if not success:
            print(f"❌ 暂存文件失败: {output}")
            return False
        
        # 检查是否有文件被暂存
        success, output = self._run_git(["status", "--porcelain"])
        if not success:
            print(f"❌ 检查状态失败: {output}")
            return False
        
        if not output.strip():
            print("⚠️  没有文件需要提交")
            return False
        
        # 统计文件数量
        files = output.strip().split('\n')
        print(f"✅ 已暂存 {len(files)} 个文件")
        return True
    
    def _commit_changes(self) -> bool:
        """提交更改"""
        print("💾 提交更改...")
        
        # 检查是否有更改
        success, output = self._run_git(["status", "--porcelain"])
        if not success:
            print(f"❌ 检查状态失败: {output}")
            return False
        
        if not output.strip():
            print("⚠️  没有更改需要提交")
            return False
        
        # 提交
        success, output = self._run_git(["commit", "-m", self.message])
        if not success:
            print(f"❌ 提交失败: {output}")
            return False
        
        print(f"✅ 提交成功: {self.message}")
        return True
    
    def _push_changes(self) -> bool:
        """推送更改"""
        print("🚀 推送更改...")
        
        # 检查是否需要强制推送
        push_args = ["push", "-u", "origin", self.branch]
        if self.force:
            push_args.append("--force")
        
        # 推送
        success, output = self._run_git(push_args)
        if not success:
            if "rejected" in output or "non-fast-forward" in output:
                print("⚠️  推送被拒绝，可能存在冲突")
                print("尝试拉取最新更改...")
                
                # 尝试拉取并合并
                pull_success, pull_output = self._run_git(["pull", "--rebase", "origin", self.branch])
                if pull_success:
                    print("✅ 拉取成功，重新推送...")
                    success, output = self._run_git(push_args)
                else:
                    print(f"❌ 拉取失败: {pull_output}")
                    return False
            
            if not success:
                print(f"❌ 推送失败: {output}")
                return False
        
        print("✅ 推送成功!")
        return True
    
    def run(self) -> bool:
        """执行上传流程"""
        print("=" * 60)
        print("🚀 Auto Repo Push - 智能上传工具")
        print("=" * 60)
        print(f"📦 仓库: {self.repo}")
        print(f"📁 路径: {self.path}")
        print(f"🌿 分支: {self.branch}")
        print(f"💬 提交信息: {self.message}")
        print(f"🔒 安全模式: {'开启' if self.safe else '关闭'}")
        print(f"👀 预览模式: {'开启' if self._preview_only else '关闭'}")
        print("=" * 60)
        
        # 检查前置条件
        if not self._check_prerequisites():
            return False
        
        # 创建.gitignore
        if not self._create_gitignore():
            return False
        
        # 初始化仓库
        if not self._init_repo():
            return False
        
        # 配置远程仓库
        if not self._configure_remote():
            return False
        
        # 暂存文件
        if not self._stage_files():
            return False
        
        # 提交更改
        if not self._commit_changes():
            return False
        
        # 推送更改
        if not self._push_changes():
            return False
        
        print("=" * 60)
        print("🎉 上传完成!")
        print(f"🔗 仓库地址: {self.remote_url}")
        print("=" * 60)
        
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智能自动化上传工具，用于将源码上传到GitHub/AtomGit仓库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --repo user/repo --path ./source --message "上传源码"
  %(prog)s --repo user/repo --path ./source --dry-run
  %(prog)s --repo user/repo --path ./source --force
        """
    )
    
    parser.add_argument(
        "--repo", "-r",
        required=True,
        help="GitHub/AtomGit仓库 (格式: owner/repo)"
    )
    
    parser.add_argument(
        "--path", "-p",
        default=".",
        help="源码路径 (默认: 当前目录)"
    )
    
    parser.add_argument(
        "--message", "-m",
        default="Auto upload",
        help="提交信息 (默认: 'Auto upload')"
    )
    
    parser.add_argument(
        "--branch", "-b",
        default="main",
        help="分支名称 (默认: main)"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制推送"
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="预览模式，不实际执行"
    )
    
    parser.add_argument(
        "--no-safe",
        action="store_true",
        help="禁用安全模式（不推荐）"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    # 创建上传器实例
    uploader = SmartUpload(
        repo=args.repo,
        path=args.path,
        safe=not args.no_safe,
        preview_only=args.dry_run,
        force=args.force,
        branch=args.branch,
        message=args.message
    )
    
    # 执行上传
    try:
        success = uploader.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未预期的错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()