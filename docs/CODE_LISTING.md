# 智能学习管理系统 - 代码清单

## 1. 用户认证模块

### 1.1 登录视图
```python
def login_view(request):
    """用户登录"""
    # 如果用户已登录，直接跳转到首页
    if request.user.is_authenticated:
        return redirect('home')
    
    # 清除之前的消息，避免在登录页面显示不相关消息
    from django.contrib.messages import get_messages
    get_messages(request)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 验证用户
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 登录成功
            login(request, user)
            messages.success(request, f'欢迎回来，{username}！')
            return redirect('home')
        else:
            # 登录失败
            messages.error(request, '用户名或密码错误')
            return redirect('login')
    
    return render(request, 'login.html')
```

### 1.2 注册视图
```python
def register_view(request):
    """用户注册"""
    # 如果用户已登录，直接跳转到首页
    if request.user.is_authenticated:
        return redirect('home')
    
    # 清除之前的消息，避免在注册页面显示不相关消息
    from django.contrib.messages import get_messages
    get_messages(request)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # 验证密码是否匹配
        if password1 != password2:
            messages.error(request, '两次输入的密码不一致')
            return redirect('register')
        
        # 验证密码长度
        if len(password1) < 8:
            messages.error(request, '密码长度不能少于8位')
            return redirect('register')
        
        # 验证用户名是否已存在
        if User.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
            return redirect('register')
        
        # 验证邮箱是否已存在
        if User.objects.filter(email=email).exists():
            messages.error(request, '邮箱已被注册')
            return redirect('register')
        
        # 创建用户
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        
        # 创建用户扩展信息
        UserProfile.objects.create(user=user)
        
        # 创建用户学习状态
        UserStudyStatus.objects.create(user=user)
        
        # 自动登录
        login(request, user)
        
        messages.success(request, '注册成功！欢迎加入 StudyFlow')
        return redirect('home')
    
    return render(request, 'register.html')
```

### 1.3 注销视图
```python
def logout_view(request):
    """用户注销"""
    logout(request)
    messages.success(request, '已成功注销')
    return redirect('login')
```

## 2. 模板管理模块

### 2.1 模型定义
```python
# 学习进度模板表
class StudyTemplate(models.Model):
    name = models.CharField(max_length=100, verbose_name="模板名称") # 如：英语四级、考研数学
    description = models.TextField(blank=True, verbose_name="描述")
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0, verbose_name="排序顺序", help_text="数值越小，排序越靠前")
    is_example = models.BooleanField(default=False, verbose_name="是否为示例模板")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_templates", verbose_name="创建者")

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.name

# 模板模块表 (关联模板)
class TemplateModule(models.Model):
    # 目标值类型选项
    TARGET_TYPE_CHOICES = [
        ('numeric', '可量化目标'),  # 如：词汇数量、学习时长
        ('boolean', '完成判断'),    # 如：是否完成
        ('text', '主观描述'),        # 如：完成情况描述
    ]
    
    template = models.ForeignKey(StudyTemplate, on_delete=models.CASCADE, related_name='modules')
    name = models.CharField(max_length=50, verbose_name="模块名称") # 如：词汇、听力
    target_value = models.IntegerField(null=True, blank=True, verbose_name="目标量(如100个/100分钟)")
    target_type = models.CharField(max_length=10, choices=TARGET_TYPE_CHOICES, default='numeric', verbose_name="目标值类型")
    color_code = models.CharField(max_length=7, default="#81C784", verbose_name="展示颜色")

    def __str__(self):
        return f"{self.template.name} - {self.name}"
```

