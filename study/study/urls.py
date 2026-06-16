from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from study_dashboard.views import (
    home, study_session, study_session_end, 
    progress_dashboard, daily_progress, submit_daily_progress,
    login_view, register_view, logout_view, profile_view, export_study_data,
    add_todo, toggle_todo, delete_todo,
    template_management, add_template, edit_template, delete_template,  # 模板管理视图
    add_module, edit_module, delete_module,  # 模块管理视图
    update_template_order,  # 模板顺序更新视图
    generate_ai_template, generate_ai_template_step1, generate_ai_template_step2, generate_ai_template_step3,  # AI生成模板视图
    generate_learning_materials, get_module_materials,  # 生成和获取学习资料视图
    cet4_study, cet4_materials,  # CET-4学习视图
    c_language_study, c_language_materials,  # 专升本C语言学习视图
    politics_study, politics_materials,  # 专升本政治学习视图
    study_base,  # 统一学习模板视图
    ai_chat, create_chat, send_message, get_chat_messages, rename_chat, delete_chat,  # AI对话视图
    study_heatmap_api,  # 学习热力图API
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    # 沉浸学习模式路由
    path('study/session/', study_session, name='study_session'),
    path('study/session/end/', study_session_end, name='study_session_end'),
    # 学习进度模式路由
    path('progress/dashboard/', progress_dashboard, name='progress_dashboard'),
    path('progress/daily/', daily_progress, name='daily_progress'),
    path('progress/submit/', submit_daily_progress, name='submit_daily_progress'),
    # 用户系统路由
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    # 数据导出路由
    path('export/study-data/', export_study_data, name='export_study_data'),
    # 任务管理路由
    path('todo/add/', add_todo, name='add_todo'),
    path('todo/toggle/<int:todo_id>/', toggle_todo, name='toggle_todo'),
    path('todo/delete/<int:todo_id>/', delete_todo, name='delete_todo'),
    # 模板管理路由
    path('template/management/', template_management, name='template_management'),
    path('template/add/', add_template, name='add_template'),
    path('template/edit/<int:template_id>/', edit_template, name='edit_template'),
    path('template/delete/<int:template_id>/', delete_template, name='delete_template'),
    # 模块管理路由
    path('module/add/<int:template_id>/', add_module, name='add_module'),
    path('module/edit/<int:module_id>/', edit_module, name='edit_module'),
    path('module/delete/<int:module_id>/', delete_module, name='delete_module'),
    # 模板顺序更新路由
    path('update_template_order/', update_template_order, name='update_template_order'),
    # AI生成模板路由
    path('template/generate_ai/', generate_ai_template, name='generate_ai_template'),
    path('template/generate_ai/step1/', generate_ai_template_step1, name='generate_ai_template_step1'),
    path('template/generate_ai/step2/', generate_ai_template_step2, name='generate_ai_template_step2'),
    path('template/generate_ai/step3/', generate_ai_template_step3, name='generate_ai_template_step3'),
    # 生成学习资料路由
    path('template/generate_materials/', generate_learning_materials, name='generate_learning_materials'),
    # 获取模块学习资料路由
    path('module/<int:module_id>/materials/', get_module_materials, name='get_module_materials'),
    # CET-4学习路由
    re_path(r'^cet4/study/(?P<module_name>[^/]+)?/$', cet4_study, name='cet4_study'),
    # CET-4学习资料路由
    path('cet4/materials/', cet4_materials, name='cet4_materials'),
    path('cet4/materials/<str:module_name>/', cet4_materials, name='cet4_materials_module'),
    # 专升本C语言学习路由
    re_path(r'^c_language/study/(?P<module_name>[^/]+)?/$', c_language_study, name='c_language_study'),
    # 专升本C语言学习资料路由
    path('c_language/materials/', c_language_materials, name='c_language_materials'),
    path('c_language/materials/<str:module_name>/', c_language_materials, name='c_language_materials_module'),
    # 专升本政治学习路由
    re_path(r'^politics/study/(?P<module_name>[^/]+)?/$', politics_study, name='politics_study'),
    # 专升本政治学习资料路由
    path('politics/materials/', politics_materials, name='politics_materials'),
    path('politics/materials/<str:module_name>/', politics_materials, name='politics_materials_module'),
    # 政治学科AI生成内容路由
    path('politics/generate_content/', politics_study, name='politics_generate_content'),
    
    # 统一学习模板路由
    re_path(r'^study/(?P<template_id>\d+)/(?P<module_name>.*)?/$', study_base, name='study_base'),
    path('study/<int:template_id>/', study_base, name='study_base'),
    # AI对话路由
    path('ai/chat/', ai_chat, name='ai_chat'),
    path('ai/chat/create/', create_chat, name='create_chat'),
    path('ai/chat/send/', send_message, name='send_message'),
    path('ai/chat/messages/', get_chat_messages, name='get_chat_messages'),
    path('ai/chat/rename/', rename_chat, name='rename_chat'),
    path('ai/chat/delete/', delete_chat, name='delete_chat'),
    # 学习热力图API
    path('api/study-heatmap/', study_heatmap_api, name='study_heatmap_api'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)