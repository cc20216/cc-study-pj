#!/usr/bin/env python3
"""
初始化示例模板数据脚本
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django环境
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study.settings')
django.setup()

from study_dashboard.models import StudyTemplate, TemplateModule

def init_example_templates():
    """初始化示例模板数据"""
    print("开始初始化示例模板数据...")
    
    # 1. 创建英语四级示例模板
    cet4_template, created = StudyTemplate.objects.get_or_create(
        name="英语四级",
        description="大学英语四级考试学习模板，包含词汇、听力、阅读、写作等模块",
        is_example=True,
        order=1
    )
    
    if created:
        print(f"创建英语四级模板成功")
        
        # 添加英语四级模块
        cet4_modules = [
            {"name": "词汇", "target_value": 4500, "color_code": "#4CAF50"},
            {"name": "听力", "target_value": 20, "color_code": "#2196F3"},
            {"name": "阅读", "target_value": 30, "color_code": "#FF9800"},
            {"name": "写作", "target_value": 10, "color_code": "#9C27B0"},
            {"name": "翻译", "target_value": 10, "color_code": "#FF5722"}
        ]
        
        for module_data in cet4_modules:
            TemplateModule.objects.create(
                template=cet4_template,
                name=module_data["name"],
                target_value=module_data["target_value"],
                target_type="numeric",
                color_code=module_data["color_code"]
            )
        print(f"添加英语四级模块成功")
    else:
        print(f"英语四级模板已存在")
    
    # 2. 创建大学高等数学示例模板
    math_template, created = StudyTemplate.objects.get_or_create(
        name="大学高等数学",
        description="大学高等数学学习模板，包含微积分、线性代数、概率论等模块",
        is_example=True,
        order=2
    )
    
    if created:
        print(f"创建大学高等数学模板成功")
        
        # 添加大学高等数学模块
        math_modules = [
            {"name": "极限与连续", "target_value": 20, "color_code": "#4CAF50"},
            {"name": "导数与微分", "target_value": 30, "color_code": "#2196F3"},
            {"name": "积分学", "target_value": 30, "color_code": "#FF9800"},
            {"name": "常微分方程", "target_value": 15, "color_code": "#9C27B0"},
            {"name": "级数", "target_value": 15, "color_code": "#FF5722"}
        ]
        
        for module_data in math_modules:
            TemplateModule.objects.create(
                template=math_template,
                name=module_data["name"],
                target_value=module_data["target_value"],
                target_type="numeric",
                color_code=module_data["color_code"]
            )
        print(f"添加大学高等数学模块成功")
    else:
        print(f"大学高等数学模板已存在")
    
    print("示例模板数据初始化完成！")

if __name__ == "__main__":
    init_example_templates()