### 2.2 视图代码
```python
@login_required
def template_management(request):
    """模板管理页面"""
    # 获取用户可访问的模板：示例模板 + 用户创建的模板
    templates = StudyTemplate.objects.filter(
        Q(is_example=True) | Q(creator=request.user)
    )
    
    # 获取URL参数中的template_id
    template_id = request.GET.get('template_id')
    
    context = {
        'templates': templates,
        'selected_template_id': template_id
    }
    
    return render(request, 'template_management.html', context)

@login_required
def add_template(request):
    """添加学习模板"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            StudyTemplate.objects.create(
                name=name,
                description=description,
                creator=request.user
            )
            messages.success(request, '模板添加成功')
            
            # 清除缓存
            cache.delete(f'user_templates_{request.user.id}')
    
    return redirect('template_management')

@login_required
def edit_template(request, template_id):
    """编辑学习模板"""
    try:
        template = StudyTemplate.objects.get(id=template_id)
        
        # 检查权限：示例模板也可编辑，任何用户都可编辑任何模板
        if template.creator != request.user and not template.is_example:
            messages.error(request, '无权编辑该模板')
            return redirect('template_management')
            
        if request.method == 'POST':
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            if name:
                template.name = name
                template.description = description
                template.save()
                messages.success(request, '模板编辑成功')
                
                # 清除缓存
                cache.delete(f'user_templates_{request.user.id}')
                
                return redirect('template_management')
        
        context = {
            'template': template,
            'templates': StudyTemplate.objects.filter(
                Q(is_example=True) | Q(creator=request.user)
            )
        }
        return render(request, 'template_management.html', context)
    except StudyTemplate.DoesNotExist:
        messages.error(request, '模板不存在')
        return redirect('template_management')

@login_required
def delete_template(request, template_id):
    """删除学习模板"""
    if request.method == 'POST':
        try:
            template = StudyTemplate.objects.get(id=template_id)
            
            # 检查权限：示例模板也可删除，任何用户都可删除任何模板
            if template.creator != request.user and not template.is_example:
                messages.error(request, '无权删除该模板')
                return redirect('template_management')
                
            template.delete()
            messages.success(request, '模板删除成功')
            
            # 清除相关缓存，确保前端显示最新数据
            cache.delete(f'user_templates_{request.user.id}')  # 清除用户模板缓存
            
        except StudyTemplate.DoesNotExist:
            messages.error(request, '模板不存在')
    
    return redirect('template_management')

@login_required
def add_module(request, template_id):
    """添加模板模块"""
    try:
        template = StudyTemplate.objects.get(id=template_id)
        if request.method == 'POST':
            name = request.POST.get('name')
            target_value = request.POST.get('target_value')
            target_type = request.POST.get('target_type', 'numeric')
            color_code = request.POST.get('color_code', '#81C784')
            
            if name:
                # 根据目标类型处理target_value
                if target_type == 'text':
                    # 主观描述类型，不需要目标值
                    module = TemplateModule.objects.create(
                        template=template,
                        name=name,
                        target_type=target_type,
                        color_code=color_code
                    )
                else:
                    # 其他类型，需要目标值
                    if target_value:
                        module = TemplateModule.objects.create(
                            template=template,
                            name=name,
                            target_value=int(target_value),
                            target_type=target_type,
                            color_code=color_code
                        )
                    else:
                        messages.error(request, '非主观描述类型必须填写目标值')
                        return redirect('template_management')
                
                messages.success(request, '模块添加成功')
                
                # 清除相关缓存，确保前端显示最新数据
                cache.delete('all_templates')  # 清除模板列表缓存
                cache.delete(f'progress_dashboard_{request.user.id}_')  # 清除进度看板缓存
                cache.delete(f'progress_dashboard_{request.user.id}_None')  # 清除进度看板缓存
                
    except StudyTemplate.DoesNotExist:
        messages.error(request, '模板不存在')
    
    return redirect('template_management')

@login_required
def edit_module(request, module_id):
    """编辑模板模块"""
    try:
        module = TemplateModule.objects.get(id=module_id)
        if request.method == 'POST':
            name = request.POST.get('name')
            target_value = request.POST.get('target_value')
            target_type = request.POST.get('target_type', 'numeric')
            color_code = request.POST.get('color_code', '#81C784')
            
            if name:
                module.name = name
                module.target_type = target_type
                module.color_code = color_code
                
                # 根据目标类型处理target_value
                if target_type == 'text':
                    # 主观描述类型，不需要目标值
                    module.target_value = None
                else:
                    # 其他类型，需要目标值
                    if target_value:
                        module.target_value = int(target_value)
                    else:
                        messages.error(request, '非主观描述类型必须填写目标值')
                        return redirect('template_management')
                
                module.save()
                messages.success(request, '模块编辑成功')
                
                # 清除相关缓存，确保前端显示最新数据
                cache.delete('all_templates')  # 清除模板列表缓存
                cache.delete(f'progress_dashboard_{request.user.id}_')  # 清除进度看板缓存
                cache.delete(f'progress_dashboard_{request.user.id}_None')  # 清除进度看板缓存
    except TemplateModule.DoesNotExist:
        messages.error(request, '模块不存在')
    
    return redirect('template_management')

@login_required
def delete_module(request, module_id):
    """删除模板模块"""
    if request.method == 'POST':
        try:
            module = TemplateModule.objects.get(id=module_id)
            module.delete()
            messages.success(request, '模块删除成功')
            
            # 清除相关缓存，确保前端显示最新数据
            cache.delete('all_templates')  # 清除模板列表缓存
            cache.delete(f'progress_dashboard_{request.user.id}_')  # 清除进度看板缓存
            cache.delete(f'progress_dashboard_{request.user.id}_None')  # 清除进度看板缓存
        except TemplateModule.DoesNotExist:
            messages.error(request, '模块不存在')
    
    return redirect('template_management')
```

## 3. AI功能模块

