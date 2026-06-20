from django.shortcuts import render, redirect, reverse
from .models import TodoTask, UserProfile, StudyTemplate, TemplateModule, StudySession, UserStudyStatus, DailyProgress, LearningMaterial, AIChatHistory, AIChatMessage
from django.contrib.auth.models import User
from datetime import datetime
from django.contrib import messages
from django.db import models
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from django.views.decorators.cache import cache_page, cache_control
import random
import json
import os

# 导入AI生成模块
from .ai_generator import MultiSubjectAIGenerator


# 辅助函数：格式化日期为中文格式
def format_chinese_date(date_obj):
    """将日期对象格式化为中文日期格式：YYYY年MM月DD日"""
    return f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"


def home(request):
    # 1. 获取当前登录用户
    user = request.user
    
    # 2. 如果用户未登录，重定向到登录页面
    if not user.is_authenticated:
        return redirect('login')

    # 3. 从数据库获取用户数据，确保数据准确性
    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # 重新计算用户的累计学习时长，确保数据准确
        total_minutes = StudySession.objects.filter(user=user).aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        profile.total_study_time = total_minutes / 60.0  # 转换为小时
        profile.save()
        
        # 缓存最新的profile数据
        cache_key = f'user_profile_{user.id}'
        cache.set(cache_key, profile, timeout=3600)  # 缓存1小时
    except Exception as e:
        # 如果数据库查询失败（如缺少字段），创建一个简单的profile对象
        profile = type('Profile', (), {
            'total_study_time': 0.0,
            'streak_days': 0
        })()

    # 4. 获取任务清单：按优先级排序（高H->中M->低L），并按创建时间倒序
    db_todos = TodoTask.objects.filter(user=user).order_by('-created_at') if user else []

    # 5. 从缓存获取学习模板（示例模板 + 用户创建的模板）
    cache_key = f'user_templates_{user.id}'
    user_templates = cache.get(cache_key)
    
    if not user_templates:
        user_templates = StudyTemplate.objects.filter(
            Q(is_example=True) | Q(creator=user)
        )
        cache.set(cache_key, user_templates, timeout=3600)  # 缓存1小时
    
    all_templates = user_templates
    
    # 5. 根据请求参数或默认选择模板
    selected_template_id = request.GET.get('template_id')
    if selected_template_id:
        # 确保用户只能访问自己创建的模板或示例模板
        current_plan = StudyTemplate.objects.filter(
            Q(id=selected_template_id) & (Q(is_example=True) | Q(creator=user))
        ).first()
    else:
        # 默认选择第一个模板
        current_plan = all_templates.first()
    
    plan_modules = []
    overall_progress = 0

    if current_plan:
        plan_modules = current_plan.modules.all()
        # 这里使用实际数据计算总进度
        plan_modules_list = []
        total_p = 0
        
        # 获取当前用户的所有每日进度记录
        user = request.user
        user_progress = DailyProgress.objects.filter(user=user)
        
        # 生成模块进度数据
        for m in plan_modules:
            # 查找该模块的所有进度记录
            module_progress = user_progress.filter(module=m)
            if module_progress.exists() and m.target_value:
                # 计算总完成量
                total_actual = sum(p.actual_value for p in module_progress)
                # 计算进度百分比，最大为100%
                percent = min(int((total_actual / m.target_value) * 100), 100)
            else:
                # 没有进度记录或目标值，进度为0
                percent = 0
            m_data = {'name': m.name, 'percent': percent, 'color': m.color_code}
            plan_modules_list.append(m_data)
            total_p += percent
        
        overall_progress = int(total_p / len(plan_modules)) if plan_modules else 0
        plan_modules = plan_modules_list

    # 5. 时间与问候语
    now = datetime.now()
    hour = now.hour
    if hour < 12:
        greeting = "早安"
    elif hour < 18:
        greeting = "下午好"
    else:
        greeting = "晚上好"

    # 6. 玩偶状态判断逻辑
    doll_is_active = True
    doll_status_text = "元气满满"
    doll_message = "数据库已连接，快开始今天的专注吧！"
    
    if user:
        # 获取用户学习状态和扩展信息
        study_status, created = UserStudyStatus.objects.get_or_create(user=user)
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # 判断逻辑：综合考虑多个学习数据指标
        from datetime import timedelta
        seven_days_ago = now - timedelta(days=7)
        
        # 计算近7天学习时长
        recent_sessions = StudySession.objects.filter(
            user=user,
            start_time__gte=seven_days_ago
        )
        recent_study_minutes = recent_sessions.aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        
        avg_daily_minutes = recent_study_minutes / 7.0  # 日均学习分钟数
        avg_daily_hours = avg_daily_minutes / 60.0  # 转换为小时
        
        # 计算连续学习天数
        streak_days = profile.streak_days
        
        # 模板完成率
        template_completion = study_status.template_completion_rate
        
        # 今日是否学习
        today_studied = recent_sessions.filter(
            start_time__date=now.date()
        ).exists()
        
        # 综合判断玩偶状态
        # 情况1：今天还没学习，提醒用户
        if not today_studied:
            doll_is_active = False
            doll_status_text = "等待学习"
            doll_message = "今天还没开始学习哦，赶紧行动起来吧！"
        # 情况2：近7天日均学习时长不足30分钟，连续天数也很少
        elif avg_daily_hours < 0.5 and streak_days < 3:
            doll_is_active = False
            doll_status_text = "有点懒惰"
            doll_message = "最近学习不够积极哦，每天坚持一点，进步会很大！"
        # 情况3：近7天日均学习时长不足1小时
        elif avg_daily_hours < 1.0:
            doll_is_active = True
            doll_status_text = "继续加油"
            doll_message = "学习时长还可以更长一点，坚持就是胜利！"
        # 情况4：连续学习天数较少
        elif streak_days < 5:
            doll_is_active = True
            doll_status_text = "逐渐进步"
            doll_message = "已经连续学习了{{ streak_days }}天，继续保持！"
        # 情况5：模板完成率较低
        elif template_completion < 50:
            doll_is_active = True
            doll_status_text = "稳步前进"
            doll_message = "学习计划完成率已达{{ template_completion|int }}%，继续努力！"
        # 情况6：表现优秀
        else:
            doll_is_active = True
            doll_status_text = "太棒了"
            doll_message = "学习状态极佳，继续保持这个节奏！"
        
        # 将变量插入到消息中
        doll_message = doll_message.replace('{{ streak_days }}', str(streak_days))
        doll_message = doll_message.replace('{{ template_completion|int }}', str(int(template_completion)))
    
    # 6. 为每个模板生成模块数据，存储在templates_with_modules字典中
    templates_with_modules = {}
    user = request.user
    # 获取当前用户的所有每日进度记录
    user_progress = DailyProgress.objects.filter(user=user)
    
    # 用于计算所有模板的平均进度
    all_templates_progress = []
    
    for template in all_templates:
        template_modules = template.modules.all()
        template_plan_modules = []
        template_total_p = 0
        
        # 生成模块进度数据
        for m in template_modules:
            # 查找该模块的所有进度记录
            module_progress = user_progress.filter(module=m)
            if module_progress.exists() and m.target_value:
                # 计算总完成量
                total_actual = sum(p.actual_value for p in module_progress)
                # 计算进度百分比，最大为100%
                percent = min(int((total_actual / m.target_value) * 100), 100)
            else:
                # 没有进度记录或目标值，进度为0
                percent = 0
            m_data = {'name': m.name, 'percent': percent, 'color': m.color_code}
            template_plan_modules.append(m_data)
            template_total_p += percent
        
        # 计算当前模板的进度
        template_progress = int(template_total_p / len(template_modules)) if template_modules else 0
        all_templates_progress.append(template_progress)
        
        templates_with_modules[template.id] = template_plan_modules
        
        # 清除相关缓存
        cache.delete(f'progress_dashboard_{user.id}_{template.id}')
    
    # 计算所有模板的平均进度作为总进度
    if all_templates_progress:
        overall_progress = int(sum(all_templates_progress) / len(all_templates_progress))
    else:
        overall_progress = 0
    
    # 8. 添加真实的每日学习时间数据
    from datetime import timedelta
    import calendar
    
    # 获取近7天日期
    seven_days_ago = datetime.now() - timedelta(days=6)  # 包括今天共7天
    recent_dates = [(seven_days_ago + timedelta(days=i)).date() for i in range(7)]
    
    # 设置每日学习数据的标签为星期几
    daily_labels = [calendar.day_name[d.weekday()] for d in recent_dates]
    daily_labels = [d.replace('Monday', '周一').replace('Tuesday', '周二').replace('Wednesday', '周三').replace('Thursday', '周四').replace('Friday', '周五').replace('Saturday', '周六').replace('Sunday', '周日') for d in daily_labels]
    
    # 获取近7天学习记录
    recent_sessions = StudySession.objects.filter(
        user=user,
        start_time__gte=seven_days_ago
    )
    
    # 统计每天的学习时长
    daily_study_time = {d: 0 for d in recent_dates}
    for session in recent_sessions:
        session_date = session.start_time.date()
        if session_date in daily_study_time:
            daily_study_time[session_date] += session.duration_minutes
    
    # 转换为图表数据格式
    daily_study_data = [daily_study_time[d] for d in recent_dates]
    
    # 7. 构造干净的上下文
    import json
    
    # 将模板数据转换为JSON格式，以便在JavaScript中使用
    templates_json = json.dumps([{
        'id': template.id,
        'name': template.name,
        'description': template.description
    } for template in all_templates])
    
    # 确保templates_with_modules中的日期类型被正确转换
    templates_with_modules_json = json.dumps(templates_with_modules)
    
    context = {
        'greeting': greeting,
        'today_date': format_chinese_date(now),
        'motto': "博观而约取，厚积而薄发。",
        'user_info': {
            'nickname': user.username if user else "访客",
            'total_hours': profile.total_study_time if profile else 0.0,
            'streak_days': profile.streak_days if profile else 0,
        },
        'profile': profile,  # 添加完整profile对象，用于访问自定义玩偶图片
        'todo_list': db_todos,
        'doll': {
            'is_active': doll_is_active,
            'status_text': doll_status_text,
            'message': doll_message,
        },
        'plan': {
            'name': current_plan.name if current_plan else "暂无计划",
            'percent': overall_progress,
            'modules': plan_modules
        },
        'templates': all_templates,
        'templates_with_modules': templates_with_modules,
        'templates_json': templates_json,
        'templates_with_modules_json': templates_with_modules_json,
        'selected_template_id': selected_template_id,
        'daily_study_labels': daily_labels,
        'daily_study_data': daily_study_data
    }
    return render(request, 'home.html', context)


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
        
        # 清除学习页面缓存（逐个清除，兼容LocMemCache）
        cache.delete('cet4_study_None')  # 清除默认CET-4学习页面缓存
        cache.delete('c_language_study_None')  # 清除默认C语言学习页面缓存
        cache.delete('politics_study_None')  # 清除默认政治学习页面缓存
        
        # 清除特定模块的学习页面缓存
        # CET-4模块
        cet4_template = StudyTemplate.objects.filter(name='英语四级').first()
        if cet4_template:
            cet4_modules = cet4_template.modules.all()
            for module in cet4_modules:
                cache.delete(f'cet4_study_{module.name}')
        
        # C语言模块
        c_language_template = StudyTemplate.objects.filter(name='专升本C语言').first()
        if c_language_template:
            c_modules = c_language_template.modules.all()
            for module in c_modules:
                cache.delete(f'c_language_study_{module.name}')
        
        # 政治模块
        politics_template = StudyTemplate.objects.filter(name='专升本政治').first()
        if politics_template:
            politics_modules = politics_template.modules.all()
            for module in politics_modules:
                cache.delete(f'politics_study_{module.name}')
        
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


