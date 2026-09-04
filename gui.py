#!/usr/bin/env python3
"""
Auto Repo Push - Windows GUI 客户端
基于 tkinter 的图形界面，用于将源码上传到 GitHub/AtomGit 仓库
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path

# 尝试导入 github_upload 模块
try:
    from github_upload import SmartUpload
except ImportError:
    SmartUpload = None


class AutoRepoPushGUI:
    """主窗口"""

    APP_TITLE = "Auto Repo Push"
    APP_VERSION = "1.0.0"
    WINDOW_SIZE = "820x680"
    WINDOW_MIN_SIZE = (700, 560)

    # 颜色主题
    BG = "#f5f5f5"
    FG = "#333333"
    ACCENT = "#2563eb"
    ACCENT_HOVER = "#1d4ed8"
    SUCCESS = "#16a34a"
    ERROR = "#dc2626"
    WARN = "#d97706"
    CARD_BG = "#ffffff"
    BORDER = "#e5e7eb"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{self.APP_TITLE} v{self.APP_VERSION}")
        self.root.geometry(self.WINDOW_SIZE)
        self.root.minsize(*self.WINDOW_MIN_SIZE)
        self.root.configure(bg=self.BG)

        # 设置图标（如果存在）
        icon_path = Path(__file__).parent / "icon.ico"
        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))

        # 变量
        self.repo_var = tk.StringVar()
        self.path_var = tk.StringVar(value=str(Path.cwd()))
        self.message_var = tk.StringVar(value="Auto upload")
        self.branch_var = tk.StringVar(value="main")
        self.private_var = tk.BooleanVar(value=False)
        self.force_var = tk.BooleanVar(value=False)
        self.dry_run_var = tk.BooleanVar(value=False)

        self._is_running = False
        self._upload_thread = None

        self._build_ui()
        self._center_window()

    # ── UI 构建 ──────────────────────────────────────────────

    def _build_ui(self):
        # 主容器
        main = tk.Frame(self.root, bg=self.BG, padx=20, pady=16)
        main.pack(fill=tk.BOTH, expand=True)

        # ── 标题栏 ──
        header = tk.Frame(main, bg=self.BG)
        header.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            header, text="🚀 " + self.APP_TITLE,
            font=("Segoe UI", 18, "bold"), bg=self.BG, fg=self.FG,
        ).pack(side=tk.LEFT)

        tk.Label(
            header, text=f"v{self.APP_VERSION}",
            font=("Segoe UI", 10), bg=self.BG, fg="#9ca3af",
        ).pack(side=tk.LEFT, padx=(8, 0), pady=(6, 0))

        # ── 设置卡片 ──
        card = tk.Frame(main, bg=self.CARD_BG, relief=tk.FLAT,
                        highlightbackground=self.BORDER, highlightthickness=1,
                        padx=20, pady=16)
        card.pack(fill=tk.X, pady=(0, 12))

        # 第 1 行：仓库
        row1 = tk.Frame(card, bg=self.CARD_BG)
        row1.pack(fill=tk.X, pady=(0, 10))
        tk.Label(row1, text="仓库 *", font=("Segoe UI", 10, "bold"),
                 bg=self.CARD_BG, fg=self.FG, width=10, anchor="w").pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.repo_var, font=("Segoe UI", 10),
                 width=52).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        tk.Label(row1, text="格式: owner/repo", font=("Segoe UI", 8),
                 bg=self.CARD_BG, fg="#9ca3af").pack(side=tk.LEFT)

        # 第 2 行：源码路径
        row2 = tk.Frame(card, bg=self.CARD_BG)
        row2.pack(fill=tk.X, pady=(0, 10))
        tk.Label(row2, text="源码路径", font=("Segoe UI", 10, "bold"),
                 bg=self.CARD_BG, fg=self.FG, width=10, anchor="w").pack(side=tk.LEFT)
        tk.Entry(row2, textvariable=self.path_var, font=("Segoe UI", 10),
                 width=42).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(row2, text="浏览…", command=self._browse_path).pack(side=tk.LEFT)

        # 第 3 行：提交信息
        row3 = tk.Frame(card, bg=self.CARD_BG)
        row3.pack(fill=tk.X, pady=(0, 10))
        tk.Label(row3, text="提交信息", font=("Segoe UI", 10, "bold"),
                 bg=self.CARD_BG, fg=self.FG, width=10, anchor="w").pack(side=tk.LEFT)
        tk.Entry(row3, textvariable=self.message_var, font=("Segoe UI", 10),
                 width=52).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 第 4 行：分支
        row4 = tk.Frame(card, bg=self.CARD_BG)
        row4.pack(fill=tk.X, pady=(0, 6))
        tk.Label(row4, text="分支", font=("Segoe UI", 10, "bold"),
                 bg=self.CARD_BG, fg=self.FG, width=10, anchor="w").pack(side=tk.LEFT)
        tk.Entry(row4, textvariable=self.branch_var, font=("Segoe UI", 10),
                 width=20).pack(side=tk.LEFT)

        # 第 5 行：复选框
        row5 = tk.Frame(card, bg=self.CARD_BG)
        row5.pack(fill=tk.X, pady=(6, 0))
        tk.Label(row5, text="选项", font=("Segoe UI", 10, "bold"),
                 bg=self.CARD_BG, fg=self.FG, width=10, anchor="w").pack(side=tk.LEFT)

        for text, var in [
            ("🔒 私有仓库", self.private_var),
            ("⚡ 强制推送", self.force_var),
            ("👀 预览模式", self.dry_run_var),
        ]:
            tk.Checkbutton(row5, text=text, variable=var,
                           font=("Segoe UI", 10), bg=self.CARD_BG, fg=self.FG,
                           selectcolor=self.CARD_BG, activebackground=self.CARD_BG,
                           ).pack(side=tk.LEFT, padx=(0, 16))

        # ── 操作按钮 ──
        btn_frame = tk.Frame(main, bg=self.BG)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self._upload_btn = tk.Button(
            btn_frame, text="🚀  开始上传", font=("Segoe UI", 12, "bold"),
            bg=self.ACCENT, fg="white", activebackground=self.ACCENT_HOVER,
            activeforeground="white", relief=tk.FLAT, padx=28, pady=8,
            cursor="hand2", command=self._on_upload,
        )
        self._upload_btn.pack(side=tk.LEFT)

        self._stop_btn = tk.Button(
            btn_frame, text="⏹  停止", font=("Segoe UI", 10),
            bg="#e5e7eb", fg=self.FG, relief=tk.FLAT, padx=16, pady=8,
            cursor="hand2", command=self._on_stop, state=tk.DISABLED,
        )
        self._stop_btn.pack(side=tk.LEFT, padx=(12, 0))

        self._clear_btn = tk.Button(
            btn_frame, text="🗑  清空日志", font=("Segoe UI", 10),
            bg="#e5e7eb", fg=self.FG, relief=tk.FLAT, padx=16, pady=8,
            cursor="hand2", command=self._clear_log,
        )
        self._clear_btn.pack(side=tk.RIGHT)

        # 状态标签
        self._status_var = tk.StringVar(value="就绪")
        tk.Label(btn_frame, textvariable=self._status_var,
                 font=("Segoe UI", 9), bg=self.BG, fg="#6b7280").pack(side=tk.RIGHT, padx=(0, 16))

        # ── 日志输出 ──
        log_label = tk.Frame(main, bg=self.BG)
        log_label.pack(fill=tk.X, pady=(0, 4))
        tk.Label(log_label, text="📋 输出日志", font=("Segoe UI", 10, "bold"),
                 bg=self.BG, fg=self.FG).pack(side=tk.LEFT)

        self._log = scrolledtext.ScrolledText(
            main, font=("Consolas", 10), bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white", relief=tk.FLAT, height=18,
            state=tk.DISABLED, wrap=tk.WORD,
        )
        self._log.pack(fill=tk.BOTH, expand=True)

        # 日志标签颜色
        self._log.tag_configure("info", foreground="#d4d4d4")
        self._log.tag_configure("success", foreground="#4ade80")
        self._log.tag_configure("error", foreground="#f87171")
        self._log.tag_configure("warn", foreground="#fbbf24")
        self._log.tag_configure("title", foreground="#60a5fa", font=("Consolas", 10, "bold"))

    # ── 窗口居中 ──────────────────────────────────────────────

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")

    # ── 日志工具 ──────────────────────────────────────────────

    def _log_write(self, text: str, tag: str = "info"):
        self._log.configure(state=tk.NORMAL)
        self._log.insert(tk.END, text + "\n", tag)
        self._log.see(tk.END)
        self._log.configure(state=tk.DISABLED)

    def _clear_log(self):
        self._log.configure(state=tk.NORMAL)
        self._log.delete("1.0", tk.END)
        self._log.configure(state=tk.DISABLED)

    # ── 事件处理 ──────────────────────────────────────────────

    def _browse_path(self):
        path = filedialog.askdirectory(title="选择源码目录")
        if path:
            self.path_var.set(path)

    def _validate(self) -> bool:
        repo = self.repo_var.get().strip()
        if not repo or "/" not in repo:
            messagebox.showwarning("参数错误", "请填写仓库地址，格式: owner/repo")
            return False

        path = self.path_var.get().strip()
        if not path or not Path(path).is_dir():
            messagebox.showwarning("参数错误", "请选择有效的源码目录")
            return False

        return True

    def _set_running(self, running: bool):
        self._is_running = running
        state_normal = tk.NORMAL if not running else tk.DISABLED
        state_disabled = tk.NORMAL if running else tk.DISABLED
        self._upload_btn.configure(state=state_normal)
        self._stop_btn.configure(state=state_disabled)
        self._status_var.set("上传中…" if running else "就绪")

    def _on_upload(self):
        if not self._validate():
            return
        if SmartUpload is None:
            messagebox.showerror("模块缺失", "找不到 github_upload.py，请确保它在同一目录下")
            return

        self._set_running(True)
        self._clear_log()
        self._upload_thread = threading.Thread(target=self._do_upload, daemon=True)
        self._upload_thread.start()

    def _on_stop(self):
        self._is_running = False
        self._log_write("⏹ 用户已停止操作", "warn")
        self._set_running(False)

    def _do_upload(self):
        """在后台线程中执行上传"""
        repo = self.repo_var.get().strip()
        path = self.path_var.get().strip()
        message = self.message_var.get().strip() or "Auto upload"
        branch = self.branch_var.get().strip() or "main"
        private = self.private_var.get()
        force = self.force_var.get()
        dry_run = self.dry_run_var.get()

        self._log_write("=" * 56, "title")
        self._log_write(f"🚀 {self.APP_TITLE}", "title")
        self._log_write("=" * 56, "title")
        self._log_write(f"📦 仓库:     {repo}", "info")
        self._log_write(f"📁 路径:     {path}", "info")
        self._log_write(f"🌿 分支:     {branch}", "info")
        self._log_write(f"💬 提交信息: {message}", "info")
        self._log_write(f"👁️  可见性:   {'私有' if private else '公开'}", "info")
        vis_tag = "warn" if private else "info"
        self._log_write(f"⚡ 强制推送: {'是' if force else '否'}", vis_tag)
        self._log_write(f"👀 预览模式: {'是' if dry_run else '否'}", "info" if not dry_run else "warn")
        self._log_write("-" * 56, "info")

        try:
            uploader = SmartUpload(
                repo=repo,
                path=path,
                safe=True,
                preview_only=dry_run,
                force=force,
                private=private,
                branch=branch,
                message=message,
            )

            # 重定向 stdout 到日志窗口
            import io
            import contextlib

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                success = uploader.run()

            # 输出捕获的日志
            for line in buf.getvalue().splitlines():
                if "✅" in line or "成功" in line or "完成" in line:
                    self._log_write(line, "success")
                elif "❌" in line or "失败" in line or "错误" in line:
                    self._log_write(line, "error")
                elif "⚠️" in line or "警告" in line:
                    self._log_write(line, "warn")
                else:
                    self._log_write(line, "info")

            if success:
                self._log_write("-" * 56, "info")
                self._log_write("🎉 上传完成!", "success")
            else:
                self._log_write("-" * 56, "info")
                self._log_write("❌ 上传失败", "error")

        except Exception as e:
            self._log_write(f"❌ 未预期的错误: {e}", "error")

        finally:
            self.root.after(0, lambda: self._set_running(False))

    # ── 启动 ──────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


def main():
    app = AutoRepoPushGUI()
    app.run()


if __name__ == "__main__":
    main()