### 3.1 AI模板生成
```python
@login_required
def generate_ai_template(request):
    """AI生成学习模板"""
    if request.method == 'POST':
        # 获取表单数据
        subject_name = request.POST.get('subject', '').strip()
        exam_type = request.POST.get('exam_type', '').strip()
        detail_level = request.POST.get('detail_level', 'basic')
        goal = request.POST.get('goal', '').strip()
        
        if not subject_name:
            return JsonResponse({'success': False, 'message': '学科名称不能为空'})
        
        if not exam_type:
            exam_type = '通用考试'
        
        try:
            # 初始化AI生成器
            generator = MultiSubjectAIGenerator()
            
            # 生成学科知识框架
            framework = generator.generate_subject_framework(subject_name, exam_type)
            
            if not framework:
                return JsonResponse({'success': False, 'message': 'AI生成失败，请检查网络连接'})
            
            # 创建学习模板，关联到当前登录用户
            study_template = StudyTemplate.objects.create(
                name=f"{subject_name}学习模板",
                description=f"AI生成的{exam_type}{subject_name}学习模板，目标：{goal or '全面学习'}",
                creator=request.user
            )
            
            # 根据生成的框架创建模块
            colors = ['#81C784', '#64B5F6', '#FFB74D', '#9575CD', '#E57373', '#4FC3F7', '#F06292', '#FFA726']
            module_count = 0
            
            for section in framework.get('sections', []):
                for chapter in section.get('chapters', []):
                    # 为每个章节创建一个模块
                    color_code = colors[module_count % len(colors)]
                    TemplateModule.objects.create(
                        template=study_template,
                        name=chapter.get('chapter_name', f'模块{module_count + 1}'),
                        target_value=100,  # 默认目标值
                        target_type='numeric',  # 默认目标类型为可量化
                        color_code=color_code
                    )
                    module_count += 1
            
            # 清除相关缓存，确保前端显示最新数据
            cache.delete('all_templates')  # 清除模板列表缓存
            cache.delete(f'user_templates_{request.user.id}')  # 清除用户模板缓存
            cache.delete(f'progress_dashboard_{request.user.id}_')  # 清除进度看板缓存
            
            return JsonResponse({
                'success': True,
                'message': 'AI模板生成成功',
                'template_id': study_template.id,
                'template_name': study_template.name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'AI生成失败：{str(e)}'})
    
    return JsonResponse({'success': False, 'message': '无效请求'})
```

### 3.2 学习资料生成
```python
@login_required
def generate_learning_materials(request):
    """生成学习资料"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            module_ids = request.POST.getlist('modules')
            generate_version = request.POST.get('generate_version', 'detailed')
            content_types = request.POST.getlist('content_types')
            
            if not module_ids:
                return JsonResponse({'success': False, 'message': '请至少选择一个模块'})
            
            # 根据版本和用户选择确定最终内容类型
            version_content_map = {
                'detailed': ['knowledge', 'questions', 'exercises', 'summary'],
                'normal': ['knowledge', 'questions', 'summary'],
                'simple': ['questions', 'exercises']
            }
            
            # 如果用户没有自定义内容类型，使用版本默认配置
            final_content_types = content_types if content_types else version_content_map.get(generate_version, version_content_map['detailed'])
            
            # 初始化AI生成器
            generator = MultiSubjectAIGenerator()
            
            # 获取模块信息
            modules = TemplateModule.objects.filter(id__in=module_ids)
            
            # 生成学习资料
            results = []
            for module in modules:
                # 获取模板信息
                template = module.template
                
                # 获取模板的学科名称和考试类型
                subject_name = template.name.replace('学习模板', '').strip()
                exam_type = template.description.split('AI生成的')[1].split(subject_name)[0].strip() if 'AI生成的' in template.description else '通用考试'
                
                # 生成学习资料
                content = generator.generate_learning_material(
                    subject_name=subject_name,
                    section_name=module.name,
                    chapter_names=[module.name],  # 使用模块名称作为章节名称
                    content_types=final_content_types,
                    exam_type=exam_type
                )
                
                if content:
                    # 保存学习资料到数据库
                    material = LearningMaterial.objects.create(
                        module=module,
                        section_name=module.name,
                        chapter_names=json.dumps([module.name]),
                        content=content,
                        generate_type=generate_version
                    )
                    results.append({
                        'module_id': module.id,
                        'module_name': module.name,
                        'material_id': material.id,
                        'success': True
                    })
                else:
                    results.append({
                        'module_id': module.id,
                        'module_name': module.name,
                        'success': False
                    })
            
            # 清除相关缓存
            cache.delete('all_templates')
            
            # 清除学习页面缓存，确保生成的学习资料能立即显示
            for module in modules:
                # 清除该模块在study_base页面的缓存
                cache.delete(f'study_base_{module.template.id}_{module.name}')
                # 清除该模板的默认缓存
                cache.delete(f'study_base_{module.template.id}_')
                cache.delete(f'study_base_{module.template.id}_None')
                
                # 清除特定学科学习页面的缓存
                template_name = module.template.name
                if template_name == "英语四级":
                    cache.delete(f'cet4_study_{module.name}')
                elif template_name == "专升本C语言":
                    cache.delete(f'c_language_study_{module.name}')
                elif template_name == "专升本政治":
                    cache.delete(f'politics_study_{module.name}')
            
            # 获取生成的学习资料，用于返回给前端
            generated_materials = []
            for module in modules:
                # 获取该模块刚生成的学习资料
                materials = LearningMaterial.objects.filter(
                    module=module,
                    generate_type=generate_version
                ).order_by('-generated_at')[:1]  # 获取最新生成的资料
                
                for material in materials:
                    generated_materials.append({
                        'id': material.id,
                        'section_name': material.section_name,
                        'content': material.content,
                        'generate_type': material.generate_type,
                        'generate_type_display': material.get_generate_type_display(),
                        'generated_at': material.generated_at.strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # 返回成功响应
            return JsonResponse({
                'success': True,
                'message': '学习资料生成完成',
                'results': results,
                'materials': generated_materials
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'生成失败：{str(e)}'})
    
    return JsonResponse({'success': False, 'message': '无效的请求方式'})
```