@cache_page(600)  # 缓存10分钟
@login_required
@cache_control(private=True)  # 仅私有缓存，不共享给其他用户
def daily_progress(request):
    """每日进度填写页面"""
    # 1. 获取所有学习模板（示例模板 + 用户创建的模板）
    templates = StudyTemplate.objects.filter(
        Q(is_example=True) | Q(creator=request.user)
    )
    
    # 2. 获取所有模板的模块数据，转换为JSON格式
    templates_with_modules = {}
    for template in templates:
        modules = []
        for module in template.modules.all():
            # 获取当前登录用户
            user = request.user
            
            # 计算累计完成量
            total_actual_value = 0
            completion_rate = 0
            is_completed = False
            
            if user:
                total_actual_value = DailyProgress.objects.filter(
                    user=user,
                    module=module
                ).aggregate(total=models.Sum('actual_value'))['total'] or 0
                
                # 计算完成率
                if module.target_value is not None and module.target_value > 0:
                    completion_rate = int((total_actual_value / module.target_value) * 100)
                    is_completed = completion_rate >= 100
            
            # 只获取需要的字段，不包含_state对象
            module_data = {
                'id': module.id,
                'name': module.name,
                'target_value': module.target_value,
                'target_type': module.target_type,
                'total_actual_value': total_actual_value,
                'completion_rate': completion_rate,
                'is_completed': is_completed
            }
            
            modules.append(module_data)
        templates_with_modules[template.id] = modules
    
    # 3. 获取URL参数中的template_id
    template_id = request.GET.get('template_id')
    
    # 4. 构造上下文
    now = datetime.now()
    context = {
        'today_date': format_chinese_date(now),
        'templates': templates,
        'templates_with_modules': templates_with_modules,
        'selected_template_id': template_id
    }
    
    return render(request, 'daily_progress_form.html', context)


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
        
        # 清除学习页面缓存（逐个清除，兼容LocMemCache）
        cache.delete('cet4_study_None')  # 清除默认CET-4学习页面缓存
        cache.delete('c_language_study_None')  # 清除默认C语言学习页面缓存
        
        # 清除特定模块的学习页面缓存
        # CET-4模块
        cet4_template = StudyTemplate.objects.filter(name='英语四级').first()
        if cet4_template:
            cet4_modules = cet4_template.modules.all()
            for module in cet4_modules:
                cache.delete(f'cet4_study_{module.name}')
        
        # C语言模块
        c_language_template = StudyTemplate.objects.filter(name='专升本C语言').first()
        if c_language_template:
            c_modules = c_language_template.modules.all()
            for module in c_modules:
                cache.delete(f'c_language_study_{module.name}')
        
        # 8. 返回成功消息
        messages.success(request, f'今日进度保存成功！已保存 {progress_saved} 个模块的数据')
        # 跳转到进度看板时传递当前模板ID，以便显示该模板的数据
        return redirect(f'{reverse("progress_dashboard")}?template_id={template_id}')
    
    # 如果是GET请求，重定向到进度填写页面
    return redirect('daily_progress')


