# Auto Repo Push

自动化将源码上传到GitHub/AtomGit仓库的Python脚本。

## 功能特点

- **智能检测**：自动检测SSH配置、Git用户信息
- **自动配置**：自动设置远程仓库、初始化Git仓库
- **安全过滤**：自动排除敏感文件（.env、密钥、二进制文件等）
- **冲突处理**：智能处理合并冲突
- **进度显示**：实时显示上传进度和文件统计
- **错误处理**：完善的错误处理和故障排除建议

## 使用方法

### 基本用法
```bash
python github_upload.py --repo owner/repo --path ./source --message "上传源码"
```

### 参数说明
- `--repo`：GitHub/AtomGit仓库（格式：owner/repo）
- `--path`：源码路径（默认当前目录）
- `--message`：提交信息（默认："Auto upload"）
- `--branch`：分支名称（默认：main）
- `--force`：强制推送
- `--dry-run`：预览模式，不实际执行

### 示例
```bash
# 上传当前目录
python github_upload.py --repo myuser/myproject

# 上传指定目录
python github_upload.py --repo myuser/myproject --path /path/to/source

# 预览模式
python github_upload.py --repo myuser/myproject --dry-run
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

脚本会自动检测系统配置，也可以手动设置：

1. **SSH密钥**：确保已配置SSH密钥并添加到GitHub/AtomGit
2. **Git用户信息**：确保已配置`user.name`和`user.email`
3. **远程仓库**：脚本会自动配置，也可手动设置

## 安全特性

- 自动排除敏感文件：`.env`、`*.pem`、`*.key`、`id_rsa`等
- 自动排除系统文件：`.DS_Store`、`Thumbs.db`等
- 自动排除Git文件：`.git/`、`.gitignore`等
- 提交频率限制：防止滥用API

## 故障排除

### 常见问题
1. **SSH密钥未加载**：运行`ssh-add ~/.ssh/id_ed25519`
2. **仓库不存在**：脚本会尝试自动创建
3. **权限不足**：确保有仓库的写入权限
4. **网络问题**：检查网络连接和防火墙设置

### 调试模式
```bash
python github_upload.py --repo owner/repo --verbose
```

## 许可证

MIT License