### 3.3 AI对话功能
```python
@login_required
def send_message(request):
    """发送消息并获取AI回复"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            chat_id = data.get('chat_id')
            user_message = data.get('message')
            
            if not chat_id or not user_message:
                return JsonResponse({'success': False, 'message': '缺少必要参数'})
            
            # 获取对话历史
            chat_history = AIChatHistory.objects.get(id=chat_id, user=request.user)
            
            # 保存用户消息
            user_chat_message = AIChatMessage.objects.create(
                chat_history=chat_history,
                role='user',
                content=user_message
            )
            
            # 构建对话历史用于AI生成
            messages = list(chat_history.messages.all().values('role', 'content'))
            
            # 初始化AI生成器
            generator = MultiSubjectAIGenerator()
            
            # 构建AI提示词
            prompt = f"""你是一位AI学习助手，请根据以下对话历史回答用户的问题：

对话历史：
{chr(10).join([f'{msg["role"]}: {msg["content"]}' for msg in messages])}

请基于上述对话历史，以自然、友好的语言回答用户的最新问题。"""
            
            # 调用AI生成回复
            ai_response = generator._call_modelscope_api(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            if not ai_response:
                ai_response = "抱歉，我暂时无法回答这个问题，请稍后再试。"
            
            # 保存AI回复
            ai_chat_message = AIChatMessage.objects.create(
                chat_history=chat_history,
                role='assistant',
                content=ai_response
            )
            
            return JsonResponse({
                'success': True,
                'user_message': {
                    'id': user_chat_message.id,
                    'role': user_chat_message.role,
                    'content': user_chat_message.content,
                    'created_at': user_chat_message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                },
                'ai_response': {
                    'id': ai_chat_message.id,
                    'role': ai_chat_message.role,
                    'content': ai_chat_message.content,
                    'created_at': ai_chat_message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': '无效请求'})
```

## 4. 进度跟踪模块

### 4.1 模型定义
```python
# 每日进度记录表
class DailyProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(TemplateModule, on_delete=models.CASCADE)
    actual_value = models.IntegerField(default=0, verbose_name="今日完成量")
    actual_text = models.TextField(blank=True, null=True, verbose_name="完成情况描述")
    is_completed = models.BooleanField(default=False, verbose_name="是否完成")
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="提交时间")

    class Meta:
        ordering = ['-date', '-created_at']

# 沉浸学习记录表 (计时器使用)
class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, verbose_name="学习科目")
    duration_minutes = models.IntegerField(verbose_name="学习时长(分钟)")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    start_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.subject} - {self.duration_minutes}min"
```