# 用户系统视图

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


def logout_view(request):
    """用户注销"""
    logout(request)
    messages.success(request, '已成功注销')
    return redirect('login')


@cache_page(300)  # 缓存5分钟
@login_required
@cache_control(private=True)  # 仅私有缓存，不共享给其他用户
def profile_view(request):
    """个人中心"""
    # 1. 尝试从缓存获取用户资料
    cache_key = f'profile_view_{request.user.id}'
    cached_profile = cache.get(cache_key)
    
    if cached_profile and request.method == 'GET':
        return render(request, 'profile.html', cached_profile)
    
    # 2. 获取用户信息
    user = request.user
    
    try:
        profile = UserProfile.objects.get_or_create(user=user)[0]
    except Exception as e:
        # 如果数据库查询失败（如缺少字段），创建一个简单的profile对象
        profile = type('Profile', (), {
            'total_study_time': 0.0,
            'streak_days': 0,
            'doll_image': None  # 确保访问doll_image不会出错
        })()
    
    if request.method == 'POST':
        # 处理个人信息更新
        if 'email' in request.POST and request.POST.get('email'):
            # 个人信息编辑
            email = request.POST.get('email')
            if email:
                user.email = email
                user.save()
                messages.success(request, '个人信息已更新')
        
        # 处理密码修改
        if 'old_password' in request.POST and request.POST.get('old_password'):
            old_password = request.POST.get('old_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            if user.check_password(old_password):
                if new_password1 and new_password1 == new_password2:
                    user.set_password(new_password1)
                    user.save()
                    messages.success(request, '密码修改成功')
                    # 重新登录用户，因为密码已更改
                    login(request, user)
                else:
                    messages.error(request, '新密码不一致或为空')
            else:
                messages.error(request, '原密码错误')
        
        # 处理头像上传
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
            profile.save()
            messages.success(request, '头像已更新')
        
        # 处理玩偶图片上传
        if 'doll_image' in request.FILES:
            profile.doll_image = request.FILES['doll_image']
            profile.save()
            messages.success(request, '玩偶图片已更新')
        
        # 清除缓存，确保数据实时性
        cache.delete(f'user_profile_{user.id}')
        cache.delete(cache_key)
        return redirect('profile')
    
    context = {
        'user': user,
        'profile': profile
    }
    
    # 缓存个人中心页面
    cache.set(cache_key, context, 300)
    
    return render(request, 'profile.html', context)


@login_required
def export_study_data(request):
    """导出学习数据"""
    from django.http import HttpResponse
    import csv
    from datetime import datetime
    
    # 获取当前用户
    user = request.user
    
    # 准备响应
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="study_data_{user.username}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    # 创建CSV写入器
    writer = csv.writer(response)
    
    # 写入学习会话数据
    writer.writerow(['学习会话数据'])
    writer.writerow(['日期', '科目', '时长（分钟）', '备注'])
    
    sessions = StudySession.objects.filter(user=user).order_by('-start_time')
    for session in sessions:
        writer.writerow([
            session.start_time.strftime('%Y-%m-%d %H:%M'),
            session.subject,
            session.duration_minutes,
            session.notes or ''
        ])
    
    # 写入空行分隔
    writer.writerow([])
    writer.writerow([])
    
    # 写入每日进度数据
    writer.writerow(['每日进度数据'])
    writer.writerow(['日期', '模板', '模块', '完成量', '目标量'])
    
    progress_records = DailyProgress.objects.filter(user=user).order_by('-date')
    for record in progress_records:
        writer.writerow([
            record.date.strftime('%Y-%m-%d'),
            record.module.template.name,
            record.module.name,
            record.actual_value,
            record.module.target_value
        ])
    
    return response


# 任务管理视图

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
            
            # 清除各学科学习页面缓存
            # 由于LocMemCache不支持delete_pattern，我们只删除主模板缓存
            # 学习页面缓存会在下次访问时自动重新生成
            
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
                
                # 清除所有可能的模板ID缓存
                templates = StudyTemplate.objects.all()
                for t in templates:
                    cache.delete(f'progress_dashboard_{request.user.id}_{t.id}')
                    # 清除study_base视图缓存
                    cache.delete(f'study_base_{t.id}_')
                    cache.delete(f'study_base_{t.id}_None')
                    # 清除study_base视图的所有模块缓存
                    for module in t.modules.all():
                        cache.delete(f'study_base_{t.id}_{module.name}')
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
                
                # 清除所有可能的模板ID缓存
                templates = StudyTemplate.objects.all()
                for t in templates:
                    cache.delete(f'progress_dashboard_{request.user.id}_{t.id}')
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
            
            # 清除所有可能的模板ID缓存
            templates = StudyTemplate.objects.all()
            for t in templates:
                cache.delete(f'progress_dashboard_{request.user.id}_{t.id}')
        except TemplateModule.DoesNotExist:
            messages.error(request, '模块不存在')
    
    return redirect('template_management')


from django.http import JsonResponse

def update_template_order(request):
    """更新模板顺序"""
    if request.method == 'POST':
        try:
            import json
            order_data = json.loads(request.body)
            
            # 更新每个模板的顺序
            for item in order_data:
                template_id = item.get('id')
                order = item.get('order')
                if template_id and order is not None:
                    template = StudyTemplate.objects.get(id=template_id)
                    template.order = order
                    template.save()
            
            return JsonResponse({'success': True, 'message': '模板顺序更新成功'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


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
                return JsonResponse({'success': False, 'message': 'AI生成失败，请检查API配置'})
            
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
            
            # 如果没有生成足够的模块，添加默认模块
            if module_count == 0:
                # 添加一些默认模块
                default_modules = ['基础知识', '核心考点', '典型例题', '模拟练习']
                for i, module_name in enumerate(default_modules):
                    TemplateModule.objects.create(
                        template=study_template,
                        name=module_name,
                        target_value=100,
                        target_type='numeric',
                        color_code=colors[i % len(colors)]
                    )
            
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


@login_required
def ai_chat(request):
    """AI对话页面"""
    # 获取用户的所有对话历史
    chat_histories = AIChatHistory.objects.filter(user=request.user)
    
    # 获取当前对话ID，如果没有则使用第一个对话
    current_chat_id = request.GET.get('chat_id')
    current_chat = None
    current_messages = []
    
    if current_chat_id:
        try:
            current_chat = AIChatHistory.objects.get(id=current_chat_id, user=request.user)
            current_messages = current_chat.messages.all()
        except AIChatHistory.DoesNotExist:
            current_chat = None
    
    # 如果没有当前对话且有历史对话，使用第一个
    if not current_chat and chat_histories.exists():
        current_chat = chat_histories.first()
        current_messages = current_chat.messages.all()
    
    context = {
        'chat_histories': chat_histories,
        'current_chat': current_chat,
        'current_messages': current_messages
    }
    
    return render(request, 'ai_chat.html', context)


@login_required
def create_chat(request):
    """创建新对话"""
    if request.method == 'POST':
        chat_name = request.POST.get('chat_name', '新对话')
        
        # 创建新对话
        chat_history = AIChatHistory.objects.create(
            user=request.user,
            chat_name=chat_name
        )
        
        return JsonResponse({
            'success': True,
            'chat_id': chat_history.id,
            'chat_name': chat_history.chat_name
        })
    
    return JsonResponse({'success': False, 'message': '无效请求'})


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
            try:
                ai_response = generator._call_modelscope_api(
                    prompt=prompt,
                    max_tokens=2000,
                    temperature=0.7
                )
            except Exception as api_error:
                error_msg = str(api_error)
                if '401' in error_msg or 'Authentication' in error_msg:
                    ai_response = "抱歉，AI服务认证失败，请检查API密钥配置。"
                else:
                    ai_response = f"抱歉，AI服务暂时不可用：{error_msg}"
            
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
            return JsonResponse({'success': False, 'message': f'对话失败：{str(e)}'})
    
    return JsonResponse({'success': False, 'message': '无效请求'})


@login_required
def get_chat_messages(request):
    """获取指定对话的所有消息"""
    if request.method == 'GET':
        chat_id = request.GET.get('chat_id')
        
        if not chat_id:
            return JsonResponse({'success': False, 'message': '缺少对话ID'})
        
        try:
            chat_history = AIChatHistory.objects.get(id=chat_id, user=request.user)
            messages = list(chat_history.messages.all().values(
                'id', 'role', 'content', 'created_at'
            ))
            
            # 格式化日期
            for msg in messages:
                msg['created_at'] = msg['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return JsonResponse({
                'success': True,
                'messages': messages,
                'chat_name': chat_history.chat_name
            })
        except AIChatHistory.DoesNotExist:
            return JsonResponse({'success': False, 'message': '对话不存在'})
    
    return JsonResponse({'success': False, 'message': '无效请求'})


@login_required
def rename_chat(request):
    """重命名对话"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            chat_id = data.get('chat_id')
            new_name = data.get('new_name')
            
            if not chat_id or not new_name:
                return JsonResponse({'success': False, 'message': '缺少必要参数'})
            
            chat_history = AIChatHistory.objects.get(id=chat_id, user=request.user)
            chat_history.chat_name = new_name
            chat_history.save()
            
            return JsonResponse({'success': True, 'chat_name': new_name})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': '无效请求'})


@login_required
def delete_chat(request):
    """删除对话"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            chat_id = data.get('chat_id')
            
            if not chat_id:
                return JsonResponse({'success': False, 'message': '缺少对话ID'})
            
            chat_history = AIChatHistory.objects.get(id=chat_id, user=request.user)
            chat_history.delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': '无效请求'})


@login_required
def generate_ai_template_step1(request):
    """AI生成模板第一步：输入基础信息"""
    return JsonResponse({
        'success': True,
        'step': 1,
        'message': '请输入学科和考试类型'
    })


@login_required
def generate_ai_template_step2(request):
    """AI生成模板第二步：生成框架"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subject_name = data.get('subject', '')
            exam_type = data.get('exam_type', '通用考试')
            
            if not subject_name:
                return JsonResponse({'success': False, 'step': 2, 'message': '学科名称不能为空'})
            
            # 初始化AI生成器
            generator = MultiSubjectAIGenerator()
            
            # 生成学科知识框架
            framework = generator.generate_subject_framework(subject_name, exam_type)
            
            if not framework:
                return JsonResponse({'success': False, 'step': 2, 'message': 'AI生成框架失败，请检查API配置'})
            
            # 返回生成的框架
            return JsonResponse({
                'success': True,
                'step': 2,
                'message': '框架生成成功',
                'framework': framework
            })
        except Exception as e:
            error_msg = str(e)
            # 如果是认证错误，给出更明确的提示
            if '401' in error_msg or 'Authentication' in error_msg:
                error_msg = 'API认证失败，请检查ModelScope API Key是否有效'
            elif 'timeout' in error_msg.lower():
                error_msg = 'API请求超时，请稍后重试'
            return JsonResponse({'success': False, 'step': 2, 'message': f'AI生成失败：{error_msg}'})
    
    return JsonResponse({'success': False, 'step': 2, 'message': '无效的请求方式'})


@login_required
def generate_ai_template_step3(request):
    """AI生成模板第三步：保存模板"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subject_name = data.get('subject', '')
            exam_type = data.get('exam_type', '通用考试')
            framework = data.get('framework', {})
            goal = data.get('goal', '')
            
            if not subject_name or not framework:
                return JsonResponse({'success': False, 'step': 3, 'message': '缺少必要参数'})
            
            # 创建学习模板
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
            cache.delete('all_templates')
            cache.delete(f'user_templates_{request.user.id}')
            
            # 返回成功响应
            return JsonResponse({
                'success': True,
                'step': 3,
                'message': '模板生成成功',
                'template_id': study_template.id,
                'template_name': study_template.name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'step': 3, 'message': f'保存失败：{str(e)}'})
    
    return JsonResponse({'success': False, 'step': 3, 'message': '无效的请求方式'})
    
    return JsonResponse({'success': False, 'message': '只允许POST请求'}, status=405)


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
                try:
                    content = generator.generate_learning_material(
                        subject_name=subject_name,
                        section_name=module.name,
                        chapter_names=[module.name],  # 使用模块名称作为章节名称
                        content_types=final_content_types,
                        exam_type=exam_type
                    )
                except Exception as api_error:
                    error_msg = str(api_error)
                    if '401' in error_msg or 'Authentication' in error_msg:
                        error_msg = 'API认证失败，请检查ModelScope API Key是否有效'
                    return JsonResponse({'success': False, 'message': f'学习资料生成失败：{error_msg}'})
                
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
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'获取学习资料失败：{str(e)}'})
    
    return JsonResponse({'success': False, 'message': '无效的请求方式'})


