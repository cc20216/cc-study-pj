from django.core.management.base import BaseCommand
from study_dashboard.models import StudyTemplate, TemplateModule

class Command(BaseCommand):
    help = 'Create CET-4 study template with modules'

    def handle(self, *args, **options):
        # 创建英语四级学习模板
        template, created = StudyTemplate.objects.get_or_create(
            name='英语四级',
            defaults={
                'description': '英语四级考试学习计划，包含词汇、语法、听力、阅读、写作和翻译六个模块'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created template: {template.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Template already exists: {template.name}'))
        
        # 定义英语四级的模块
        modules_data = [
            {'name': '词汇', 'target_value': 5000, 'color_code': '#81C784'},
            {'name': '语法', 'target_value': 50, 'color_code': '#64B5F6'},
            {'name': '听力', 'target_value': 120, 'color_code': '#FFB74D'},
            {'name': '阅读', 'target_value': 100, 'color_code': '#9575CD'},
            {'name': '写作', 'target_value': 20, 'color_code': '#E57373'},
            {'name': '翻译', 'target_value': 30, 'color_code': '#4FC3F7'}
        ]
        
        # 创建或更新模块
        for module_data in modules_data:
            module, created = TemplateModule.objects.get_or_create(
                template=template,
                name=module_data['name'],
                defaults={
                    'target_value': module_data['target_value'],
                    'color_code': module_data['color_code']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  - Successfully created module: {module.name}'))
            else:
                # 更新现有模块
                module.target_value = module_data['target_value']
                module.color_code = module_data['color_code']
                module.save()
                self.stdout.write(self.style.WARNING(f'  - Updated module: {module.name}'))
        
        self.stdout.write(self.style.SUCCESS('\nCET-4 template with modules created successfully!'))