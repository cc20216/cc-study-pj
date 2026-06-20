import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
# override=True 确保读取最新的 .env 文件，覆盖进程中已有的环境变量
load_dotenv(override=True)


class MultiSubjectAIGenerator:
    """多学科AI学习资料生成器（ModelScope API兼容版）"""

    def __init__(self):
        # ModelScope API配置（从环境变量读取）
        self.api_url = os.getenv(
            'MODELSCOPE_API_URL',
            'https://api-inference.modelscope.cn/v1/chat/completions'
        )
        self.api_key = os.getenv('MODELSCOPE_API_KEY', '')
        self.model = os.getenv('MODELSCOPE_MODEL', 'Qwen/Qwen3-VL-8B-Instruct')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 初始化本地存储目录
        self.output_dir = os.path.join(os.getcwd(), "ai_generated_materials")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _call_modelscope_api(self, prompt, max_tokens=4000, temperature=0.2):
        """
        调用ModelScope API（遵循正确格式）
        :param prompt: 生成提示词
        :param max_tokens: 最大生成长度
        :param temperature: 生成随机性
        :return: 生成内容 / None
        """
        # ModelScope API请求体（遵循正确格式）
        payload = {
            "model": self.model,  # 从环境变量读取模型ID
            "messages": [
                {
                    "role": "user",
                    "content": prompt  # 纯文本提示词
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.9,
            "stream": False
        }

        try:
            # 发起HTTP请求
            response = requests.post(
                url=self.api_url,
                headers=self.headers,
                json=payload,
                timeout=180  # 增加超时时间
            )

            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"API请求失败，状态码：{response.status_code}"
                if response.text:
                    error_msg += f"，错误信息：{response.text[:200]}"
                print(error_msg)
                raise Exception(error_msg)

            # 解析响应
            result = response.json()

            # 提取生成内容
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"].strip()
                    print(f"API调用成功，生成内容长度：{len(content)}字符")
                    return content
                else:
                    error_msg = "响应格式异常，缺少message/content字段"
                    print(f"{error_msg}，响应内容：{result}")
                    raise Exception(error_msg)
            else:
                error_msg = "API响应异常，无choices字段"
                print(f"{error_msg}：{result}")
                raise Exception(error_msg)

        except requests.exceptions.Timeout:
            error_msg = "API请求超时（180秒）"
            print(f"错误：{error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "API连接失败，请检查网络"
            print(f"错误：{error_msg}")
            raise Exception(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败：{str(e)}"
            print(f"错误：{error_msg}")
            print(f"原始响应：{response.text[:500] if 'response' in locals() else '无响应'}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"API调用异常：{type(e).__name__}: {str(e)}"
            print(f"错误：{error_msg}")
            raise Exception(error_msg)

    def generate_subject_framework(self, subject_name, exam_type):
        """
        生成指定学科的核心知识框架（通用适配所有学科）
        :param subject_name: 学科名称
        :param exam_type: 考试类型
        :return: 结构化知识框架字典 / None
        """
        # 优化提示词，减少JSON复杂度
        prompt = f"""
        你是一位精通各类考试的学科专家，基于{exam_type}最新官方考纲，为「{subject_name}」生成核心知识框架。

        要求：
        1. 分为3-5个核心板块，每个板块包含3-5个章节
        2. 每个章节标注考试权重（1-5星）
        3. 输出严格的JSON格式，不添加任何额外文本

        输出JSON格式：
        {{
            "subject_name": "{subject_name}",
            "exam_type": "{exam_type}",
            "sections": [
                {{
                    "section_name": "板块名称",
                    "section_desc": "简要描述（100字内）",
                    "chapters": [
                        {{
                            "chapter_name": "章节名称",
                            "exam_weight": 3
                        }}
                    ]
                }}
            ]
        }}

        请直接输出JSON，不要有其他内容。
        """

        # 调用API生成框架
        print(f"正在生成{subject_name}的知识框架...")
        raw_content = self._call_modelscope_api(
            prompt=prompt,
            max_tokens=2000,  # 减少token，框架不需要太长
            temperature=0.1  # 降低随机性，确保结构稳定
        )

        if not raw_content:
            print("知识框架生成失败")
            return None

        # 清理并解析JSON
        print("正在解析知识框架...")
        try:
            # 移除可能的markdown代码块标记
            clean_content = raw_content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:]
            if clean_content.startswith("```"):
                clean_content = clean_content[3:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]
            clean_content = clean_content.strip()

            # 尝试解析JSON
            framework = json.loads(clean_content)

            # 添加时间戳
            framework["update_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            print(f"知识框架生成成功，包含{len(framework.get('sections', []))}个板块")
            return framework

        except json.JSONDecodeError as e:
            print(f"JSON解析失败：{str(e)}")
            print("原始内容前500字符：", raw_content[:500])

            # 降级方案：创建基础框架
            return self._create_fallback_framework(subject_name, exam_type)
        except Exception as e:
            print(f"框架处理异常：{str(e)}")
            return self._create_fallback_framework(subject_name, exam_type)

    def _create_fallback_framework(self, subject_name, exam_type):
        """创建备用知识框架"""
        fallback_framework = {
            "subject_name": subject_name,
            "exam_type": exam_type,
            "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "sections": [
                {
                    "section_name": "基础知识板块",
                    "section_desc": "包含该学科的基础核心概念和原理",
                    "chapters": [
                        {"chapter_name": "基础概念", "exam_weight": 5},
                        {"chapter_name": "核心原理", "exam_weight": 4},
                        {"chapter_name": "常用方法", "exam_weight": 3}
                    ]
                },
                {
                    "section_name": "核心考点板块",
                    "section_desc": "历年考试高频考点和重点内容",
                    "chapters": [
                        {"chapter_name": "高频考点一", "exam_weight": 5},
                        {"chapter_name": "高频考点二", "exam_weight": 4},
                        {"chapter_name": "难点解析", "exam_weight": 3}
                    ]
                }
            ]
        }
        print(f"使用备用知识框架，包含{len(fallback_framework['sections'])}个板块")
        return fallback_framework

    def generate_learning_material(self, subject_name, section_name, chapter_names, content_types=None,
                                   exam_type="专升本"):
        """
        生成指定学科/板块/章节的学习资料
        :param subject_name: 学科名称
        :param section_name: 核心板块名称
        :param chapter_names: 章节名称列表
        :param content_types: 内容类型列表，可选值：knowledge(知识点), questions(考题), exercises(练习题), summary(总结)
        :param exam_type: 考试类型
        :return: 生成的学习资料文本 / None
        """
        # 默认内容类型
        if not content_types:
            content_types = ['knowledge', 'questions', 'exercises', 'summary']
        
        chapters_text = "、".join(chapter_names)
        
        # 根据模块类型定制生成内容
        module_type = section_name.lower()
        
        # 内容类型配置
        content_config = {
            'knowledge': {
                'title': "一、核心知识点",
                'desc': """
                1. 详细讲解章节核心知识点，用清晰的层级结构组织
                2. 重点内容用★标注，重要程度越高，★数量越多
                3. 对于词汇模块，生成单词列表、释义和例句
                4. 对于语法模块，生成语法规则、结构和示例
                5. 对于其他模块，生成相应的核心概念和原理
                """
            },
            'questions': {
                'title': "二、典型考题",
                'desc': """
                1. 生成3-5道典型考题，覆盖章节核心知识点
                2. 题目类型要多样化（选择题、填空题、简答题等）
                3. 每道题后面附详细答案和解析
                4. 标注题目难度和考查知识点
                """
            },
            'exercises': {
                'title': "三、练习题",
                'desc': """
                1. 生成5-10道练习题，用于巩固知识点
                2. 题目难度适中，覆盖章节重点内容
                3. 题型多样化，符合考试要求
                4. 附参考答案（无需详细解析）
                """
            },
            'summary': {
                'title': "四、学习总结",
                'desc': """
                1. 本章知识点总结，用简洁的语言概括核心内容
                2. 学习方法建议，包括记忆技巧、复习策略等
                3. 章节间的联系和学习重点提示
                4. 适合快速复习的要点提炼
                """
            }
        }
        
        # 根据内容类型生成要求
        content_requirements = ""
        for content_type in content_types:
            if content_type in content_config:
                content = content_config[content_type]
                content_requirements += f"{content['title']}\n{content['desc']}\n"
        
        # 生成类型和token配置
        generate_type = "\n".join([content_config[ct]['title'] for ct in content_types if ct in content_config])
        max_tokens = 2000 + 500 * len(content_types)  # 根据内容类型数量动态调整token数
        
        # 构建提示词
        prompt = f"""
        你是一位{exam_type}考试的{subject_name}学科专家，请基于最新考纲生成学习资料。

        学科：{subject_name}
        板块：{section_name}
        章节：{chapters_text}
        考试：{exam_type}
        模块类型：{module_type}
        生成内容：{', '.join(content_types)}

        生成要求：
        1. 严格按照以下结构组织内容：
        {content_requirements}
        
        2. 内容定制要求：
        - 如果是词汇模块，重点生成单词列表、释义、例句
        - 如果是语法模块，重点生成语法规则、结构、示例
        - 如果是听力模块，重点生成听力技巧、题型分析
        - 如果是阅读模块，重点生成阅读策略、解题方法
        - 如果是写作模块，重点生成写作模板、常用句型
        - 如果是翻译模块，重点生成翻译技巧、固定搭配
        - 其他模块根据实际内容调整生成重点
        
        3. 语言要求：
        - 语言简洁明了，易于理解
        - 重点突出，层次分明
        - 结合考试实际，注重实用性
        
        请直接生成学习资料内容，不需要额外解释。
        """

        print(f"正在生成学习资料，内容类型：{', '.join(content_types)}")
        material_content = self._call_modelscope_api(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.1
        )

        if material_content:
            print(f"学习资料生成成功，长度：{len(material_content)}字符")
        else:
            print("学习资料生成失败")

        return material_content

    def save_material_to_file(self, content, subject_name, section_name, generate_type):
        """将生成的学习资料保存到本地文件"""
        if not content:
            print("错误：无内容可保存")
            return None

        # 处理文件名特殊字符
        safe_subject = "".join(c for c in subject_name if c.isalnum() or c in (' ', '-', '_'))
        safe_section = "".join(c for c in section_name if c.isalnum() or c in (' ', '-', '_'))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 构建文件名和路径
        filename = f"{safe_subject}_{safe_section}_{generate_type}_{timestamp}.txt"
        file_path = os.path.join(self.output_dir, filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"学科：{subject_name}\n")
                f.write(f"板块：{section_name}\n")
                f.write(f"类型：{generate_type}\n")
                f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content)
            print(f"学习资料已保存至：{file_path}")
            return file_path
        except Exception as e:
            print(f"文件保存失败：{str(e)}")
            return None

    def save_framework_to_file(self, framework):
        """将知识框架保存到本地JSON文件"""
        if not framework:
            print("错误：无知识框架可保存")
            return None

        subject_name = framework.get("subject_name", "未知学科")
        exam_type = framework.get("exam_type", "未知考试")

        # 处理文件名特殊字符
        safe_subject = "".join(c for c in subject_name if c.isalnum() or c in (' ', '-', '_'))
        safe_exam = "".join(c for c in exam_type if c.isalnum() or c in (' ', '-', '_'))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 构建文件名和路径
        filename = f"{safe_subject}_{safe_exam}_知识框架_{timestamp}.json"
        file_path = os.path.join(self.output_dir, filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(framework, f, ensure_ascii=False, indent=2)
            print(f"知识框架已保存至：{file_path}")
            return file_path
        except Exception as e:
            print(f"知识框架保存失败：{str(e)}")
            return None


def main():
    """主运行函数 - 交互式生成学习资料"""
    print("=" * 50)
    print("多学科AI学习资料生成系统")
    print("ModelScope API接口版")
    print("=" * 50)

    # 初始化生成器
    generator = MultiSubjectAIGenerator()

    try:
        # 1. 输入基础信息
        print("\n请输入学科信息：")
        subject_name = input("学科名称（如：英语、政治、数学）：").strip()
        if not subject_name:
            subject_name = "通用学科"

        exam_type = input("考试类型（如：专升本、四级、考研）：").strip()
        if not exam_type:
            exam_type = "通用考试"

        # 2. 生成学科知识框架
        print(f"\n正在为【{subject_name}】生成{exam_type}知识框架...")
        framework = generator.generate_subject_framework(subject_name, exam_type)

        if not framework:
            print("知识框架生成失败，请检查网络和API密钥")
            return

        # 保存框架
        framework_file = generator.save_framework_to_file(framework)

        # 展示框架
        print("\n" + "=" * 50)
        print("生成的知识框架：")
        print("=" * 50)

        for idx, section in enumerate(framework.get("sections", []), 1):
            print(f"\n{idx}. {section.get('section_name', '未命名板块')}")
            print(f"   {section.get('section_desc', '')}")

            chapters = section.get("chapters", [])
            for chap_idx, chapter in enumerate(chapters, 1):
                chap_name = chapter.get("chapter_name", "未命名章节")
                weight = chapter.get("exam_weight", 1)
                stars = "★" * weight
                print(f"   {idx}.{chap_idx} {chap_name} {stars}")

        # 3. 选择生成的板块和章节
        print("\n" + "=" * 50)
        sections = framework.get("sections", [])
        if not sections:
            print("知识框架中无板块信息，使用默认设置")
            section_idx = 0
            chapter_idxs = "1"
        else:
            print("请选择要生成的板块和章节：")

            # 选择板块
            for i, section in enumerate(sections, 1):
                print(f"  {i}. {section.get('section_name', f'板块{i}')}")

            section_input = input(f"\n选择板块序号 (1-{len(sections)}) [默认1]: ").strip()
            try:
                section_idx = int(section_input) - 1 if section_input else 0
                if section_idx < 0 or section_idx >= len(sections):
                    section_idx = 0
            except:
                section_idx = 0

            # 选择章节
            selected_section = sections[section_idx]
            chapters = selected_section.get("chapters", [])

            if chapters:
                print(f"\n【{selected_section.get('section_name', '所选板块')}】中的章节：")
                for i, chapter in enumerate(chapters, 1):
                    chap_name = chapter.get("chapter_name", f"章节{i}")
                    print(f"  {i}. {chap_name}")

                chapter_input = input(f"\n选择章节序号 (多选用逗号分隔，如1,3) [默认1]: ").strip()
                if not chapter_input:
                    chapter_idxs = ["1"]
                else:
                    chapter_idxs = chapter_input.split(",")
            else:
                print("该板块无章节信息")
                chapter_idxs = ["1"]

        # 确定章节名称
        selected_chapter_names = []
        for idx_str in chapter_idxs:
            try:
                chap_idx = int(idx_str.strip()) - 1
                if 0 <= chap_idx < len(chapters):
                    selected_chapter_names.append(chapters[chap_idx].get("chapter_name", f"章节{chap_idx + 1}"))
            except:
                continue

        if not selected_chapter_names:
            selected_chapter_names = ["核心知识点"]

        # 4. 选择生成类型
        print("\n" + "=" * 50)
        print("选择生成类型：")
        print("  1. 简略版 (快速生成，适合复习)")
        print("  2. 详细版 (详细内容，包含例题)")

        type_input = input("\n选择类型序号 (1或2) [默认1]: ").strip()
        generate_type = "详细版" if type_input == "2" else "简略版"

        # 5. 生成学习资料
        selected_section_name = selected_section.get("section_name", "核心板块")
        print(f"\n正在生成【{subject_name} - {selected_section_name}】的{generate_type}学习资料...")

        material_content = generator.generate_learning_material(
            subject_name=subject_name,
            section_name=selected_section_name,
            chapter_names=selected_chapter_names,
            generate_type=generate_type,
            exam_type=exam_type
        )

        if not material_content:
            print("学习资料生成失败")
            return

        # 6. 展示并保存生成结果
        print("\n" + "=" * 50)
        print(f"{generate_type}学习资料生成完成")
        print("=" * 50)
        print(material_content)
        print("=" * 50)

        # 保存到文件
        generator.save_material_to_file(
            content=material_content,
            subject_name=subject_name,
            section_name=selected_section_name,
            generate_type=generate_type
        )

        print("\n操作完成！所有文件已保存至 ai_generated_materials 文件夹")

    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n程序运行异常：{str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()