@cache_page(600)  # 缓存10分钟
@login_required
@cache_control(private=True)  # 仅私有缓存，不共享给其他用户
def study_base(request, template_id, module_name=None):
    """统一学习模板页面，支持不同学科的模板"""
    # 1. 获取当前登录用户
    user = request.user
    
    # 2. 尝试从缓存获取数据
    cache_key = f'study_base_{template_id}_{module_name}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'study_base.html', cached_data)
    
    # 3. 获取指定ID的模板，确保用户只能访问自己创建的模板或示例模板
    template = StudyTemplate.objects.filter(
        Q(id=template_id) & (Q(is_example=True) | Q(creator=user))
    ).first()
    
    if not template:
        messages.error(request, '您无权访问该学习模板')
        return redirect('template_management')
    
    # 3. 获取模板的所有模块
    modules = template.modules.all()
    
    # 4. 获取当前学习模块
    current_module = None
    if module_name:
        current_module = modules.filter(name=module_name).first()
    else:
        # 默认选择第一个模块
        current_module = modules.first()
    
    # 5. 生成学习进度数据
    study_progress = {
        'today_completed': 0,
        'total_completed': 0,
        'completion_rate': 0
    }
    
    # 根据模块名称生成不同的进度数据
    if current_module is not None:
        # 英语四级模块
        if template.name == "英语四级":
            if current_module.name == '词汇':
                study_progress = {
                    'today_completed': 85,
                    'total_completed': 1230,
                    'completion_rate': 61
                }
            elif current_module.name == '语法':
                study_progress = {
                    'today_completed': 15,
                    'total_completed': 450,
                    'completion_rate': 45
                }
            elif current_module.name == '听力':
                study_progress = {
                    'today_completed': 60,
                    'total_completed': 980,
                    'completion_rate': 72
                }
            elif current_module.name == '阅读':
                study_progress = {
                    'today_completed': 45,
                    'total_completed': 780,
                    'completion_rate': 58
                }
            elif current_module.name == '写作':
                study_progress = {
                    'today_completed': 10,
                    'total_completed': 230,
                    'completion_rate': 35
                }
            elif current_module.name == '翻译':
                study_progress = {
                    'today_completed': 25,
                    'total_completed': 650,
                    'completion_rate': 55
                }
            else:
                # 新添加的模块，默认进度为0
                study_progress = {
                    'today_completed': 0,
                    'total_completed': 0,
                    'completion_rate': 0
                }
        # 专升本C语言模块
        elif template.name == "专升本C语言":
            if current_module.name == '语法':
                study_progress = {
                    'today_completed': 25,
                    'total_completed': 320,
                    'completion_rate': 52
                }
            elif current_module.name == '编程题':
                study_progress = {
                    'today_completed': 12,
                    'total_completed': 190,
                    'completion_rate': 38
                }
            elif current_module.name == '知识点':
                study_progress = {
                    'today_completed': 35,
                    'total_completed': 650,
                    'completion_rate': 65
                }
            elif current_module.name == '模拟题':
                study_progress = {
                    'today_completed': 8,
                    'total_completed': 140,
                    'completion_rate': 28
                }
            else:
                # 新添加的模块，默认进度为0
                study_progress = {
                    'today_completed': 0,
                    'total_completed': 0,
                    'completion_rate': 0
                }
        # 专升本政治模块
        elif template.name == "专升本政治":
            if current_module.name == '概论':
                study_progress = {
                    'today_completed': 18,
                    'total_completed': 450,
                    'completion_rate': 62
                }
            elif current_module.name == '毛泽东思想':
                study_progress = {
                    'today_completed': 15,
                    'total_completed': 340,
                    'completion_rate': 45
                }
            elif current_module.name == '邓小平理论':
                study_progress = {
                    'today_completed': 25,
                    'total_completed': 560,
                    'completion_rate': 70
                }
            elif current_module.name == '三个代表':
                study_progress = {
                    'today_completed': 12,
                    'total_completed': 330,
                    'completion_rate': 55
                }
            elif current_module.name == '科学发展观':
                study_progress = {
                    'today_completed': 20,
                    'total_completed': 420,
                    'completion_rate': 68
                }
            else:
                # 新添加的模块，默认进度为0
                study_progress = {
                    'today_completed': 0,
                    'total_completed': 0,
                    'completion_rate': 0
                }
        # 其他模板默认进度为0
        else:
            study_progress = {
                'today_completed': 0,
                'total_completed': 0,
                'completion_rate': 0
            }
    
    # 6. 获取当前模块的学习资料
    learning_materials = []
    if current_module:
        learning_materials = LearningMaterial.objects.filter(module=current_module).order_by('-generated_at')
    
    # 7. 构造上下文
    context = {
        'template_id': template_id,
        'template_name': template.name,
        'modules': modules,
        'current_module': current_module,
        'study_progress': study_progress,
        'learning_materials': learning_materials,
        'template': template  # 添加模板对象到上下文，用于AI生成按钮
    }
    
    # 7. 缓存数据
    cache.set(cache_key, context, 600)  # 缓存10分钟
    
    return render(request, 'study_base.html', context)