### 4.2 进度提交视图
```python
def submit_daily_progress(request):
    """提交每日进度"""
    # 1. 检查用户是否登录
    if not request.user.is_authenticated:
        messages.error(request, '请先登录')
        return redirect('login')
    
    if request.method == 'POST':
        # 2. 获取当前登录用户
        user = request.user
        
        # 3. 获取表单数据
        template_id = request.POST.get('template')
        notes = request.POST.get('notes', '')
        
        # 获取总的学习时间
        learning_time = request.POST.get('learning_time')
        learning_time_minutes = 0
        if learning_time and learning_time.strip():
            try:
                # 将小时转换为分钟
                learning_time_minutes = int(float(learning_time) * 60)
            except ValueError:
                learning_time_minutes = 0
        
        # 4. 验证数据
        try:
            template = StudyTemplate.objects.get(id=template_id)
            
            # 检查用户是否有权访问该模板：只能为示例模板或自己创建的模板提交进度
            if not (template.is_example or template.creator == user):
                messages.error(request, '您无权访问该模板')
                return redirect('daily_progress')
                
        except StudyTemplate.DoesNotExist:
            messages.error(request, '学习模板未找到')
            return redirect('daily_progress')
        
        # 5. 处理模块进度数据
        modules = TemplateModule.objects.filter(template=template)
        progress_saved = 0
        
        for module in modules:
            actual_value = 0
            actual_text = ''
            is_completed = False
            
            if module.target_type == 'boolean':
                # 二元判断模块处理
                module_key = f'module_{module.id}'
                checkbox_value = request.POST.get(module_key)
                is_completed = checkbox_value == '1'
                actual_value = 1 if is_completed else 0
            elif module.target_type == 'text':
                # 主观描述模块处理
                text_key = f'module_text_{module.id}'
                actual_text = request.POST.get(text_key, '')
                is_completed = actual_text.strip() != ''
                actual_value = 1 if is_completed else 0
            else:
                # 可量化目标模块处理
                module_key = f'module_{module.id}'
                module_value = request.POST.get(module_key)
                if module_value is not None and module_value.strip() != '':
                    try:
                        actual_value = int(module_value)
                        is_completed = actual_value > 0
                    except ValueError:
                        # 处理无效的数值输入
                        actual_value = 0
                        is_completed = False
                else:
                    actual_value = 0
                    is_completed = False
            
            # 只有当实际完成量大于0、文本内容不为空或二元判断模块被选中时，才创建进度记录
            if actual_value > 0 or (module.target_type == 'text' and actual_text.strip() != '') or (module.target_type == 'boolean' and is_completed):
                DailyProgress.objects.create(
                    user=user,
                    module=module,
                    actual_value=actual_value,
                    actual_text=actual_text,
                    is_completed=is_completed,
                    date=datetime.now().date()
                )
                progress_saved += 1
        
        # 创建总的学习时间记录
        if learning_time_minutes > 0:
            StudySession.objects.create(
                user=user,
                subject=f'{template.name}',
                duration_minutes=learning_time_minutes,
                notes=notes
            )
        
        # 6. 更新用户学习状态
        # 无论是否有进度保存，只要有学习时间记录，就更新学习状态
        if progress_saved > 0 or learning_time_minutes > 0:
            # 更新总进度（示例：简单计算完成率）
            study_status, created = UserStudyStatus.objects.get_or_create(user=user)
            
            # 更新模板完成率
            total_modules = modules.count()
            completed_modules = DailyProgress.objects.filter(
                user=user,
                module__template=template,
                date=datetime.now().date(),
                actual_value__gt=0
            ).count()
            
            if total_modules > 0:
                completion_rate = (completed_modules / total_modules) * 100
                study_status.template_completion_rate = completion_rate
            
            # 更新累计学习时长
            total_minutes = StudySession.objects.filter(user=user).aggregate(
                total=models.Sum('duration_minutes')
            )['total'] or 0
            study_status.cumulative_study_time = total_minutes / 60.0
            
            study_status.save()
            
            # 更新用户资料中的累计学习时长
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.total_study_time = total_minutes / 60.0
            profile.save()
        
        # 7. 清除相关缓存，确保数据实时性
        cache.delete(f'user_profile_{user.id}')  # 清除用户资料缓存
        cache.delete('all_templates')  # 清除模板缓存
        cache.delete(f'progress_dashboard_{user.id}_')  # 清除进度看板缓存（默认模板）
        cache.delete(f'progress_dashboard_{user.id}_None')  # 清除进度看板缓存（None模板）
        cache.delete(f'profile_view_{user.id}')  # 清除个人中心缓存
        
        # 清除所有可能的模板ID缓存
        templates = StudyTemplate.objects.all()
        for template in templates:
            cache.delete(f'progress_dashboard_{user.id}_{template.id}')
        
        # 8. 返回成功消息
        messages.success(request, f'今日进度保存成功！已保存 {progress_saved} 个模块的数据')
        # 跳转到进度看板时传递当前模板ID，以便显示该模板的数据
        return redirect(f'{reverse("progress_dashboard")}?template_id={template_id}')
    
    # 如果是GET请求，重定向到进度填写页面
    return redirect('daily_progress')
```

