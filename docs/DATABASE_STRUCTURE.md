# 智能学习管理系统 - 数据库表结构详细说明

## 1. 核心表结构

### 1.1 用户相关表

#### UserProfile (用户扩展信息表)
| 字段名 | 数据类型 | 约束 | 描述 |
|-------|---------|------|------|
| id | Integer | Primary Key | 自增主键 |
| user | OneToOneField(User) | Foreign Key | 关联Django默认User表 |
| total_study_time | Float | Default: 0.0 | 累计学习时长（小时） |
| streak_days | Integer | Default: 0 | 连续学习天数 |
| avatar | ImageField | Blank, Null | 头像图片 |
| doll_image | ImageField | Blank, Null | 玩偶图片 |
| created_at | DateTimeField | Auto Now Add | 创建时间 |
| updated_at | DateTimeField | Auto Now | 更新时间 |

#### UserStudyStatus (用户学习状态表)
| 字段名 | 数据类型 | 约束 | 描述 |
|-------|---------|------|------|
| id | Integer | Primary Key | 自增主键 |
| user | OneToOneField(User) | Foreign Key | 关联Django默认User表 |
| template_completion_rate | Float | Default: 0.0 | 模板完成率(%) |
| cumulative_study_time | Float | Default: 0.0 | 累计学习时长(小时) |
| last_study_date | DateField | Null | 最后学习日期 |
| created_at | DateTimeField | Auto Now Add | 创建时间 |
| updated_at | DateTimeField | Auto Now | 更新时间 |

### 1.2 学习模板相关表

#### StudyTemplate (学习模板表)
| 字段名 | 数据类型 | 约束 | 描述 |
|-------|---------|------|------|
| id | Integer | Primary Key | 自增主键 |
| name | CharField(100) | Not Null | 模板名称（如：英语四级、考研数学） |
| description | TextField | Blank | 模板描述 |
| created_at | DateTimeField | Auto Now Add | 创建时间 |
| order | Integer | Default: 0 | 排序顺序 |
| is_example | BooleanField | Default: False | 是否为示例模板 |
| creator | ForeignKey(User) | Null, Blank | 创建者 |

#### TemplateModule (模板模块表)
| 字段名 | 数据类型 | 约束 | 描述 |
|-------|---------|------|------|
| id | Integer | Primary Key | 自增主键 |
| template | ForeignKey(StudyTemplate) | Foreign Key | 关联学习模板 |
| name | CharField(50) | Not Null | 模块名称（如：词汇、听力） |
| target_value | Integer | Null, Blank | 目标量(如100个/100分钟) |
| target_type | CharField(10) | Default: 'numeric' | 目标值类型（numeric/boolean/text） |
| color_code | CharField(7) | Default: "#81C784" | 展示颜色 |

### 1.3 学习进度相关表

#### DailyProgress (每日进度记录表)
| 字段名 | 数据类型 | 约束 | 描述 |
|-------|---------|------|------|
| id | Integer | Primary Key | 自增主键 |
| user | ForeignKey(User) | Foreign Key | 关联用户 |
| module | ForeignKey(TemplateModule) | Foreign Key | 关联模板模块 |
| actual_value | Integer | Default: 0 | 今日完成量 |
| actual_text | TextField | Null, Blank | 完成情况描述 |
| is_completed | BooleanField | Default: False | 是否完成 |
| date | DateField | Default: timezone.now | 记录日期 |
| created_at | DateTimeField | Default: timezone.now | 提交时间 |

#### StudySession (学习会话表)
| 字段名 | 数据类型 | 约束 | 描述 |
|-------|---------|------|------|
| id | Integer | Primary Key | 自增主键 |
| user | ForeignKey(User) | Foreign Key | 关联用户 |
| subject | CharField(100) | Not Null | 学习科目 |
| duration_minutes | Integer | Not Null | 学习时长(分钟) |
| notes | TextField | Null, Blank | 备注 |
| start_time | DateTimeField | Auto Now Add | 开始时间 |

### 1.4 学习资料相关表

#### LearningMaterial (学习资料表)
| 字段名 | 数据类型 | 约束 | 描述 |
|-------|---------|------|------|
| id | Integer | Primary Key | 自增主键 |
| module | ForeignKey(TemplateModule) | Foreign Key | 关联模板模块 |
| section_name | CharField(100) | Not Null | 章节名称 |
| chapter_names | TextField | Not Null | 章节列表（JSON格式） |
| content | TextField | Not Null | 资料内容 |
| generate_type | CharField(20) | Default: 'detailed' | 生成类型 |
| generated_at | DateTimeField | Auto Now Add | 生成时间 |