@cache_page(600)  # 缓存10分钟
@login_required
@cache_control(private=True)  # 仅私有缓存，不共享给其他用户
def cet4_study(request, module_name=None):
    """CET-4模块学习页面"""
    # 1. 尝试从缓存获取数据
    cache_key = f'cet4_study_{module_name}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'cet4_study.html', cached_data)
    
    # 2. 获取CET-4模板
    cet4_template = StudyTemplate.objects.filter(name='英语四级').first()
    
    if not cet4_template:
        messages.error(request, 'CET-4模板不存在')
        return redirect('template_management')
    
    # 3. 获取所有CET-4模块
    modules = cet4_template.modules.all()
    
    # 4. 获取当前学习模块
    current_module = None
    if module_name:
        current_module = modules.filter(name=module_name).first()
    else:
        # 默认选择第一个模块
        current_module = modules.first()
    
    # 5. 生成学习进度数据，根据模块名称生成不同的进度
    study_progress = {
        'today_completed': 0,
        'total_completed': 0,
        'completion_rate': 0
    }
    
    # 根据模块名称生成不同的进度数据
    if current_module is not None:
        if current_module.name == '词汇':
            study_progress = {
                'today_completed': 85,
                'total_completed': 1230,
                'completion_rate': 61
            }
        elif current_module.name == '语法':
            study_progress = {
                'today_completed': 15,
                'total_completed': 450,
                'completion_rate': 45
            }
        elif current_module.name == '听力':
            study_progress = {
                'today_completed': 60,
                'total_completed': 980,
                'completion_rate': 72
            }
        elif current_module.name == '阅读':
            study_progress = {
                'today_completed': 45,
                'total_completed': 780,
                'completion_rate': 58
            }
        elif current_module.name == '写作':
            study_progress = {
                'today_completed': 10,
                'total_completed': 230,
                'completion_rate': 35
            }
        elif current_module.name == '翻译':
            study_progress = {
                'today_completed': 25,
                'total_completed': 650,
                'completion_rate': 55
            }
    
    context = {
        'template': cet4_template,
        'modules': modules,
        'current_module': current_module,
        'study_progress': study_progress,
        'subject_name': '英语四级',
        'subject_type': 'cet4',
        'icon_type': 'book'
    }
    
    # 6. 缓存数据
    cache.set(cache_key, context, 600)
    
    return render(request, 'study_base.html', context)

