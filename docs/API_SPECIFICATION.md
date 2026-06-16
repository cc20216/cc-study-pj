# 智能学习管理系统 - API接口规范

## 1. 内部API文档

### 1.1 认证相关API
| 接口路径 | 方法 | 功能描述 | 请求参数 | 成功响应 | 失败响应 |
|---------|------|----------|---------|----------|----------|
| `/login/` | POST | 用户登录 | username: str, password: str | 重定向到首页 | 错误消息 |
| `/register/` | POST | 用户注册 | username: str, email: str, password1: str, password2: str | 重定向到登录页 | 错误消息 |
| `/logout/` | GET | 用户登出 | 无 | 重定向到登录页 | 无 |

### 1.2 任务管理API
| 接口路径 | 方法 | 功能描述 | 请求参数 | 成功响应 | 失败响应 |
|---------|------|----------|---------|----------|----------|
| `/todo/add/` | POST | 添加任务 | content: str, priority: str | JSON: {"success": true} | JSON: {"success": false, "error": "错误信息"} |
| `/todo/toggle/<int:todo_id>/` | GET | 切换任务状态 | todo_id: int | 重定向到首页 | 无 |
| `/todo/delete/<int:todo_id>/` | GET | 删除任务 | todo_id: int | 重定向到首页 | 无 |

### 1.3 模板管理API
| 接口路径 | 方法 | 功能描述 | 请求参数 | 成功响应 | 失败响应 |
|---------|------|----------|---------|----------|----------|
| `/template/management/` | GET | 模板管理页面 | 无 | 模板列表页面 | 无 |
| `/template/add/` | POST | 添加模板 | name: str, description: str | 重定向到模板管理页 | 错误消息 |
| `/template/edit/<int:template_id>/` | POST | 编辑模板 | name: str, description: str | 重定向到模板管理页 | 错误消息 |
| `/template/delete/<int:template_id>/` | GET | 删除模板 | template_id: int | 重定向到模板管理页 | 无 |
| `/update_template_order/` | POST | 更新模板顺序 | order_data: JSON | JSON: {"success": true} | JSON: {"success": false} |

### 1.4 模块管理API
| 接口路径 | 方法 | 功能描述 | 请求参数 | 成功响应 | 失败响应 |
|---------|------|----------|---------|----------|----------|
| `/module/add/<int:template_id>/` | POST | 添加模块 | name: str, target_value: int, target_type: str, color_code: str | 重定向到模板管理页 | 错误消息 |
| `/module/edit/<int:module_id>/` | POST | 编辑模块 | name: str, target_value: int, target_type: str, color_code: str | 重定向到模板管理页 | 错误消息 |
| `/module/delete/<int:module_id>/` | GET | 删除模块 | module_id: int | 重定向到模板管理页 | 无 |

### 1.5 AI生成API
| 接口路径 | 方法 | 功能描述 | 请求参数 | 成功响应 | 失败响应 |
|---------|------|----------|---------|----------|----------|
| `/template/generate_ai/` | GET | AI生成模板页面 | 无 | AI生成模板页面 | 无 |
| `/template/generate_ai/step1/` | POST | 生成模板步骤1 | subject: str, difficulty: str | 步骤2页面 | 错误消息 |
| `/template/generate_ai/step2/` | POST | 生成模板步骤2 | modules: JSON | 步骤3页面 | 错误消息 |
| `/template/generate_ai/step3/` | POST | 生成模板步骤3 | template_name: str | 重定向到模板管理页 | 错误消息 |
| `/template/generate_materials/` | POST | 生成学习资料 | module_id: int, generate_type: str | JSON: {"success": true, "material_id": int} | JSON: {"success": false, "error": "错误信息"} |
| `/module/<int:module_id>/materials/` | GET | 获取模块学习资料 | module_id: int | 学习资料页面 | 无 |

### 1.6 学习进度API
| 接口路径 | 方法 | 功能描述 | 请求参数 | 成功响应 | 失败响应 |
|---------|------|----------|---------|----------|----------|
| `/progress/daily/` | GET | 每日进度填写页面 | template_id: int (可选) | 进度填写页面 | 无 |
| `/progress/submit/` | POST | 提交每日进度 | template: int, learning_time: float, module_*: int/text, module_text_*: text | 重定向到进度看板 | 错误消息 |
| `/progress/dashboard/` | GET | 学习进度看板 | template_id: int (可选) | 进度看板页面 | 无 |

### 1.7 沉浸学习API
| 接口路径 | 方法 | 功能描述 | 请求参数 | 成功响应 | 失败响应 |
|---------|------|----------|---------|----------|----------|
| `/study/session/` | GET | 沉浸学习页面 | template_id: int (可选) | 学习计时页面 | 无 |
| `/study/session/end/` | POST | 结束学习会话 | duration: int, subject: str, notes: str | 学习总结页面 | 错误消息 |

