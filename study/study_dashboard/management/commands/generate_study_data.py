from django.core.management.base import BaseCommand
from django.db import models
from study_dashboard.models import (
    User, UserProfile, StudySession, DailyProgress, 
    StudyTemplate, TemplateModule, UserStudyStatus
)
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = '生成示例学习会话和每日进度数据'

    def handle(self, *args, **kwargs):
        # 检查是否有用户，如果没有则创建一个测试用户
        if not User.objects.exists():
            self.stdout.write('创建测试用户...')
            user = User.objects.create_user(
                username='testuser',
                password='testpass123',
                email='test@example.com'
            )
            # 创建用户扩展信息
            UserProfile.objects.create(user=user)
            # 创建用户学习状态
            UserStudyStatus.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS('测试用户已创建'))
        else:
            # 使用第一个用户
            user = User.objects.first()
        
        # 获取所有模板和模块
        templates = StudyTemplate.objects.all()
        if not templates:
            self.stdout.write(self.style.ERROR('没有找到学习模板，请先运行 generate_sample_data 命令'))
            return
        
        # 生成最近30天的学习会话数据
        self.stdout.write('生成学习会话数据...')
        subjects = ['英语四级词汇', '英语四级听力', '编程学习', '考研英语阅读']
        notes = ['今天学习了新单词', '听力练习进步很大', '编程题做了10道', '阅读速度有所提升']
        
        for i in range(30):
            # 随机生成1-3个学习会话
            session_count = random.randint(1, 3)
            for _ in range(session_count):
                # 随机生成学习时长（10-120分钟）
                duration = random.randint(10, 120)
                # 随机选择科目和备注
                subject = random.choice(subjects)
                note = random.choice(notes)
                # 随机生成时间（最近30天内）
                session_time = datetime.now() - timedelta(days=random.randint(0, 29))
                
                StudySession.objects.create(
                    user=user,
                    subject=subject,
                    duration_minutes=duration,
                    notes=note,
                    start_time=session_time
                )
        
        # 更新用户累计学习时长
        total_minutes = StudySession.objects.filter(user=user).aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        
        profile = UserProfile.objects.get(user=user)
        profile.total_study_time = total_minutes / 60.0
        profile.streak_days = random.randint(5, 15)  # 随机生成5-15天连续学习
        profile.save()
        
        # 更新用户学习状态
        study_status = UserStudyStatus.objects.get(user=user)
        study_status.cumulative_study_time = profile.total_study_time
        study_status.template_completion_rate = random.randint(20, 80)  # 随机生成20-80%完成率
        study_status.save()
        
        self.stdout.write(self.style.SUCCESS('学习会话数据已生成'))
        
        # 生成每日进度数据
        self.stdout.write('生成每日进度数据...')
        
        for template in templates:
            modules = template.modules.all()
            # 为每个模板生成最近7天的每日进度
            for i in range(7):
                date = datetime.now().date() - timedelta(days=i)
                for module in modules:
                    # 随机生成完成量（0-目标值的120%）
                    actual_value = random.randint(0, int(module.target_value * 1.2))
                    DailyProgress.objects.create(
                        user=user,
                        module=module,
                        actual_value=actual_value,
                        date=date
                    )
        
        self.stdout.write(self.style.SUCCESS('每日进度数据已生成'))
        
        self.stdout.write(self.style.SUCCESS('所有学习数据已生成完成！'))