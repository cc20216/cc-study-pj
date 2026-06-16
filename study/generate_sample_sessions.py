from study_dashboard.models import StudySession
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import random

# 获取第一个用户
user = User.objects.first()

# 删除现有会话数据
StudySession.objects.filter(user=user).delete()

# 生成近7天的示例数据
for i in range(7):
    date = datetime.now() - timedelta(days=i)
    # 每天生成1-3个学习会话
    for j in range(random.randint(1, 3)):
        duration = random.randint(20, 90)  # 20-90分钟
        end_time = date + timedelta(minutes=duration)
        session = StudySession.objects.create(
            user=user,
            subject='英语',
            start_time=date,
            end_time=end_time,
            duration_minutes=duration
        )
        print(f'Generated session: {session.start_time} {session.duration_minutes} minutes')

# 生成一些其他科目数据
StudySession.objects.create(
    user=user,
    subject='C语言',
    start_time=datetime.now() - timedelta(days=3),
    end_time=datetime.now() - timedelta(days=3) + timedelta(minutes=60),
    duration_minutes=60
)

StudySession.objects.create(
    user=user,
    subject='数学',
    start_time=datetime.now() - timedelta(days=5),
    end_time=datetime.now() - timedelta(days=5) + timedelta(minutes=45),
    duration_minutes=45
)

print(f'Total sessions created: {StudySession.objects.filter(user=user).count()}')
