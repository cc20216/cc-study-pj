# 项目部署指南

本指南用于在第二台电脑上部署学习管理系统项目。

## 1. 环境准备

### 1.1 安装必要软件

1. **Python 3.7.9**
   - 下载链接：https://www.python.org/downloads/release/python-379/
   - 安装时勾选 "Add Python to PATH"

2. **MySQL 5.7+ 或 8.0**
   - 下载链接：https://dev.mysql.com/downloads/mysql/
   - 安装时设置 root 密码（后续需要使用）

3. **Git**（可选，用于代码获取）
   - 下载链接：https://git-scm.com/downloads

### 1.2 检查环境

在命令行中执行以下命令检查环境：

```bash
# 检查 Python 版本
python --version

# 检查 pip 版本
pip --version

# 检查 MySQL 是否运行（Windows）
net start MySQL80
```

## 2. 代码获取

### 2.1 方法一：通过 Git 克隆

```bash
git clone <项目仓库地址>
cd dbstudy
```

### 2.2 方法二：通过文件传输

1. 将整个 `dbstudy` 文件夹复制到第二台电脑
2. 在目标电脑上解压（如果是压缩文件）

## 3. 依赖安装

### 3.1 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 激活虚拟环境（Linux/Mac）
source venv/bin/activate
```

### 3.2 安装依赖

```bash
# 进入项目根目录
cd dbstudy

# 安装依赖
pip install -r requirements.txt
```

## 4. 数据库配置

### 4.1 配置环境变量

项目使用 `.env` 文件管理敏感配置，**不要直接修改 settings.py**。

首先，复制环境变量模板并填入你的配置：

```bash
# 复制模板
cp .env.example .env
```

然后编辑 `.env` 文件，修改以下内容：

```ini
# .env 文件内容
SECRET_KEY=your-random-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# 数据库配置（替换为你的 MySQL 信息）
DB_NAME=dbstudy_db
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_HOST=127.0.0.1
DB_PORT=3306

# API 配置
MODELSCOPE_API_KEY=你的ModelScope API密钥
```

> **注意**：`.env` 文件已在 `.gitignore` 中排除，不会被提交到 Git，确保密码安全。

### 4.2 创建数据库

在 MySQL 中执行以下 SQL 语句：

```sql
CREATE DATABASE dbstudy_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 5. 数据库迁移

执行以下命令进行数据库迁移：

```bash
# 进入 study 目录
cd study

# 生成迁移文件
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 创建超级用户（可选）
python manage.py createsuperuser
```

## 6. 静态文件配置

确保 `settings.py` 中的静态文件配置正确：

```python
# 静态文件配置
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # 根目录的static

# 媒体文件配置
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

## 7. 运行项目

```bash
# 进入 study 目录
cd study

# 启动开发服务器
python manage.py runserver
```

项目将在 http://127.0.0.1:8000/ 运行。

## 8. 常见问题及解决方案

### 8.1 数据库连接错误

**问题**：`OperationalError: (2003, "Can't connect to MySQL server on '127.0.0.1' ([WinError 10061] 由于目标计算机积极拒绝，无法连接。)")`

**解决方案**：
- 检查 MySQL 服务是否启动
- 检查数据库连接信息是否正确
- 确保 MySQL 允许本地连接

### 8.2 依赖安装错误

**问题**：`ModuleNotFoundError: No module named 'requests'`

**解决方案**：
- 确保虚拟环境已激活
- 重新执行 `pip install -r requirements.txt`
- 检查网络连接是否正常

### 8.3 静态文件无法访问

**问题**：CSS、JS 等静态文件无法加载

**解决方案**：
- 确保 `STATICFILES_DIRS` 配置正确
- 确保静态文件目录存在且包含所需文件
- 尝试执行 `python manage.py collectstatic`（生产环境）

### 8.4 媒体文件上传错误

**问题**：用户上传的图片无法保存

**解决方案**：
- 确保 `MEDIA_ROOT` 目录存在
- 确保目录有写入权限
- 检查 `MEDIA_URL` 配置是否正确

## 9. 项目结构说明

```
dbstudy/
├── study/                # 主项目目录
│   ├── study/            # 项目配置目录
│   │   ├── settings.py   # 项目配置文件
│   │   ├── urls.py       # URL路由配置
│   │   └── ...
│   ├── study_dashboard/  # 核心功能应用
│   │   ├── models.py     # 数据库模型
│   │   ├── views.py      # 视图函数
│   │   └── ...
│   └── manage.py         # 项目管理脚本
├── templates/            # 模板文件目录
├── static/               # 静态文件目录
├── media/                # 媒体文件目录
├── requirements.txt      # 依赖文件
└── DEPLOYMENT_GUIDE.md   # 部署指南
```

## 10. 后续维护

### 10.1 代码更新

当代码更新后，执行以下步骤：

1. 拉取最新代码
2. 激活虚拟环境
3. 安装新依赖（如果有）
4. 执行数据库迁移
5. 重启服务器

### 10.2 定期备份

建议定期备份：
- 数据库数据
- 媒体文件
- 重要配置文件

## 11. 部署完成验证

部署完成后，访问 http://127.0.0.1:8000/ 验证：

1. **首页**：检查是否正常加载
2. **注册/登录**：测试用户注册和登录功能
3. **学习模板**：查看和创建学习模板
4. **进度记录**：测试进度记录功能
5. **AI对话**：测试AI对话功能

如果所有功能正常，说明部署成功！

---

**注意**：本指南适用于开发环境部署。生产环境部署需要额外的配置和安全措施。