### 1.8 学习内容API
| 接口路径 | 方法 | 功能描述 | 请求参数 | 成功响应 | 失败响应 |
|---------|------|----------|---------|----------|----------|
| `/cet4/study/(?P<module_name>[^/]+)?/` | GET | CET-4学习页面 | module_name: str (可选) | 学习页面 | 无 |
| `/cet4/materials/` | GET | CET-4学习资料 | 无 | 学习资料页面 | 无 |
| `/cet4/materials/<str:module_name>/` | GET | CET-4模块资料 | module_name: str | 学习资料页面 | 无 |
| `/c_language/study/(?P<module_name>[^/]+)?/` | GET | C语言学习页面 | module_name: str (可选) | 学习页面 | 无 |
| `/c_language/materials/` | GET | C语言学习资料 | 无 | 学习资料页面 | 无 |
| `/c_language/materials/<str:module_name>/` | GET | C语言模块资料 | module_name: str | 学习资料页面 | 无 |
| `/politics/study/(?P<module_name>[^/]+)?/` | GET | 政治学习页面 | module_name: str (可选) | 学习页面 | 无 |
| `/politics/materials/` | GET | 政治学习资料 | 无 | 学习资料页面 | 无 |
| `/politics/materials/<str:module_name>/` | GET | 政治模块资料 | module_name: str | 学习资料页面 | 无 |
| `/study/<int:template_id>/` | GET | 统一学习模板页面 | template_id: int | 学习页面 | 无 |
| `/study/<int:template_id>/<str:module_name>/` | GET | 统一学习模块页面 | template_id: int, module_name: str | 学习页面 | 无 |

### 1.9 AI对话API
| 接口路径 | 方法 | 功能描述 | 请求参数 | 成功响应 | 失败响应 |
|---------|------|----------|---------|----------|----------|
| `/ai/chat/` | GET | AI对话页面 | 无 | 对话页面 | 无 |
| `/ai/chat/create/` | POST | 创建对话 | 无 | JSON: {"chat_id": int} | JSON: {"error": "错误信息"} |
| `/ai/chat/send/` | POST | 发送消息 | chat_id: int, content: str | JSON: {"message": {"id": int, "content": str, "role": str, "created_at": str}} | JSON: {"error": "错误信息"} |
| `/ai/chat/messages/` | GET | 获取对话消息 | chat_id: int | JSON: {"messages": [{"id": int, "content": str, "role": str, "created_at": str}]} | JSON: {"error": "错误信息"} |
| `/ai/chat/rename/` | POST | 重命名对话 | chat_id: int, name: str | JSON: {"success": true} | JSON: {"error": "错误信息"} |
| `/ai/chat/delete/` | POST | 删除对话 | chat_id: int | JSON: {"success": true} | JSON: {"error": "错误信息"} |

### 1.10 数据导出API
| 接口路径 | 方法 | 功能描述 | 请求参数 | 成功响应 | 失败响应 |
|---------|------|----------|---------|----------|----------|
| `/export/study-data/` | GET | 导出学习数据 | 无 | CSV文件下载 | 无 |

## 2. 请求/响应格式标准

### 2.1 统一数据格式

#### 2.1.1 成功响应 (JSON)
```json
{
  "success": true,
  "data": {...},  // 具体数据
  "message": "操作成功"  // 可选
}
```

#### 2.1.2 失败响应 (JSON)
```json
{
  "success": false,
  "error": "错误信息",
  "code": 400  // 错误码
}
```

### 2.2 错误码规范
| 错误码 | 描述 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 2.3 数据类型规范
- **字符串**：使用双引号包围
- **数字**：直接表示，不使用引号
- **布尔值**：true/false（小写）
- **日期时间**：ISO 8601格式（YYYY-MM-DDTHH:MM:SSZ）
- **空值**：null

## 3. API版本控制策略

### 3.1 版本管理方案
- **URL路径版本**：在URL中包含版本号，如 `/v1/todo/add/`
- **请求头版本**：通过HTTP请求头 `X-API-Version` 指定版本

### 3.2 版本迭代流程
1. **新增API**：在新版本中添加，保持旧版本API不变
2. **修改API**：创建新版本API，旧版本API标记为 deprecated
3. **删除API**：在新版本中删除，旧版本API继续支持一段时间

### 3.3 向后兼容性
- 确保新版本API能够处理旧版本的请求格式
- 提供迁移指南，帮助客户端从旧版本迁移到新版本
- 旧版本API在一定时间内保持可用，给予客户端足够的迁移时间

### 3.4 版本号格式
- **主版本号**：当API发生不兼容的重大变化时增加
- **次版本号**：当API添加新功能但保持向后兼容时增加
- **修订版本号**：当API进行向后兼容的错误修复时增加

格式：`v{主版本号}.{次版本号}.{修订版本号}`

### 3.5 当前版本
- **API版本**：v1.0.0
- **状态**：稳定