### 4.3 进度看板视图
```python
def progress_dashboard(request):
    """学习进度看板"""
    # 1. 获取当前用户
    user = request.user
    
    # 2. 如果用户未登录，重定向到登录页面
    if not user.is_authenticated:
        return redirect('login')
    
    # 2. 获取模板选择
    template_id = request.GET.get('template_id')
    
    # 3. 重新计算用户的累计学习时长，确保数据准确
    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
        total_minutes = StudySession.objects.filter(user=user).aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        profile.total_study_time = total_minutes / 60.0  # 转换为小时
        profile.save()
    except Exception as e:
        pass
    
    # 4. 尝试从缓存获取数据，减少数据库查询
    cache_key = f'progress_dashboard_{user.id}_{template_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'progress_dashboard.html', cached_data)
    
    # 3. 获取真实学习数据
    overall_progress = 0
    recent_study_time = 0  # 近7天学习时长
    total_study_time = 0  # 累计学习时长
    study_sessions = []  # 最近学习记录
    module_progress_map = {}  # 初始化模块进度映射，防止未定义错误
    
    # 图表数据初始化
    completion_data = {
        'labels': ['词汇', '语法', '听力', '阅读', '写作'],
        'datasets': [{
            'data': [0, 0, 0, 0, 0],
            'backgroundColor': [
                '#81C784',
                '#64B5F6',
                '#FFB74D',
                '#9575CD',
                '#E57373'
            ]
        }]
    }
    
    daily_data = {
        'labels': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
        'datasets': [{
            'label': '学习时长（分钟）',
            'data': [0, 0, 0, 0, 0, 0, 0],
            'borderColor': '#81C784',
            'backgroundColor': 'rgba(129, 199, 132, 0.1)',
            'fill': True,
            'tension': 0.4
        }]
    }
    
    grammar_data = {
        'labels': ['虚拟语气', '时态', '被动语态', '从句', '非谓语动词'],
        'datasets': [{
            'label': '掌握程度（%）',
            'data': [0, 0, 0, 0, 0],
            'backgroundColor': '#64B5F6'
        }]
    }
    
    if user:
        # 2.1 获取累计学习时长
        profile, created = UserProfile.objects.get_or_create(user=user)
        total_study_time = profile.total_study_time
        
        # 2.5 首先获取所有模板的模块完成率数据（支持模板选择）
        all_templates = StudyTemplate.objects.filter(
            Q(is_example=True) | Q(creator=user)
        )
        # 根据模板ID选择模板，若无ID或ID无效则使用第一个模板
        template = None
        if template_id:
            template = StudyTemplate.objects.filter(id=template_id).first()
        if not template:
            template = all_templates.first()
        
        # 2.2 获取近7天学习时长和每日学习数据
        from datetime import timedelta, date
        import calendar
        import random
        
        # 获取近7天日期
        seven_days_ago = datetime.now() - timedelta(days=6)  # 包括今天共7天
        recent_dates = [(seven_days_ago + timedelta(days=i)).date() for i in range(7)]
        
        # 设置每日学习数据的标签为星期几
        daily_data['labels'] = [calendar.day_name[d.weekday()] for d in recent_dates]
        daily_data['labels'] = [d.replace('Monday', '周一').replace('Tuesday', '周二').replace('Wednesday', '周三').replace('Thursday', '周四').replace('Friday', '周五').replace('Saturday', '周六').replace('Sunday', '周日') for d in daily_data['labels']]
        
        # 获取近7天学习记录
        # 如果有模板，只显示该模板的学习记录；否则显示所有学习记录
        if template:
            recent_sessions = StudySession.objects.filter(
                user=user,
                start_time__gte=seven_days_ago,
                subject=template.name  # 根据模板名称过滤
            ).order_by('start_time')
        else:
            recent_sessions = StudySession.objects.filter(
                user=user,
                start_time__gte=seven_days_ago
            ).order_by('start_time')
        
        # 计算近7天总学习时长
        recent_study_time = sum(session.duration_minutes for session in recent_sessions) / 60.0  # 转换为小时
        
        # 统计每天的学习时长
        daily_duration = {d: 0 for d in recent_dates}
        for session in recent_sessions:
            session_date = session.start_time.date()
            if session_date in daily_duration:
                daily_duration[session_date] += session.duration_minutes
        
        # 将每天的学习时长放入数据集 - 只使用真实数据，不生成随机数据
        daily_data['datasets'][0]['data'] = [daily_duration[d] for d in recent_dates]
        
        # 2.3 获取最近学习记录（最多100条）
        # 如果有模板，只显示该模板的学习记录；否则显示所有学习记录
        if template:
            study_sessions = StudySession.objects.filter(
                user=user,
                subject=template.name  # 根据模板名称过滤
            ).order_by('-start_time')[:100]
        else:
            study_sessions = StudySession.objects.filter(user=user).order_by('-start_time')[:100]
        
        # 2.4 计算整体进度（从UserStudyStatus获取）
        study_status, created = UserStudyStatus.objects.get_or_create(user=user)
        overall_progress = int(study_status.template_completion_rate) if study_status.template_completion_rate else 0
        
        # 模板数据已在前面获取
        
        if template:
            modules = template.modules.all()
            if modules:
                # 准备模块完成率数据
                module_names = []
                module_progress = []
                colors = ['#81C784', '#64B5F6', '#FFB74D', '#9575CD', '#E57373', '#4FC3F7', '#F06292', '#FFA726']
                
                # 获取真实的模块进度数据
                module_progress_map = {}
                total_progress_sum = 0
                valid_module_count = 0
                
                # 遍历每个模块，计算实际进度
                for module in modules:
                    # 获取该模块的所有历史进度记录，计算累计完成量
                    all_progress = DailyProgress.objects.filter(
                        user=user,
                        module=module
                    )
                    
                    # 累加所有历史进度
                    total_actual_value = sum(progress.actual_value for progress in all_progress)
                    
                    # 计算完成率：(累计完成量 / 目标量) * 100
                    if module.target_type == 'text' or module.target_value is None:
                        # 主观描述类型或目标值为None，跳过进度计算
                        completion_rate = 0
                    else:
                        target_value = module.target_value if module.target_value > 0 else 100
                        completion_rate = int((total_actual_value / target_value) * 100)
                        completion_rate = max(0, min(100, completion_rate))
                    
                    # 保存进度数据
                    module_progress_map[module.name] = completion_rate
                    
                    # 用于计算总进度
                    total_progress_sum += completion_rate
                    valid_module_count += 1
                
                # 计算总进度（所有模块的平均值）
                if valid_module_count > 0:
                    overall_progress = int(total_progress_sum / valid_module_count)
                else:
                    overall_progress = 0
                
                # 更新用户学习状态的总进度
                study_status, created = UserStudyStatus.objects.get_or_create(user=user)
                study_status.template_completion_rate = overall_progress
                study_status.save()
                
                # 遍历模块，准备显示数据
                for i, module in enumerate(modules):  # 显示所有模块
                    module_names.append(module.name)
                    # 获取该模块的完成率
                    progress = module_progress_map.get(module.name, 0)
                    module_progress.append(progress)
                
                # 更新饼图数据
                completion_data['labels'] = module_names
                completion_data['datasets'][0]['data'] = module_progress
                completion_data['datasets'][0]['backgroundColor'] = colors[:len(module_names)]
                
                # 使用当前模板的真实模块作为知识点标签，并过滤非数据模块
                real_module_names = []
                real_module_progress = []
                
                # 遍历模块，只使用可量化的模块（排除文本类型）
                for i, module in enumerate(modules):
                    if module.target_type in ['numeric', 'boolean']:  # 只使用可量化目标模块
                        real_module_names.append(module.name)
                        real_module_progress.append(module_progress_map.get(module.name, 0))
                
                # 更新知识点掌握情况图表数据
                grammar_data['labels'] = real_module_names
                grammar_data['datasets'][0]['data'] = real_module_progress
    
    # 3. 获取每日进度记录
    daily_progress_records = []
    if user:
        # 如果有模板，只显示该模板的进度记录；否则显示所有进度记录
        if template:
            daily_progress_records = DailyProgress.objects.filter(
                user=user,
                module__template=template  # 根据模板过滤
            ).order_by('-date', '-id')[:100]
        else:
            daily_progress_records = DailyProgress.objects.filter(user=user).order_by('-date', '-id')[:100]
    
    # 4. 构造上下文
    now = datetime.now()
    context = {
        'today_date': format_chinese_date(now),
        'overall_progress': overall_progress,
        'total_study_time': round(total_study_time, 1),
        'recent_study_time': round(recent_study_time, 1),
        'study_sessions': study_sessions,
        'daily_progress_records': daily_progress_records,
        'completion_data': completion_data,
        'daily_data': daily_data,
        'grammar_data': grammar_data,
        'templates': StudyTemplate.objects.filter(
            Q(is_example=True) | Q(creator=user)
        ),
        'selected_template_id': template_id,
        'current_template': template,
        'module_progress_map': module_progress_map
    }
    
    # 4. 缓存数据，有效期10分钟
    cache.set(cache_key, context, timeout=600)
    
    return render(request, 'progress_dashboard.html', context)
```

