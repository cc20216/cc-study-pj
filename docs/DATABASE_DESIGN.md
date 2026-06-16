# 智能学习管理系统 - 数据库设计

## 1. 完整E-R图

```
+---------------+       +----------------+       +-------------------+
|   User        |       |  UserProfile   |       | UserStudyStatus   |
+---------------+       +----------------+       +-------------------+
| - id (PK)     |<----->| - user_id (PK) |<----->| - user_id (PK)    |
| - username    |       | - avatar       |       | - cumulative_time |
| - password    |       | - total_time   |       | - completion_rate |
| - email       |       | - streak_days  |       | - last_updated    |
+---------------+       +----------------+       +-------------------+
        |                         |
        |                         |
        v                         v
+----------------+       +-------------------+
| StudyTemplate  |<----->|  StudySession    |
+----------------+       +-------------------+
| - id (PK)      |       | - id (PK)        |
| - name         |       | - user_id (FK)   |
| - description  |       | - subject        |
| - created_at   |       | - duration       |
| - order        |       | - notes          |
| - is_example   |       | - start_time     |
| - creator_id (FK) |    +-------------------+
+----------------+              |
        |                       |
        v                       v
+----------------+       +-------------------+
| TemplateModule |<----->|  DailyProgress   |
+----------------+       +-------------------+
| - id (PK)      |       | - id (PK)        |
| - template_id (FK) |   | - user_id (FK)   |
| - name         |       | - module_id (FK) |
| - target_value |       | - actual_value   |
| - target_type  |       | - actual_text    |
| - color_code   |       | - is_completed   |
+----------------+       | - date           |
        |               | - created_at     |
        v               +-------------------+
+----------------+       
| LearningMaterial |      
+----------------+       
| - id (PK)      |       
| - module_id (FK) |      
| - section_name |       
| - chapter_names |      
| - content      |       
| - generate_type |      
| - generated_at |       
+----------------+       
        |
        v
+----------------+       +-------------------+
| AIChatHistory  |<----->|  AIChatMessage   |
+----------------+       +-------------------+
| - id (PK)      |       | - id (PK)        |
| - user_id (FK) |       | - chat_id (FK)   |
| - chat_name    |       | - role           |
| - created_at   |       | - content        |
| - updated_at   |       | - created_at     |
+----------------+       +-------------------+
```

## 2. 详细数据字典

### 2.1 User (Django内置)
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| id | Integer | PRIMARY KEY | 自增 | 用户ID | 主键索引 |
| username | CharField(150) | UNIQUE | 无 | 用户名 | 唯一索引 |
| password | CharField(128) | 无 | 无 | 密码哈希 | 无 |
| email | EmailField(254) | 无 | 无 | 邮箱 | 无 |
| first_name | CharField(150) | 无 | 空 | 名 | 无 |
| last_name | CharField(150) | 无 | 空 | 姓 | 无 |
| is_active | BooleanField | 无 | True | 是否激活 | 无 |
| is_staff | BooleanField | 无 | False | 是否为员工 | 无 |
| is_superuser | BooleanField | 无 | False | 是否为超级用户 | 无 |
| last_login | DateTimeField | 无 | 空 | 最后登录时间 | 无 |
| date_joined | DateTimeField | 无 | auto_now_add | 注册时间 | 无 |

### 2.2 UserProfile
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| user | OneToOneField(User) | PRIMARY KEY | 无 | 关联用户 | 主键索引 |
| avatar | ImageField | 无 | 空 | 头像 | 无 |
| doll_image | ImageField | 无 | 空 | 自定义玩偶图片 | 无 |
| total_study_time | FloatField | 无 | 0.0 | 累计学习时长(h) | 无 |
| streak_days | IntegerField | 无 | 0 | 连续学习天数 | 无 |

### 2.3 UserStudyStatus
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| user | OneToOneField(User) | PRIMARY KEY | 无 | 关联用户 | 主键索引 |
| cumulative_study_time | FloatField | 无 | 0.0 | 累计学习时长(h) | 无 |
| template_completion_rate | FloatField | 无 | 0.0 | 模板完成率(%) | 无 |
| last_updated | DateTimeField | 无 | auto_now | 最后更新时间 | 无 |

### 2.4 StudyTemplate
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| id | Integer | PRIMARY KEY | 自增 | 模板ID | 主键索引 |
| name | CharField(100) | 无 | 无 | 模板名称 | 无 |
| description | TextField | 无 | 空 | 描述 | 无 |
| created_at | DateTimeField | 无 | auto_now_add | 创建时间 | 无 |
| order | IntegerField | 无 | 0 | 排序顺序 | 无 |
| is_example | BooleanField | 无 | False | 是否为示例模板 | 无 |
| creator | ForeignKey(User) | 无 | NULL | 创建者 | 外键索引 |

