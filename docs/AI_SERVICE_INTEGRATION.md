# 智能学习管理系统 - AI服务集成方式和配置

## 1. AI服务概述

本系统集成了ModelScope的AI模型，用于以下功能：
- 学习模板自动生成
- 学习资料内容生成
- AI对话助手

## 2. AI生成器实现

### 2.1 核心类：MultiSubjectAIGenerator

```python
class MultiSubjectAIGenerator:
    """多学科AI生成器"""
    
    def __init__(self):
        # 从环境变量读取配置
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv('MODELSCOPE_API_KEY', '')
        self.api_url = os.getenv(
            'MODELSCOPE_API_URL',
            'https://api-inference.modelscope.cn/v1/chat/completions'
        )
        self.model = os.getenv('MODELSCOPE_MODEL', 'Qwen/Qwen3-VL-8B-Instruct')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def _call_modelscope_api(self, prompt, max_tokens=1000, temperature=0.7):
        """调用ModelScope API"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                self.api_url, headers=self.headers, json=payload, timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"API调用失败: {e}")
            return None
    
    def generate_subject_framework(self, subject_name, exam_type):
        """生成学科知识框架"""
        prompt = f"""请为{subject_name}学科（{exam_type}）生成一个详细的知识框架，包含以下结构：

1. 主要章节（sections）
2. 每个章节下的子章节（chapters）

请以JSON格式返回，结构如下：
{
  "subject": "{subject_name}",
  "exam_type": "{exam_type}",
  "sections": [
    {
      "section_name": "章节名称",
      "chapters": [
        {
          "chapter_name": "子章节名称"
        }
      ]
    }
  ]
}

请确保框架结构合理，覆盖该学科的主要知识点。"""
        
        response = self._call_modelscope_api(prompt, max_tokens=2000)
        if response:
            try:
                import json
                return json.loads(response)
            except json.JSONDecodeError:
                return None
        return None
    
    def generate_learning_material(self, subject_name, section_name, chapter_names, content_types, exam_type):
        """生成学习资料"""
        content_type_map = {
            'knowledge': '知识点讲解',
            'questions': '典型例题',
            'exercises': '练习题',
            'summary': '章节总结'
        }
        
        content_type_str = '、'.join([content_type_map.get(ct, ct) for ct in content_types])
        chapters_str = '、'.join(chapter_names)
        
        prompt = f"""请为{subject_name}学科（{exam_type}）的{section_name}部分生成学习资料，包含以下内容：

章节：{chapters_str}
需要包含的内容类型：{content_type_str}

请确保内容详细、准确，适合学生学习使用。"""
        
        return self._call_modelscope_api(prompt, max_tokens=3000)
```

## 3. 配置方式

### 3.1 API密钥配置

在实际部署时，需要配置 `.env` 文件中的 ModelScope API 密钥：

1. **环境变量配置**（推荐方式）：
   ```ini
   # 在 .env 文件中配置
   MODELSCOPE_API_KEY=ms-xxxxxxxxxxxxxxxx
   MODELSCOPE_API_URL=https://api-inference.modelscope.cn/v1/chat/completions
   MODELSCOPE_MODEL=Qwen/Qwen3-VL-8B-Instruct
   ```

2. **代码读取方式**（在 ai_generator.py 中）：
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   
   self.api_key = os.getenv('MODELSCOPE_API_KEY', '')
   self.api_url = os.getenv('MODELSCOPE_API_URL', 'https://api-inference.modelscope.cn/v1/chat/completions')
   self.model = os.getenv('MODELSCOPE_MODEL', 'Qwen/Qwen3-VL-8B-Instruct')
   ```

### 3.2 模型选择

系统默认使用Qwen2.5-72B-Instruct模型，可根据需要调整为其他ModelScope支持的模型：

| 模型名称 | 适用场景 | 特点 |
|---------|---------|------|
| Qwen2.5-72B-Instruct | 通用场景 | 生成质量高，支持长文本 |
| Qwen2.5-14B-Instruct | 平衡场景 | 性能与质量平衡 |
| Qwen2.5-3B-Instruct | 轻量场景 | 响应速度快，适合简单任务 |

## 4. 调用流程

### 4.1 学习模板生成流程

1. **用户输入**：学科名称、考试类型、详细程度、学习目标
2. **前端调用**：`generate_ai_template`视图
3. **后端处理**：
   - 验证输入参数
   - 初始化AI生成器
   - 调用`generate_subject_framework`生成知识框架
   - 根据框架创建学习模板和模块
   - 保存到数据库
4. **返回结果**：模板ID、模板名称、成功消息

### 4.2 学习资料生成流程

1. **用户选择**：选择模板模块、生成版本、内容类型
2. **前端调用**：`generate_learning_materials`视图
3. **后端处理**：
   - 验证输入参数
   - 初始化AI生成器
   - 调用`generate_learning_material`生成学习资料
   - 保存到数据库
   - 清除相关缓存
4. **返回结果**：生成状态、学习资料内容

### 4.3 AI对话流程

1. **用户发送消息**：在AI对话页面输入问题
2. **前端调用**：`send_message`视图
3. **后端处理**：
   - 验证输入参数
   - 保存用户消息
   - 构建对话历史
   - 初始化AI生成器
   - 调用API生成回复
   - 保存AI回复
4. **返回结果**：用户消息、AI回复、时间戳

## 5. 错误处理

### 5.1 API调用错误

- **网络错误**：显示"AI生成失败，请检查网络连接"
- **API限制**：显示"API调用频率过高，请稍后再试"
- **参数错误**：显示"参数错误，请检查输入"

### 5.2 生成内容错误

- **JSON解析错误**：使用默认模板结构
- **内容为空**：显示"AI生成失败，返回默认内容"
- **生成超时**：显示"生成超时，请尝试更简单的请求"

## 6. 性能优化

### 6.1 缓存策略

- 缓存生成的模板框架
- 缓存常用的学习资料
- 缓存AI对话历史

### 6.2 异步处理

- 考虑使用Celery等异步任务队列处理AI生成请求
- 前端显示加载状态，提高用户体验

### 6.3 批量处理

- 支持批量生成学习资料
- 优化API调用频率，避免频繁请求

## 7. 安全考虑

### 7.1 API密钥保护

- 不在代码中硬编码API密钥
- 使用环境变量或配置文件管理
- 定期更换API密钥

### 7.2 输入验证

- 验证用户输入，防止恶意请求
- 限制输入长度和频率
- 过滤敏感内容

### 7.3 输出过滤

- 过滤AI生成的敏感内容
- 验证生成内容的质量
- 提供用户反馈机制

## 8. 扩展性

### 8.1 支持多模型

- 可扩展支持其他AI模型
- 可根据任务类型选择合适的模型

### 8.2 自定义提示词

- 支持自定义提示词模板
- 可根据学科特点调整提示词

### 8.3 多语言支持

- 可扩展支持多语言生成
- 可根据用户语言偏好调整生成内容