## 5. 后台管理模块

### 5.1 admin.py 配置
```python
from django.contrib import admin
from .models import UserProfile, StudyTemplate, TemplateModule, DailyProgress, StudySession, TodoTask

@admin.register(TodoTask)
class TodoTaskAdmin(admin.ModelAdmin):
    list_display = ('content', 'user', 'priority', 'is_done')

@admin.register(StudyTemplate)
class StudyTemplateAdmin(admin.ModelAdmin):
    pass

@admin.register(TemplateModule)
class TemplateModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'template', 'target_value')

admin.site.register(UserProfile)
admin.site.register(DailyProgress)
admin.site.register(StudySession)
```

## 6. 其他核心功能

### 6.1 待办事项功能
```python
@login_required
def add_todo(request):
    """添加新任务"""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            TodoTask.objects.create(
                user=request.user,
                content=content
            )
    return redirect('home')

@login_required
def toggle_todo(request, todo_id):
    """切换任务状态"""
    if request.method == 'POST':
        try:
            todo = TodoTask.objects.get(id=todo_id, user=request.user)
            todo.is_done = not todo.is_done
            todo.save()
        except TodoTask.DoesNotExist:
            pass
    return redirect('home')

@login_required
def delete_todo(request, todo_id):
    """删除任务"""
    if request.method == 'POST':
        try:
            todo = TodoTask.objects.get(id=todo_id, user=request.user)
            todo.delete()
        except TodoTask.DoesNotExist:
            pass
    return redirect('home')
```

