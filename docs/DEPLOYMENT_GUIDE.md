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

# API 配置（AI 功能必需）
MODELSCOPE_API_KEY=你的ModelScope API密钥
MODELSCOPE_API_URL=https://api-inference.modelscope.cn/v1/chat/completions
MODELSCOPE_MODEL=Qwen/Qwen3-VL-8B-Instruct
```

> **注意**：`.env` 文件已在 `.gitignore` 中排除，不会被提交到 Git，确保密码安全。

### 4.1.1 AI 模型配置说明

项目默认使用 **Qwen/Qwen3-VL-8B-Instruct** 模型，但也支持其他兼容 OpenAI Chat Completions 格式的模型。

#### ModelScope 支持的模型（部分）

| 模型名称 | 模型 ID | 说明 |
|---------|---------|------|
| Qwen3-VL-8B-Instruct | `Qwen/Qwen3-VL-8B-Instruct` | 多模态模型，支持图文理解（默认） |
| Qwen3-7B-Instruct | `Qwen/Qwen3-7B-Instruct` | 纯文本模型，响应更快 |
| Qwen2-7B-Instruct | `Qwen/Qwen2-7B-Instruct` | Qwen2 系列文本模型 |
| Qwen-7B-Chat | `Qwen/Qwen-7B-Chat` | Qwen 原始系列 |

#### 使用其他模型的方法

如需更换模型，只需修改 `.env` 文件中的 `MODELSCOPE_MODEL`：

```ini
# 使用纯文本模型（响应更快）
MODELSCOPE_MODEL=Qwen/Qwen3-7B-Instruct

# 使用 Qwen2 系列
MODELSCOPE_MODEL=Qwen/Qwen2-7B-Instruct
```

#### 使用其他 API 服务

项目采用 **OpenAI 兼容接口**，理论上支持任何兼容 OpenAI Chat Completions 格式的 API：

| 平台 | API URL | 说明 |
|------|---------|------|
| ModelScope | `https://api-inference.modelscope.cn/v1/chat/completions` | 默认 |
| OpenAI | `https://api.openai.com/v1/chat/completions` | 需要 OpenAI API Key |
| DeepSeek | `https://api.deepseek.com/v1/chat/completions` | 需要 DeepSeek API Key |

如需切换到其他平台，修改 `.env`：

```ini
# 示例：使用 OpenAI API
MODELSCOPE_API_URL=https://api.openai.com/v1/chat/completions
MODELSCOPE_API_KEY=sk-your-openai-api-key
MODELSCOPE_MODEL=gpt-4o-mini
```

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

### 8.5 AI API 认证失败（401 错误）

**问题**：AI 生成模板、AI 对话等功能返回 `Authentication failed`

**原因**：使用了无效或过期的 ModelScope API Key

**解决方案**：
1. 登录 [ModelScope 控制台](https://modelscope.cn/)
2. 检查 Token 是否有效，必要时重新生成
3. 更新 `.env` 文件中的 `MODELSCOPE_API_KEY`
4. **重启开发服务器**（关键步骤，见 8.6）

### 8.6 更新 .env 后配置不生效

**问题**：修改了 `.env` 文件，但开发服务器仍使用旧配置

**原因**：`load_dotenv()` 默认不会覆盖进程中已加载的环境变量。服务器启动时读取了旧配置，后续修改 `.env` 不会自动生效。

**解决方案**：
```bash
# 必须重启开发服务器才能加载新配置
Ctrl+C  # 停止当前服务器
python manage.py runserver  # 重新启动
```

### 8.7 AI 功能报错"请检查网络连接"

**问题**：AI 生成模板时提示"请检查网络连接"

**原因**：通常不是网络问题，而是 API Key 无效或服务器未加载最新配置

**解决方案**：
1. 确认 `.env` 中的 `MODELSCOPE_API_KEY` 是有效的
2. 重启开发服务器
3. 如果仍失败，检查页面上显示的具体 API 错误信息

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