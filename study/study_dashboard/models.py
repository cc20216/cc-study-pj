from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 1. 用户扩展信息表 (关联内置 User)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    doll_image = models.ImageField(upload_to='doll_images/', null=True, blank=True, verbose_name="自定义玩偶图片")
    total_study_time = models.FloatField(default=0.0, verbose_name="累计学习时长(h)")
    streak_days = models.IntegerField(default=0, verbose_name="连续学习天数")

    def __str__(self):
        return f"{self.user.username} 的个人资料"

# 2. 学习进度模板表
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

# 3. 模板模块表 (关联模板)
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

# 4. 每日进度记录表
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

# 5. 沉浸学习记录表 (计时器使用)
class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, verbose_name="学习科目")
    duration_minutes = models.IntegerField(verbose_name="学习时长(分钟)")
    notes = models.TextField(blank=True, null=True, verbose_name="备注")
    start_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.subject} - {self.duration_minutes}min"

# 6. 任务清单表 (首页左侧展示)
class TodoTask(models.Model):
    PRIORITY_CHOICES = [('H', '高'), ('M', '中'), ('L', '低')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=200, verbose_name="任务内容")
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default='M')
    is_done = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.content

# 7. 用户学习状态表 (驱动玩偶状态)
class UserStudyStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='study_status')
    cumulative_study_time = models.FloatField(default=0.0, verbose_name="累计学习时长(h)")
    template_completion_rate = models.FloatField(default=0.0, verbose_name="模板完成率(%)")
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} 的学习状态"

# 8. 学习资料表 (关联模板模块)
class LearningMaterial(models.Model):
    # 生成类型选项
    GENERATE_TYPE_CHOICES = [
        ('simple', '简略版'),  # 快速生成，适合复习
        ('detailed', '详细版'), # 详细内容，包含例题
    ]
    
    module = models.ForeignKey(TemplateModule, on_delete=models.CASCADE, related_name='materials')
    section_name = models.CharField(max_length=100, verbose_name="板块名称")
    chapter_names = models.TextField(verbose_name="章节名称列表", help_text="JSON格式的章节名称列表")
    content = models.TextField(verbose_name="学习资料内容")
    generate_type = models.CharField(max_length=10, choices=GENERATE_TYPE_CHOICES, default='simple', verbose_name="生成类型")
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="生成时间")
    
    def __str__(self):
        return f"{self.module.name} - {self.get_generate_type_display()}学习资料"
    
    class Meta:
        ordering = ['-generated_at']

# 9. AI对话记录表 (AI问答功能)
class AIChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_histories')
    chat_name = models.CharField(max_length=100, verbose_name="对话名称", default="新对话")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    def __str__(self):
        return f"{self.user.username} - {self.chat_name}"
    
    class Meta:
        ordering = ['-updated_at']

# 10. AI对话消息表 (消息内容)
class AIChatMessage(models.Model):
    # 消息角色选项
    ROLE_CHOICES = [
        ('user', '用户'),
        ('assistant', 'AI助手'),
    ]
    
    chat_history = models.ForeignKey(AIChatHistory, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name="消息角色")
    content = models.TextField(verbose_name="消息内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="发送时间")
    
    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."
    
    class Meta:
        ordering = ['created_at']