### 1.5 AI对话相关表

#### AIChatHistory (AI对话历史表)
| 字段名 | 数据类型 | 约束 | 描述 |
|-------|---------|------|------|
| id | Integer | Primary Key | 自增主键 |
| user | ForeignKey(User) | Foreign Key | 关联用户 |
| chat_name | CharField(100) | Default: '新对话' | 对话名称 |
| created_at | DateTimeField | Auto Now Add | 创建时间 |
| updated_at | DateTimeField | Auto Now | 更新时间 |

#### AIChatMessage (AI对话消息表)
| 字段名 | 数据类型 | 约束 | 描述 |
|-------|---------|------|------|
| id | Integer | Primary Key | 自增主键 |
| chat_history | ForeignKey(AIChatHistory) | Foreign Key | 关联对话历史 |
| role | CharField(20) | Not Null | 角色（user/assistant） |
| content | TextField | Not Null | 消息内容 |
| created_at | DateTimeField | Auto Now Add | 创建时间 |

### 1.6 待办事项表

#### TodoTask (待办事项表)
| 字段名 | 数据类型 | 约束 | 描述 |
|-------|---------|------|------|
| id | Integer | Primary Key | 自增主键 |
| user | ForeignKey(User) | Foreign Key | 关联用户 |
| content | TextField | Not Null | 任务内容 |
| is_done | BooleanField | Default: False | 是否完成 |
| priority | Integer | Default: 0 | 优先级 |
| created_at | DateTimeField | Auto Now Add | 创建时间 |
| updated_at | DateTimeField | Auto Now | 更新时间 |

## 2. 表关系图

```
┌─────────────────┐      ┌────────────────────┐      ┌─────────────────────┐
│    User        │      │  UserProfile       │      │ UserStudyStatus     │
├─────────────────┤      ├────────────────────┤      ├─────────────────────┤
│ id             │<─────┤ user               │      │ user                │
│ username       │      │ total_study_time   │      │ template_completion │
│ email          │      │ streak_days        │      │ cumulative_study_time│
│ password       │      │ avatar             │      └─────────────────────┘
└─────────────────┘      └────────────────────┘
        │                        │
        │                        │
        ▼                        ▼
┌─────────────────┐      ┌────────────────────┐
│  StudyTemplate  │      │  DailyProgress     │
├─────────────────┤      ├────────────────────┤
│ id             │      │ user               │
│ name           │      │ module             │
│ description    │      │ actual_value       │
│ creator        │<─────┤                    │
└─────────────────┘      └────────────────────┘
        │
        │
        ▼
┌─────────────────┐
│ TemplateModule  │
├─────────────────┤
│ id             │
│ template       │
│ name           │
│ target_value   │
│ target_type    │
└─────────────────┘
        │
        │
        ▼
┌─────────────────┐
│ LearningMaterial│
├─────────────────┤
│ id             │
│ module         │
│ content        │
│ generate_type  │
└─────────────────┘
```

## 3. 数据流程

1. **用户认证流程**：用户注册 → 创建UserProfile和UserStudyStatus → 登录 → 访问系统
2. **模板管理流程**：创建/编辑学习模板 → 添加模块 → 设置目标值和类型
3. **进度跟踪流程**：选择模板 → 填写每日进度 → 提交 → 更新UserStudyStatus → 生成统计数据
4. **AI功能流程**：输入学科信息 → AI生成学习模板 → 选择模块 → AI生成学习资料
5. **专注计时流程**：开始计时 → 结束计时 → 记录StudySession → 更新累计学习时长
6. **待办事项流程**：添加任务 → 完成任务 → 标记状态

## 4. 数据完整性保障

1. **外键约束**：所有关联表都使用外键约束，确保数据一致性
2. **默认值**：关键字段设置合理默认值，确保数据完整性
3. **数据验证**：在视图层实现数据验证，确保输入数据的合法性
4. **事务处理**：重要操作使用事务，确保数据操作的原子性
5. **缓存机制**：使用Django缓存减少数据库查询，提高性能

## 5. 性能优化考虑

1. **索引优化**：为常用查询字段添加索引
2. **缓存策略**：使用LocMemCache缓存热点数据
3. **查询优化**：使用select_related和prefetch_related减少数据库查询次数
4. **分页处理**：对大量数据使用分页，减少内存占用
5. **异步处理**：AI生成等耗时操作考虑使用异步处理