@login_required
def cet4_materials(request, module_name=None):
    """CET-4模块学习资料页面"""
    # 获取CET-4模板
    cet4_template = StudyTemplate.objects.filter(name='英语四级').first()
    
    if not cet4_template:
        messages.error(request, 'CET-4模板不存在')
        return redirect('template_management')
    
    # 获取所有CET-4模块
    modules = cet4_template.modules.all()
    
    # 获取当前学习模块
    current_module = None
    if module_name:
        current_module = modules.filter(name=module_name).first()
    else:
        # 默认选择第一个模块
        current_module = modules.first()
    
    context = {
        'template': cet4_template,
        'modules': modules,
        'current_module': current_module
    }
    
    # 根据模块名称渲染不同的模板
    if current_module and current_module.name == '词汇':
        return render(request, 'cet4_vocab_materials.html', context)
    else:
        # 其他模块暂时使用通用模板
        return render(request, 'cet4_materials.html', context)


@cache_page(600)  # 缓存10分钟
@login_required
@cache_control(private=True)  # 仅私有缓存，不共享给其他用户
def c_language_study(request, module_name=None):
    """专升本C语言模块学习页面"""
    # 1. 尝试从缓存获取数据
    cache_key = f'c_language_study_{module_name}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'c_language_study.html', cached_data)
    
    # 2. 获取专升本C语言模板
    c_language_template = StudyTemplate.objects.filter(name='专升本C语言').first()
    
    if not c_language_template:
        messages.error(request, '专升本C语言模板不存在')
        return redirect('template_management')
    
    # 3. 获取所有专升本C语言模块
    modules = c_language_template.modules.all()
    
    # 4. 获取当前学习模块
    current_module = None
    if module_name:
        current_module = modules.filter(name=module_name).first()
    else:
        # 默认选择第一个模块
        current_module = modules.first()
    
    # 5. 生成学习进度数据，根据模块名称生成不同的进度
    study_progress = {
        'today_completed': 0,
        'total_completed': 0,
        'completion_rate': 0
    }
    
    # 根据模块名称生成不同的进度数据
    if current_module is not None:
        if current_module.name == '语法':
            study_progress = {
                'today_completed': 25,
                'total_completed': 520,
                'completion_rate': 52
            }
        elif current_module.name == '编程题':
            study_progress = {
                'today_completed': 8,
                'total_completed': 380,
                'completion_rate': 38
            }
        elif current_module.name == '知识点':
            study_progress = {
                'today_completed': 45,
                'total_completed': 650,
                'completion_rate': 65
            }
        elif current_module.name == '模拟题':
            study_progress = {
                'today_completed': 5,
                'total_completed': 280,
                'completion_rate': 28
            }
    
    context = {
        'template': c_language_template,
        'modules': modules,
        'current_module': current_module,
        'study_progress': study_progress,
        'subject_name': '专升本C语言',
        'subject_type': 'c_language',
        'icon_type': 'code'
    }
    
    # 6. 缓存数据
    cache.set(cache_key, context, 600)
    
    return render(request, 'study_base.html', context)