### 6.2 专注计时功能
```python
@login_required
def study_session(request):
    """沉浸学习模式 - 计时页面"""
    # 获取URL参数中的template_id
    template_id = request.GET.get('template_id')
    
    context = {
        'template_id': template_id
    }
    
    return render(request, 'study_session.html', context)

@login_required
def study_session_end(request):
    """沉浸学习结束 - 记录学习数据并显示总结"""
    if request.method == 'POST':
        # 1. 获取当前登录用户
        user = request.user
        
        # 2. 获取表单数据
        duration_minutes = int(request.POST.get('duration', 0))
        subject = request.POST.get('subject', '')
        notes = request.POST.get('notes', '')
        
        # 3. 验证数据
        if not subject:
            messages.error(request, '请输入学习科目')
            return redirect('study_session')
        
        # 4. 记录学习会话
        session = StudySession.objects.create(
            user=user,
            subject=subject,
            duration_minutes=duration_minutes,
            notes=notes
        )
        
        # 5. 更新用户累计学习时长
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.total_study_time += duration_minutes / 60.0  # 转换为小时
        profile.save()
        
        # 6. 更新用户学习状态（驱动玩偶）
        study_status, created = UserStudyStatus.objects.get_or_create(user=user)
        study_status.cumulative_study_time += duration_minutes / 60.0
        study_status.save()
        
        # 7. 清除相关缓存，确保数据实时性
        cache.delete(f'user_profile_{user.id}')  # 清除用户资料缓存
        cache.delete('all_templates')  # 清除模板缓存
        cache.delete(f'progress_dashboard_{user.id}_')  # 清除进度看板缓存（默认模板）
        cache.delete(f'progress_dashboard_{user.id}_None')  # 清除进度看板缓存（None模板）
        cache.delete(f'profile_view_{user.id}')  # 清除个人中心缓存
        
        # 清除所有可能的模板ID缓存
        templates = StudyTemplate.objects.all()
        for template in templates:
            cache.delete(f'progress_dashboard_{user.id}_{template.id}')
        
        # 7. 生成鼓励话语
        encouragement_messages = [
            f"太棒了！你已经完成了 {duration_minutes} 分钟的学习，继续保持这个节奏，成功就在前方！",
            f"优秀！本次学习时长 {duration_minutes} 分钟，每一次努力都在为你的目标积累力量！",
            f"为你点赞！{duration_minutes} 分钟的专注学习，你正在成为更好的自己！",
            f"完美！{duration_minutes} 分钟的学习时光，知识正在慢慢充实你的大脑，坚持下去！",
            f"了不起！{duration_minutes} 分钟的高效学习，你的努力终将收获回报！",
            f"出色！本次学习 {duration_minutes} 分钟，继续保持，距离成功又近了一步！",
            f"精彩！{duration_minutes} 分钟的专注，你正在创造属于自己的辉煌！",
            f"厉害！{duration_minutes} 分钟的学习，每一分钟都是成长的见证！",
            f"加油！{duration_minutes} 分钟的付出，未来的你会感谢现在努力的自己！",
            f"完美！{duration_minutes} 分钟的学习，坚持就是胜利！"
        ]
        
        import random
        encouragement = random.choice(encouragement_messages)
        
        # 8. 渲染学习总结页面
        return render(request, 'study_summary.html', {
            'session': session,
            'encouragement': encouragement
        })
    
    # 如果是GET请求，重定向到计时页面
    return redirect('study_session')
```

### 6.3 资料库功能
```python
@login_required
def get_module_materials(request, module_id):
    """获取模块的学习资料"""
    if request.method == 'GET':
        try:
            # 获取模块信息
            module = TemplateModule.objects.get(id=module_id)
            
            # 获取模块的所有学习资料
            materials = LearningMaterial.objects.filter(module=module).order_by('-generated_at')
            
            # 格式化学习资料数据
            materials_data = []
            for material in materials:
                materials_data.append({
                    'id': material.id,
                    'section_name': material.section_name,
                    'chapter_names': json.loads(material.chapter_names),
                    'content': material.content,
                    'generate_type': material.generate_type,
                    'generate_type_display': material.get_generate_type_display(),
                    'generated_at': material.generated_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # 返回成功响应
            return JsonResponse({
                'success': True,
                'module_id': module.id,
                'module_name': module.name,
                'materials': materials_data
            })
        except TemplateModule.DoesNotExist:
            return JsonResponse({'success': False, 'message': '模块不存在'})
    
    return JsonResponse({'success': False, 'message': '无效的请求方式'})
```