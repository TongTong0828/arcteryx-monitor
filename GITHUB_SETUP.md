# GitHub 设置和推送指南 📦

## 🎯 方案选择

### 方案 A：GitHub（推荐 - 公开或私有仓库）
- ✅ 免费私有仓库
- ✅ 完整的版本控制
- ✅ 方便团队协作

### 方案 B：GitLab
- ✅ 更多免费 CI/CD 分钟数
- ✅ 私有仓库无限制

### 方案 C：Bitbucket
- ✅ 与 Jira 集成好
- ✅ 小团队免费

---

## 📋 GitHub 快速设置（5分钟）

### 步骤 1：创建 GitHub 仓库

1. **访问** https://github.com/new
2. **填写信息**：
   - Repository name: `arcteryx-monitor`
   - Description: `Arc'teryx Outlet 商品监控系统 - 自动监控新商品和价格变化`
   - 选择 **Private**（推荐，避免暴露您的监控策略）或 Public
   - **不要**勾选 "Initialize with README"（我们已经有了）
3. **点击** "Create repository"

### 步骤 2：推送代码到 GitHub

在本地终端运行（GitHub 会显示这些命令）：

```bash
cd /Users/at/Desktop/ARC

# 添加远程仓库
git remote add origin https://github.com/你的用户名/arcteryx-monitor.git

# 或使用 SSH（推荐）
git remote add origin git@github.com:你的用户名/arcteryx-monitor.git

# 推送代码
git branch -M main
git push -u origin main
```

### 步骤 3：设置 GitHub Token（如果使用 HTTPS）

**如果推送时要求输入密码：**

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限：`repo` (完整仓库访问)
4. 生成并**复制** token
5. 推送时使用 token 作为密码

---

## 🚀 从 GitHub 部署到 AWS

### 方式 1：使用改进的部署脚本（推荐）

```bash
# 在本地 Mac 运行
./deploy_from_git.sh \
  https://github.com/你的用户名/arcteryx-monitor.git \
  54.123.45.67 \
  ~/Downloads/your-key.pem
```

这会：
1. ✅ 连接到 EC2
2. ✅ 从 GitHub 克隆代码
3. ✅ 安装所有依赖
4. ✅ 配置环境
5. ✅ 设置定时任务

### 方式 2：在 EC2 上手动克隆

```bash
# 1. SSH 到 EC2
ssh -i ~/Downloads/your-key.pem ec2-user@54.123.45.67

# 2. 克隆仓库
git clone https://github.com/你的用户名/arcteryx-monitor.git
cd arcteryx-monitor

# 3. 运行安装脚本
./setup.sh

# 4. 测试运行
./run.sh

# 5. 设置 Cron
crontab -e
# 添加: */30 * * * * cd $HOME/arcteryx-monitor && ./run.sh >> logs/monitor.log 2>&1
```

---

## 🔄 后续更新流程

### 在本地修改代码后

```bash
cd /Users/at/Desktop/ARC

# 查看修改
git status

# 添加修改
git add .

# 提交
git commit -m "描述你的修改"

# 推送到 GitHub
git push
```

### 在 EC2 上更新代码

```bash
# SSH 到 EC2
ssh -i ~/Downloads/your-key.pem ec2-user@54.123.45.67

# 进入项目目录
cd ~/arcteryx-monitor

# 拉取最新代码
git pull

# 如果有新的依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启（Cron 会自动使用新代码）
```

---

## 🔐 安全最佳实践

### ⚠️ 绝对不要提交的文件

```bash
# 这些文件已经在 .gitignore 中
.env              # 环境变量（邮箱密码等）
*.pem             # AWS 密钥
*.key             # 私钥
data/             # 商品数据
logs/             # 日志文件
```

### ✅ 检查是否泄露敏感信息

```bash
# 查看即将提交的文件
git status

# 查看文件内容
git diff

# 如果不小心添加了敏感文件
git rm --cached .env
git commit -m "Remove sensitive file"
```

### 🔒 使用私有仓库

**强烈建议**使用私有仓库，因为：
- ❌ 公开仓库会暴露您的监控策略
- ❌ 可能被竞争对手利用
- ❌ 其他人可能复制您的配置

---

## 🎁 GitHub Actions 自动部署（进阶）

### 创建 `.github/workflows/deploy.yml`

```yaml
name: Deploy to AWS

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to EC2
      env:
        PRIVATE_KEY: ${{ secrets.EC2_SSH_KEY }}
        HOST: ${{ secrets.EC2_HOST }}
        USER: ${{ secrets.EC2_USER }}
      run: |
        echo "$PRIVATE_KEY" > private_key.pem
        chmod 600 private_key.pem
        ssh -o StrictHostKeyChecking=no -i private_key.pem ${USER}@${HOST} '
          cd ~/arcteryx-monitor
          git pull
          source venv/bin/activate
          pip install -r requirements.txt
        '
```

### 在 GitHub 设置 Secrets

1. 仓库 → Settings → Secrets and variables → Actions
2. 添加：
   - `EC2_SSH_KEY`: 您的 .pem 文件内容
   - `EC2_HOST`: EC2 IP 地址
   - `EC2_USER`: `ec2-user` 或 `ubuntu`

现在每次推送代码，GitHub Actions 会自动部署到 EC2！

---

## 🌿 Git 分支策略

### 简单项目（推荐）

```bash
# 只用 main 分支
git checkout main
# 修改代码
git commit -m "Update"
git push
```

### 复杂项目

```bash
# 创建开发分支
git checkout -b develop

# 开发新功能
git checkout -b feature/email-notification

# 完成后合并
git checkout develop
git merge feature/email-notification

# 测试通过后合并到 main
git checkout main
git merge develop
git push
```

---

## 📊 常用 Git 命令

```bash
# 查看状态
git status

# 查看历史
git log --oneline

# 查看差异
git diff

# 撤销修改
git checkout -- file.py

# 回退提交
git reset --soft HEAD~1

# 查看远程仓库
git remote -v

# 删除远程分支
git push origin --delete branch-name

# 清理未跟踪文件
git clean -fd
```

---

## 🔍 故障排查

### 推送失败：认证错误

```bash
# 使用 SSH 代替 HTTPS
git remote set-url origin git@github.com:username/arcteryx-monitor.git

# 或配置 Git 凭证
git config --global credential.helper store
```

### 推送失败：文件太大

```bash
# 检查大文件
du -sh * | sort -h

# 从 Git 历史中删除大文件
git filter-branch --tree-filter 'rm -rf path/to/large/file' HEAD
```

### 合并冲突

```bash
# 拉取最新代码
git pull

# 手动解决冲突后
git add .
git commit
git push
```

---

## 📚 参考资源

- [GitHub 官方文档](https://docs.github.com/)
- [Git 教程](https://git-scm.com/book/zh/v2)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [生成 SSH 密钥](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

---

## ✅ 完成检查清单

- [ ] 创建 GitHub 仓库
- [ ] 推送代码到 GitHub
- [ ] 设置为私有仓库
- [ ] 在 EC2 上克隆代码
- [ ] 测试运行成功
- [ ] 设置 Cron 定时任务
- [ ] （可选）配置 GitHub Actions 自动部署

---

**恭喜！您的代码现在托管在 GitHub，可以轻松部署到 AWS 了！** 🎉

