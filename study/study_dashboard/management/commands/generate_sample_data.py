from django.core.management.base import BaseCommand
from study_dashboard.models import StudyTemplate, TemplateModule

class Command(BaseCommand):
    help = '生成示例学习模板和模块数据'

    def handle(self, *args, **kwargs):
        # 清理现有数据
        self.stdout.write('清理现有数据...')
        TemplateModule.objects.all().delete()
        StudyTemplate.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('现有数据已清理'))

        # 创建英语四级模板
        self.stdout.write('创建英语四级模板...')
        cet4_template, created = StudyTemplate.objects.get_or_create(
            name='英语四级',
            defaults={'description': '英语四级考试学习计划，包含词汇、语法、听力、阅读、写作、翻译六个模块，帮助全面提升英语能力。'}
        )
        
        # 添加英语四级模块
        cet4_modules = [
            {'name': '词汇', 'target_value': 100, 'color_code': '#81C784'},
            {'name': '语法', 'target_value': 20, 'color_code': '#42A5F5'},
            {'name': '听力', 'target_value': 30, 'color_code': '#FFA726'},
            {'name': '阅读', 'target_value': 50, 'color_code': '#EC407A'},
            {'name': '写作', 'target_value': 10, 'color_code': '#5C6BC0'},
            {'name': '翻译', 'target_value': 15, 'color_code': '#66BB6A'},
        ]
        
        for module_data in cet4_modules:
            TemplateModule.objects.create(
                template=cet4_template,
                **module_data
            )
        
        self.stdout.write(self.style.SUCCESS('英语四级模板及模块已创建'))

        # 创建考研英语模板
        self.stdout.write('创建考研英语模板...')
        kaoyan_english, created = StudyTemplate.objects.get_or_create(
            name='考研英语',
            defaults={'description': '考研英语学习计划，包含词汇、语法、阅读、写作、翻译五个模块，针对考研英语考试特点设计。'}
        )
        
        # 添加考研英语模块
        kaoyan_modules = [
            {'name': '词汇', 'target_value': 150, 'color_code': '#81C784'},
            {'name': '语法', 'target_value': 25, 'color_code': '#42A5F5'},
            {'name': '阅读', 'target_value': 40, 'color_code': '#FFA726'},
            {'name': '写作', 'target_value': 20, 'color_code': '#EC407A'},
            {'name': '翻译', 'target_value': 25, 'color_code': '#5C6BC0'},
        ]
        
        for module_data in kaoyan_modules:
            TemplateModule.objects.create(
                template=kaoyan_english,
                **module_data
            )
        
        self.stdout.write(self.style.SUCCESS('考研英语模板及模块已创建'))

        # 创建日常英语模板
        self.stdout.write('创建日常英语模板...')
        daily_english, created = StudyTemplate.objects.get_or_create(
            name='日常英语',
            defaults={'description': '日常英语学习计划，包含听力、口语、阅读、写作四个模块，适合提升日常英语交流能力。'}
        )
        
        # 添加日常英语模块
        daily_modules = [
            {'name': '听力', 'target_value': 45, 'color_code': '#FFA726'},
            {'name': '口语', 'target_value': 30, 'color_code': '#EC407A'},
            {'name': '阅读', 'target_value': 40, 'color_code': '#42A5F5'},
            {'name': '写作', 'target_value': 15, 'color_code': '#5C6BC0'},
        ]
        
        for module_data in daily_modules:
            TemplateModule.objects.create(
                template=daily_english,
                **module_data
            )
        
        self.stdout.write(self.style.SUCCESS('日常英语模板及模块已创建'))

        # 创建编程学习模板
        self.stdout.write('创建编程学习模板...')
        programming, created = StudyTemplate.objects.get_or_create(
            name='编程学习',
            defaults={'description': '编程学习计划，包含算法、数据结构、前端开发、后端开发四个模块，适合系统学习编程技能。'}
        )
        
        # 添加编程学习模块
        programming_modules = [
            {'name': '算法', 'target_value': 20, 'color_code': '#81C784'},
            {'name': '数据结构', 'target_value': 15, 'color_code': '#42A5F5'},
            {'name': '前端开发', 'target_value': 60, 'color_code': '#FFA726'},
            {'name': '后端开发', 'target_value': 50, 'color_code': '#EC407A'},
        ]
        
        for module_data in programming_modules:
            TemplateModule.objects.create(
                template=programming,
                **module_data
            )
        
        self.stdout.write(self.style.SUCCESS('编程学习模板及模块已创建'))

        self.stdout.write(self.style.SUCCESS('所有示例数据已生成完成！'))