@login_required
def c_language_materials(request, module_name=None):
    """专升本C语言模块学习资料页面"""
    # 获取专升本C语言模板
    c_language_template = StudyTemplate.objects.filter(name='专升本C语言').first()
    
    if not c_language_template:
        messages.error(request, '专升本C语言模板不存在')
        return redirect('template_management')
    
    # 获取所有专升本C语言模块
    modules = c_language_template.modules.all()
    
    # 获取当前学习模块
    current_module = None
    if module_name:
        current_module = modules.filter(name=module_name).first()
    else:
        # 默认选择第一个模块
        current_module = modules.first()
    
    context = {
        'template': c_language_template,
        'modules': modules,
        'current_module': current_module
    }
    
    # 根据模块名称渲染不同的模板
    if current_module and current_module.name == '词汇':
        return render(request, 'c_language_vocab_materials.html', context)
    else:
        # 其他模块暂时使用通用模板
        return render(request, 'c_language_materials.html', context)


@cache_page(600)  # 缓存10分钟
@login_required
@cache_control(private=True)  # 仅私有缓存，不共享给其他用户
def politics_study(request, module_name=None):
    """专升本政治模块学习页面"""
    # 1. 尝试从缓存获取数据
    cache_key = f'politics_study_{module_name}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'study_base.html', cached_data)
    
    # 2. 获取政治模板
    politics_template = StudyTemplate.objects.filter(name='专升本政治').first()
    
    if not politics_template:
        messages.error(request, '政治模板不存在')
        return redirect('template_management')
    
    # 3. 获取所有政治模块
    modules = politics_template.modules.all()
    
    # 4. 获取当前学习模块
    current_module = None
    if module_name:
        current_module = modules.filter(name=module_name).first()
    else:
        # 默认选择第一个模块
        current_module = modules.first()
    
    # 5. 生成学习进度数据，根据模块名称生成不同的进度
    study_progress = {
        'today_completed': 0,
        'total_completed': 0,
        'completion_rate': 0
    }
    
    # 初始进度全部为0，等待用户实际学习后更新
    if current_module is not None:
        study_progress = {
            'today_completed': 0,
            'total_completed': 0,
            'completion_rate': 0
        }
    
    context = {
        'template': politics_template,
        'modules': modules,
        'current_module': current_module,
        'study_progress': study_progress,
        'subject_name': '专升本政治',
        'subject_type': 'politics',
        'icon_type': 'book-open'
    }
    
    # 6. 缓存数据
    cache.set(cache_key, context, 600)
    
    return render(request, 'study_base.html', context)


