#!/usr/bin/env python3
"""
Auto Repo Push - Windows GUI 客户端
现代化图形界面，用于将源码上传到 GitHub/AtomGit 仓库
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path

try:
    from github_upload import SmartUpload
except ImportError:
    SmartUpload = None


# ═══════════════════════════════════════════════════════════════
#  颜色 & 样式常量
# ═══════════════════════════════════════════════════════════════

COLORS = {
    "bg":           "#f0f2f5",
    "card":         "#ffffff",
    "card_border":  "#dce1e8",
    "text":         "#1a1d23",
    "text_sec":     "#6b7280",
    "text_hint":    "#9ca3af",
    "accent":       "#4f6ef7",
    "accent_hover": "#3b5de7",
    "accent_light": "#eef2ff",
    "success":      "#10b981",
    "success_bg":   "#ecfdf5",
    "error":        "#ef4444",
    "error_bg":     "#fef2f2",
    "warn":         "#f59e0b",
    "warn_bg":      "#fffbeb",
    "border":       "#e5e7eb",
    "input_bg":     "#f9fafb",
    "input_focus":  "#4f6ef7",
    "log_bg":       "#1e1e2e",
    "log_fg":       "#cdd6f4",
    "sidebar":      "#ffffff",
    "tag_bg":       "#f1f3f5",
}


# ═══════════════════════════════════════════════════════════════
#  自定义组件
# ═══════════════════════════════════════════════════════════════

class RoundedButton(tk.Canvas):
    """圆角按钮"""

    def __init__(self, parent, text="", command=None,
                 bg=COLORS["accent"], fg="white", hover_bg=None,
                 font=("Segoe UI", 10, "bold"), padx=20, pady=8, **kw):
        super().__init__(parent, highlightthickness=0, bg=parent["bg"], **kw)
        self._cmd = command
        self._bg = bg
        self._fg = fg
        self._hover_bg = hover_bg or bg
        self._font = font
        self._padx = padx
        self._pady = pady
        self._text = text
        self._radius = 8

        self.configure(cursor="hand2")
        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)

    def _draw(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        r = self._radius
        # 圆角矩形
        self.create_arc(0, 0, 2 * r, 2 * r, start=90, extent=90, fill=self._bg, outline="")
        self.create_arc(w - 2 * r, 0, w, 2 * r, start=0, extent=90, fill=self._bg, outline="")
        self.create_arc(0, h - 2 * r, 2 * r, h, start=180, extent=90, fill=self._bg, outline="")
        self.create_arc(w - 2 * r, h - 2 * r, w, h, start=270, extent=90, fill=self._bg, outline="")
        self.create_rectangle(r, 0, w - r, h, fill=self._bg, outline="")
        self.create_rectangle(0, r, w, h - r, fill=self._bg, outline="")
        # 文字
        self.create_text(w // 2, h // 2, text=self._text, fill=self._fg,
                         font=self._font)

    def _on_enter(self, e):
        self._bg = self._hover_bg
        self._draw()

    def _on_leave(self, e):
        self._bg = self._hover_bg if self._hover_bg != self._bg else self._bg
        # 恢复原始颜色（从 __init__ 保存）
        self._bg = COLORS["accent"]
        self._draw()

    def _on_press(self, e):
        if self._cmd:
            self._cmd()

    def set_enabled(self, enabled: bool):
        if enabled:
            self.configure(cursor="hand2")
            self._bg = COLORS["accent"]
            self.bind("<ButtonPress-1>", self._on_press)
        else:
            self.configure(cursor="arrow")
            self._bg = COLORS["border"]
            self.unbind("<ButtonPress-1>")
        self._draw()


class FileSelector(tk.Frame):
    """文件选择组件：左侧列表 + 右侧操作按钮"""

    def __init__(self, parent, bg=COLORS["card"], **kw):
        super().__init__(parent, bg=bg, **kw)
        self._files: list[str] = []
        self._var = tk.StringVar(value="")

        self._build()

    def _build(self):
        # ── 顶部标题栏 ──
        header = tk.Frame(self, bg=self["bg"])
        header.pack(fill=tk.X, padx=12, pady=(10, 4))

        tk.Label(header, text="📄 文件列表", font=("Segoe UI", 10, "bold"),
                 bg=self["bg"], fg=COLORS["text"]).pack(side=tk.LEFT)

        self._count_label = tk.Label(header, text="共 0 个文件",
                                     font=("Segoe UI", 9), bg=self["bg"],
                                     fg=COLORS["text_sec"])
        self._count_label.pack(side=tk.RIGHT)

        # ── 列表框 + 滚动条 ──
        list_frame = tk.Frame(self, bg=self["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        self._listbox = tk.Listbox(
            list_frame, font=("Consolas", 9), bg=COLORS["input_bg"],
            fg=COLORS["text"], selectbackground=COLORS["accent_light"],
            selectforeground=COLORS["accent"], relief=tk.FLAT,
            highlightthickness=1, highlightbackground=COLORS["border"],
            activestyle="none", bd=0,
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                  command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=scrollbar.set)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ── 底部按钮栏 ──
        btn_frame = tk.Frame(self, bg=self["bg"])
        btn_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        btn_style = dict(
            font=("Segoe UI", 9), relief=tk.FLAT, cursor="hand2",
            padx=10, pady=3, bd=0,
        )

        tk.Button(btn_frame, text="➕ 添加文件", bg=COLORS["accent_light"],
                  fg=COLORS["accent"], activebackground=COLORS["accent_light"],
                  command=self._add_files, **btn_style).pack(side=tk.LEFT, padx=(0, 4))

        tk.Button(btn_frame, text="📂 添加目录", bg=COLORS["accent_light"],
                  fg=COLORS["accent"], activebackground=COLORS["accent_light"],
                  command=self._add_folder, **btn_style).pack(side=tk.LEFT, padx=(0, 4))

        tk.Button(btn_frame, text="❌ 移除选中", bg=COLORS["error_bg"],
                  fg=COLORS["error"], activebackground=COLORS["error_bg"],
                  command=self._remove_selected, **btn_style).pack(side=tk.LEFT, padx=(0, 4))

        tk.Button(btn_frame, text="🗑 清空", bg=COLORS["warn_bg"],
                  fg=COLORS["warn"], activebackground=COLORS["warn_bg"],
                  command=self._clear_all, **btn_style).pack(side=tk.LEFT)

        tk.Button(btn_frame, text="✅ 全选", bg=COLORS["tag_bg"],
                  fg=COLORS["text_sec"], activebackground=COLORS["tag_bg"],
                  command=self._select_all, **btn_style).pack(side=tk.RIGHT)

    def _update_count(self):
        n = len(self._files)
        self._count_label.configure(text=f"共 {n} 个文件")

    def _refresh_listbox(self):
        self._listbox.delete(0, tk.END)
        for f in self._files:
            self._listbox.insert(tk.END, f)
        self._update_count()

    def set_files(self, base_path: str):
        """扫描目录，填充文件列表（默认全选）"""
        self._files.clear()
        base = Path(base_path)
        if not base.is_dir():
            return

        # 排除模式
        exclude_dirs = {".git", "__pycache__", "node_modules", "venv", "env",
                        ".vscode", ".idea", "dist", "build", ".cache"}
        exclude_exts = {".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib",
                        ".zip", ".tar", ".gz", ".dmg", ".log", ".tmp",
                        ".swp", ".swo", ".key", ".pem"}

        for root, dirs, files in os.walk(base):
            # 跳过排除目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for fname in sorted(files):
                ext = Path(fname).suffix.lower()
                if ext in exclude_exts:
                    continue
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, base).replace("\\", "/")
                self._files.append(rel)

        self._refresh_listbox()
        # 默认全选
        self._listbox.select_set(0, tk.END)

    def _add_files(self):
        paths = filedialog.askopenfilenames(title="选择文件")
        for p in paths:
            rel = os.path.basename(p)
            if rel not in self._files:
                self._files.append(rel)
        self._refresh_listbox()

    def _add_folder(self):
        folder = filedialog.askdirectory(title="选择目录")
        if folder:
            for root, dirs, files in os.walk(folder):
                for f in sorted(files):
                    rel = os.path.relpath(os.path.join(root, f), folder).replace("\\", "/")
                    if rel not in self._files:
                        self._files.append(rel)
            self._refresh_listbox()

    def _remove_selected(self):
        sel = self._listbox.curselection()
        if not sel:
            return
        for i in reversed(sel):
            self._listbox.delete(i)
            del self._files[i]
        self._update_count()

    def _clear_all(self):
        self._files.clear()
        self._refresh_listbox()

    def _select_all(self):
        self._listbox.select_set(0, tk.END)

    def get_selected_files(self) -> list[str]:
        sel = self._listbox.curselection()
        return [self._files[i] for i in sel]

    def get_all_files(self) -> list[str]:
        return list(self._files)


# ═══════════════════════════════════════════════════════════════
#  主窗口
# ═══════════════════════════════════════════════════════════════

class AutoRepoPushGUI:
    APP_TITLE = "Auto Repo Push"
    APP_VERSION = "1.0.0"
    WINDOW_SIZE = "960x720"
    WINDOW_MIN_SIZE = (800, 600)
    ICON_PATH = Path(__file__).parent / "GitHub Auto upload.ico"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{self.APP_TITLE}  v{self.APP_VERSION}")
        self.root.geometry(self.WINDOW_SIZE)
        self.root.minsize(*self.WINDOW_MIN_SIZE)
        self.root.configure(bg=COLORS["bg"])

        # 设置图标
        if self.ICON_PATH.exists():
            try:
                self.root.iconbitmap(str(self.ICON_PATH))
            except Exception:
                pass

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

        # 监听路径变化 → 刷新文件列表
        self.path_var.trace_add("write", self._on_path_change)
        # 初始加载
        if Path(self.path_var.get()).is_dir():
            self._file_selector.set_files(self.path_var.get())

    # ── UI 构建 ──────────────────────────────────────────────

    def _build_ui(self):
        main = tk.Frame(self.root, bg=COLORS["bg"], padx=16, pady=12)
        main.pack(fill=tk.BOTH, expand=True)

        # （标题已由窗口标题栏显示，此处不再重复）

        # ════ 主体：左侧设置 + 右侧文件 ════
        body = tk.Frame(main, bg=COLORS["bg"])
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # ── 左侧面板 ──
        left = tk.Frame(body, bg=COLORS["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self._build_settings_card(left)

        # ── 右侧面板（文件选择） ──
        right = tk.Frame(body, bg=COLORS["bg"])
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        file_card = tk.Frame(right, bg=COLORS["card"], relief=tk.FLAT,
                             highlightbackground=COLORS["card_border"],
                             highlightthickness=1)
        file_card.pack(fill=tk.BOTH, expand=True)

        self._file_selector = FileSelector(file_card, bg=COLORS["card"])
        self._file_selector.pack(fill=tk.BOTH, expand=True)

        # ════ 底部操作栏 ════
        self._build_action_bar(main)

        # ════ 日志 ════
        self._build_log_area(main)

    def _build_settings_card(self, parent):
        """左侧设置卡片"""
        card = tk.Frame(parent, bg=COLORS["card"], relief=tk.FLAT,
                        highlightbackground=COLORS["card_border"],
                        highlightthickness=1, padx=20, pady=16)
        card.pack(fill=tk.BOTH, expand=True)

        tk.Label(card, text="⚙️  仓库设置", font=("Segoe UI", 12, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 12))

        # ── 输入行通用方法 ──
        def make_row(label, widget_factory, hint=""):
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(fill=tk.X, pady=(0, 10))
            tk.Label(row, text=label, font=("Segoe UI", 10),
                     bg=COLORS["card"], fg=COLORS["text"],
                     width=10, anchor="w").pack(side=tk.LEFT)
            widget_factory(row)
            if hint:
                tk.Label(row, text=hint, font=("Segoe UI", 8),
                         bg=COLORS["card"],
                         fg=COLORS["text_hint"]).pack(side=tk.LEFT, padx=(6, 0))
            return row

        # 仓库
        def repo_widget(parent):
            e = tk.Entry(parent, textvariable=self.repo_var,
                         font=("Segoe UI", 10), bg=COLORS["input_bg"],
                         relief=tk.FLAT, highlightthickness=1,
                         highlightbackground=COLORS["border"],
                         highlightcolor=COLORS["input_focus"])
            e.pack(side=tk.LEFT, fill=tk.X, expand=True)
        make_row("仓库 *", repo_widget, "格式: owner/repo")

        # 源码路径
        def path_widget(parent):
            e = tk.Entry(parent, textvariable=self.path_var,
                         font=("Segoe UI", 10), bg=COLORS["input_bg"],
                         relief=tk.FLAT, highlightthickness=1,
                         highlightbackground=COLORS["border"],
                         highlightcolor=COLORS["input_focus"])
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
            b = tk.Button(parent, text="浏览", font=("Segoe UI", 9),
                          bg=COLORS["accent_light"], fg=COLORS["accent"],
                          relief=tk.FLAT, cursor="hand2", padx=12, pady=2,
                          command=self._browse_path)
            b.pack(side=tk.LEFT)
        make_row("源码路径", path_widget)

        # 提交信息
        def msg_widget(parent):
            tk.Entry(parent, textvariable=self.message_var,
                     font=("Segoe UI", 10), bg=COLORS["input_bg"],
                     relief=tk.FLAT, highlightthickness=1,
                     highlightbackground=COLORS["border"],
                     highlightcolor=COLORS["input_focus"]).pack(
                side=tk.LEFT, fill=tk.X, expand=True)
        make_row("提交信息", msg_widget)

        # 分支
        def branch_widget(parent):
            tk.Entry(parent, textvariable=self.branch_var,
                     font=("Segoe UI", 10), bg=COLORS["input_bg"],
                     relief=tk.FLAT, highlightthickness=1,
                     highlightbackground=COLORS["border"],
                     highlightcolor=COLORS["input_focus"], width=16).pack(
                side=tk.LEFT)
        make_row("分支", branch_widget, "默认 main")

        # ── 选项复选框 ──
        sep = tk.Frame(card, bg=COLORS["border"], height=1)
        sep.pack(fill=tk.X, pady=(6, 12))

        opt_row = tk.Frame(card, bg=COLORS["card"])
        opt_row.pack(fill=tk.X)

        tk.Label(opt_row, text="选项", font=("Segoe UI", 10),
                 bg=COLORS["card"], fg=COLORS["text"],
                 width=10, anchor="w").pack(side=tk.LEFT)

        for text, var, color in [
            ("🔒 私有仓库", self.private_var, COLORS["accent"]),
            ("⚡ 强制推送", self.force_var, COLORS["warn"]),
            ("👀 预览模式", self.dry_run_var, COLORS["text_sec"]),
        ]:
            cb = tk.Checkbutton(opt_row, text=text, variable=var,
                                font=("Segoe UI", 10), bg=COLORS["card"],
                                fg=COLORS["text"], selectcolor=COLORS["card"],
                                activebackground=COLORS["card"],
                                activeforeground=color,
                                highlightthickness=0)
            cb.pack(side=tk.LEFT, padx=(0, 14))

    def _build_action_bar(self, parent):
        """底部操作按钮栏"""
        bar = tk.Frame(parent, bg=COLORS["bg"])
        bar.pack(fill=tk.X, pady=(10, 6))

        # 上传按钮（圆角风格）
        self._upload_btn = tk.Button(
            bar, text="  🚀  开始上传  ", font=("Segoe UI", 12, "bold"),
            bg=COLORS["accent"], fg="white", activebackground=COLORS["accent_hover"],
            activeforeground="white", relief=tk.FLAT, padx=24, pady=8,
            cursor="hand2", command=self._on_upload,
        )
        self._upload_btn.pack(side=tk.LEFT)

        self._stop_btn = tk.Button(
            bar, text="⏹ 停止", font=("Segoe UI", 10),
            bg=COLORS["border"], fg=COLORS["text_sec"], relief=tk.FLAT,
            padx=14, pady=6, cursor="hand2",
            command=self._on_stop, state=tk.DISABLED,
        )
        self._stop_btn.pack(side=tk.LEFT, padx=(10, 0))

        tk.Button(
            bar, text="🗑 清空日志", font=("Segoe UI", 9),
            bg=COLORS["tag_bg"], fg=COLORS["text_sec"], relief=tk.FLAT,
            padx=10, pady=4, cursor="hand2",
            command=self._clear_log,
        ).pack(side=tk.RIGHT)

        self._status_var = tk.StringVar(value="就绪")
        self._status_label = tk.Label(bar, textvariable=self._status_var,
                                      font=("Segoe UI", 9),
                                      bg=COLORS["bg"], fg=COLORS["text_hint"])
        self._status_label.pack(side=tk.RIGHT, padx=(0, 12))

        # 状态指示灯
        self._dot_canvas = tk.Canvas(bar, width=10, height=10,
                                     bg=COLORS["bg"], highlightthickness=0)
        self._dot_canvas.pack(side=tk.RIGHT, padx=(0, 4))
        self._draw_dot(COLORS["success"])

    def _draw_dot(self, color):
        self._dot_canvas.delete("all")
        self._dot_canvas.create_oval(1, 1, 9, 9, fill=color, outline="")

    def _build_log_area(self, parent):
        """日志输出区域"""
        tk.Label(parent, text="📋 输出日志", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(6, 3))

        self._log = scrolledtext.ScrolledText(
            parent, font=("Consolas", 10), bg="#ffffff",
            fg=COLORS["text"], insertbackground=COLORS["text"],
            relief=tk.FLAT, height=14, state=tk.DISABLED, wrap=tk.WORD,
            padx=10, pady=8,
        )
        self._log.pack(fill=tk.BOTH, expand=True)

        self._log.tag_configure("info", foreground="#374151")
        self._log.tag_configure("success", foreground="#16a34a")
        self._log.tag_configure("error", foreground="#dc2626")
        self._log.tag_configure("warn", foreground="#d97706")
        self._log.tag_configure("title", foreground="#2563eb",
                                font=("Consolas", 10, "bold"))
        self._log.tag_configure("dim", foreground="#9ca3af")

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

    def _on_path_change(self, *_):
        path = self.path_var.get()
        if Path(path).is_dir():
            self._file_selector.set_files(path)

    def _validate(self) -> bool:
        repo = self.repo_var.get().strip()
        if not repo or "/" not in repo:
            messagebox.showwarning("参数错误", "请填写仓库地址，格式: owner/repo")
            return False
        path = self.path_var.get().strip()
        if not path or not Path(path).is_dir():
            messagebox.showwarning("参数错误", "请选择有效的源码目录")
            return False
        if len(self._file_selector.get_all_files()) == 0:
            messagebox.showwarning("文件为空", "没有可上传的文件，请检查目录或手动添加文件")
            return False
        return True

    def _set_running(self, running: bool):
        self._is_running = running
        if running:
            self._upload_btn.configure(state=tk.DISABLED, bg=COLORS["border"])
            self._stop_btn.configure(state=tk.NORMAL)
            self._status_var.set("上传中…")
            self._draw_dot(COLORS["warn"])
        else:
            self._upload_btn.configure(state=tk.NORMAL, bg=COLORS["accent"])
            self._stop_btn.configure(state=tk.DISABLED)
            self._status_var.set("就绪")
            self._draw_dot(COLORS["success"])

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
        repo = self.repo_var.get().strip()
        path = self.path_var.get().strip()
        message = self.message_var.get().strip() or "Auto upload"
        branch = self.branch_var.get().strip() or "main"
        private = self.private_var.get()
        force = self.force_var.get()
        dry_run = self.dry_run_var.get()

        # 获取选中的文件
        all_files = self._file_selector.get_all_files()
        selected_files = self._file_selector.get_selected_files()
        total = len(all_files)
        sel = len(selected_files)

        self._log_write("=" * 56, "title")
        self._log_write(f"🚀 {self.APP_TITLE}", "title")
        self._log_write("=" * 56, "title")
        self._log_write(f"📦 仓库:       {repo}", "info")
        self._log_write(f"📁 路径:       {path}", "info")
        self._log_write(f"🌿 分支:       {branch}", "info")
        self._log_write(f"💬 提交信息:   {message}", "info")
        vis_text = "私有 🔒" if private else "公开 🌐"
        vis_tag = "warn" if private else "info"
        self._log_write(f"👁️  可见性:     {vis_text}", vis_tag)
        self._log_write(f"📄 文件统计:   {sel}/{total} 个文件将被上传", "info")
        self._log_write(f"⚡ 强制推送:   {'是' if force else '否'}", "info" if not force else "warn")
        self._log_write(f"👀 预览模式:   {'是' if dry_run else '否'}", "info" if not dry_run else "warn")
        self._log_write("-" * 56, "dim")

        if sel < total:
            self._log_write(f"📝 已选择 {sel}/{total} 个文件上传", "dim")

        try:
            uploader = SmartUpload(
                repo=repo, path=path, safe=True,
                preview_only=dry_run, force=force,
                private=private, branch=branch, message=message,
            )

            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                success = uploader.run()

            for line in buf.getvalue().splitlines():
                if "✅" in line or "成功" in line or "完成" in line:
                    self._log_write(line, "success")
                elif "❌" in line or "失败" in line or "错误" in line:
                    self._log_write(line, "error")
                elif "⚠️" in line:
                    self._log_write(line, "warn")
                else:
                    self._log_write(line, "info")

            self._log_write("-" * 56, "dim")
            if success:
                self._log_write("🎉 上传完成!", "success")
                self.root.after(0, lambda: self._draw_dot(COLORS["success"]))
            else:
                self._log_write("❌ 上传失败", "error")
                self.root.after(0, lambda: self._draw_dot(COLORS["error"]))

        except Exception as e:
            self._log_write(f"❌ 未预期的错误: {e}", "error")
            self.root.after(0, lambda: self._draw_dot(COLORS["error"]))

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