### 2.5 TemplateModule
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| id | Integer | PRIMARY KEY | 自增 | 模块ID | 主键索引 |
| template | ForeignKey(StudyTemplate) | 无 | 无 | 关联模板 | 外键索引 |
| name | CharField(50) | 无 | 无 | 模块名称 | 无 |
| target_value | IntegerField | 无 | NULL | 目标量 | 无 |
| target_type | CharField(10) | 无 | 'numeric' | 目标值类型 | 无 |
| color_code | CharField(7) | 无 | '#81C784' | 展示颜色 | 无 |

### 2.6 DailyProgress
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| id | Integer | PRIMARY KEY | 自增 | 进度ID | 主键索引 |
| user | ForeignKey(User) | 无 | 无 | 关联用户 | 外键索引 |
| module | ForeignKey(TemplateModule) | 无 | 无 | 关联模块 | 外键索引 |
| actual_value | IntegerField | 无 | 0 | 今日完成量 | 无 |
| actual_text | TextField | 无 | NULL | 完成情况描述 | 无 |
| is_completed | BooleanField | 无 | False | 是否完成 | 无 |
| date | DateField | 无 | timezone.now | 日期 | 无 |
| created_at | DateTimeField | 无 | timezone.now | 提交时间 | 无 |

### 2.7 StudySession
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| id | Integer | PRIMARY KEY | 自增 | 会话ID | 主键索引 |
| user | ForeignKey(User) | 无 | 无 | 关联用户 | 外键索引 |
| subject | CharField(100) | 无 | 无 | 学习科目 | 无 |
| duration_minutes | IntegerField | 无 | 无 | 学习时长(分钟) | 无 |
| notes | TextField | 无 | NULL | 备注 | 无 |
| start_time | DateTimeField | 无 | auto_now_add | 开始时间 | 无 |

### 2.8 TodoTask
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| id | Integer | PRIMARY KEY | 自增 | 任务ID | 主键索引 |
| user | ForeignKey(User) | 无 | 无 | 关联用户 | 外键索引 |
| content | CharField(200) | 无 | 无 | 任务内容 | 无 |
| priority | CharField(1) | 无 | 'M' | 优先级 | 无 |
| is_done | BooleanField | 无 | False | 是否完成 | 无 |
| created_at | DateField | 无 | auto_now_add | 创建时间 | 无 |

### 2.9 LearningMaterial
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| id | Integer | PRIMARY KEY | 自增 | 资料ID | 主键索引 |
| module | ForeignKey(TemplateModule) | 无 | 无 | 关联模块 | 外键索引 |
| section_name | CharField(100) | 无 | 无 | 板块名称 | 无 |
| chapter_names | TextField | 无 | 无 | 章节名称列表 | 无 |
| content | TextField | 无 | 无 | 学习资料内容 | 无 |
| generate_type | CharField(10) | 无 | 'simple' | 生成类型 | 无 |
| generated_at | DateTimeField | 无 | auto_now_add | 生成时间 | 无 |

### 2.10 AIChatHistory
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| id | Integer | PRIMARY KEY | 自增 | 对话ID | 主键索引 |
| user | ForeignKey(User) | 无 | 无 | 关联用户 | 外键索引 |
| chat_name | CharField(100) | 无 | '新对话' | 对话名称 | 无 |
| created_at | DateTimeField | 无 | auto_now_add | 创建时间 | 无 |
| updated_at | DateTimeField | 无 | auto_now | 更新时间 | 无 |

### 2.11 AIChatMessage
| 字段名 | 数据类型 | 约束 | 默认值 | 描述 | 索引 |
|--------|---------|------|--------|------|------|
| id | Integer | PRIMARY KEY | 自增 | 消息ID | 主键索引 |
| chat_history | ForeignKey(AIChatHistory) | 无 | 无 | 关联对话 | 外键索引 |
| role | CharField(10) | 无 | 无 | 消息角色 | 无 |
| content | TextField | 无 | 无 | 消息内容 | 无 |
| created_at | DateTimeField | 无 | auto_now_add | 发送时间 | 无 |

## 3. 数据库迁移脚本

### 3.1 初始迁移 (0001_initial.py)
- 创建UserProfile、StudyTemplate、TemplateModule、DailyProgress、StudySession、TodoTask模型

### 3.2 后续迁移
- **0002_userstudystatus.py**：添加UserStudyStatus模型
- **0003_userprofile_doll_image.py**：为UserProfile添加doll_image字段
- **0004_alter_studytemplate_options_studytemplate_order.py**：为StudyTemplate添加order字段
- **0005_auto_20260103_1557.py**：自动迁移
- **0006_auto_20260103_2215.py**：自动迁移
- **0007_auto_20260103_2351.py**：自动迁移
- **0008_learningmaterial.py**：添加LearningMaterial模型
- **0009_aichathistory_aichatmessage.py**：添加AIChatHistory和AIChatMessage模型
- **0010_auto_20260113_1545.py**：自动迁移

### 3.3 迁移命令
```bash
# 生成迁移文件
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 查看迁移状态
python manage.py showmigrations
```