@login_required
def politics_materials(request, module_name=None):
    """专升本政治模块学习资料页面"""
    # 获取政治模板
    politics_template = StudyTemplate.objects.filter(name='专升本政治').first()
    
    if not politics_template:
        messages.error(request, '政治模板不存在')
        return redirect('template_management')
    
    # 获取所有政治模块
    modules = politics_template.modules.all()
    
    # 获取当前学习模块
    current_module = None
    if module_name:
        current_module = modules.filter(name=module_name).first()
    else:
        # 默认选择第一个模块
        current_module = modules.first()
    
    context = {
        'template': politics_template,
        'modules': modules,
        'current_module': current_module,
        'subject_name': '专升本政治',
        'subject_type': 'politics'
    }
    
    # 使用政治资料模板
    return render(request, 'politics_materials.html', context)


def study_heatmap_api(request):
    """返回用户学习热力图数据（最近84天）"""
    from django.http import JsonResponse
    from datetime import timedelta, date
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': '未登录'}, status=401)
    
    today = date.today()
    start_date = today - timedelta(days=83)  # 84天（12周）
    
    # 查询所有 StudySession
    sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date__gte=start_date,
        start_time__date__lte=today
    ).values('start_time__date').annotate(
        total_minutes=models.Sum('duration_minutes')
    )
    
    # 构建日期到分钟数的映射
    study_map = {}
    for s in sessions:
        d = s['start_time__date']
        study_map[d.isoformat()] = s['total_minutes'] or 0
    
    # 构建84天数据
    heatmap_data = []
    current = start_date
    while current <= today:
        iso = current.isoformat()
        minutes = study_map.get(iso, 0)
        
        # 确定颜色等级
        if minutes <= 0:
            level = 0
        elif minutes <= 30:
            level = 1
        elif minutes <= 60:
            level = 2
        elif minutes <= 120:
            level = 3
        else:
            level = 4
        
        heatmap_data.append({
            'date': iso,
            'minutes': minutes,
            'level': level,
        })
        current += timedelta(days=1)
    
    # 连续学习天数
    profile = UserProfile.objects.filter(user=request.user).first()
    streak = profile.streak_days if profile else 0
    
    # 累计学习时长
    total_hours = profile.total_study_time if profile else 0
    
    return JsonResponse({
        'heatmap': heatmap_data,
        'streak': streak,
        'total_hours': round(total_hours, 1),
    })