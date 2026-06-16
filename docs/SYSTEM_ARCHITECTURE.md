# 智能学习管理系统 - 系统架构设计

## 1. 系统架构图

```
+------------------------+
|        前端层           |
+------------------------+
|  HTML/CSS/JavaScript   |
|  Chart.js (数据可视化)  |
|  Lucide Icons (图标库)  |
+------------------------+
            |
            v
+------------------------+
|        后端层           |
+------------------------+
|  Django 4.x (MVT架构)   |
|  视图函数 (views.py)    |
|  模型 (models.py)       |
|  模板 (templates/)      |
+------------------------+
            |
            v
+------------------------+
|        数据层           |
+------------------------+
|  MySQL 8.0+             |
|  数据模型存储           |
|  关系型数据库           |
+------------------------+
            |
            v
+------------------------+
|        AI模块           |
+------------------------+
|  ai_generator.py (AI生成) |
|  MultiSubjectAIGenerator  |
|  学习资料生成           |
+------------------------+
```

## 2. 技术栈详细配置

### 2.1 Django配置
- **版本**：Django 3.2.25
- **核心配置**：
  - SECRET_KEY: 从 .env 环境变量读取（不硬编码在代码中）
  - DEBUG: 从 .env 环境变量读取
  - ALLOWED_HOSTS: 从 .env 环境变量读取，逗号分隔
  - INSTALLED_APPS: ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'study_dashboard']
  - MIDDLEWARE: 包含CSRF保护、认证中间件等
  - TEMPLATES: 根目录templates文件夹
  - STATIC_URL: 'static/'
  - STATICFILES_DIRS: [os.path.join(BASE_DIR, 'static')]
  - MEDIA_URL: 'media/'
  - MEDIA_ROOT: os.path.join(BASE_DIR, 'media')

### 2.2 MySQL配置
- **版本**：MySQL 8.0+
- **配置参数**：
  - ENGINE: 'django.db.backends.mysql'
  - NAME: 'dbstudy_db'
  - USER: 'root'
  - PASSWORD: 从 .env 环境变量读取（不硬编码在代码中）
  - HOST: '127.0.0.1'
  - PORT: '3306'
  - OPTIONS: {'charset': 'utf8mb4'}

### 2.3 前端技术
- **Chart.js**：最新版本，用于数据可视化
- **Lucide Icons**：最新版本，用于图标展示
- **CSS Grid/Flexbox**：用于响应式布局
- **JavaScript**：用于前端交互和AJAX调用

## 3. 部署架构图

### 3.1 开发环境
```
+------------------------+
|  本地开发环境           |
+------------------------+
|  Windows 10/11         |
|  Python 3.7.9          |
|  Django 3.2.25         |
|  MySQL 8.0+            |
|  VS Code               |
+------------------------+
|  开发服务器 (runserver) |
+------------------------+
```

### 3.2 生产环境
```
+------------------------+
|  生产服务器             |
+------------------------+
|  Linux (Ubuntu 20.04+)  |
|  Python 3.7+            |
|  Django 3.2.25          |
|  MySQL 8.0+             |
|  Nginx (反向代理)        |
|  Gunicorn (WSGI服务器)   |
+------------------------+
|  静态文件CDN (可选)      |
+------------------------+
```

### 3.3 环境差异对比
| 配置项 | 开发环境 | 生产环境 |
|--------|---------|---------|
| 服务器 | Django开发服务器 | Nginx + Gunicorn |
| DEBUG模式 | True | False |
| 数据库 | 本地MySQL | 生产MySQL |
| 静态文件 | 本地存储 | 可能使用CDN |
| 安全性 | 较低 | 较高（HTTPS、防火墙等） |
| 性能优化 | 未优化 | 已优化（缓存、压缩等） |