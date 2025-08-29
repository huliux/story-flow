#!/usr/bin/env python3
"""
爆款视频大纲和生图提示词生成器
根据用户输入的视频主题和风格，自动生成视频大纲和Flux1提示词
"""

import json
from datetime import datetime
from typing import Dict, Optional, Tuple

from src.config import config
from src.llm_client import llm_client


class ViralVideoGenerator:
    """爆款视频生成器类"""

    def __init__(self):
        self.input_dir = config.input_dir
        self.processed_dir = config.output_dir_txt

        # 确保目录存在
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def get_user_input(self) -> Optional[Tuple[str, str, int]]:
        """
        获取用户输入的视频主题、风格提示和场景数量

        Returns:
            tuple[str, str, int] | None: (视频主题, 风格提示, 场景数量) 或 None（用户退出）
        """
        print("\n" + "=" * 60)
        print("🎬 爆款视频大纲和生图提示词生成器")
        print("=" * 60)
        print("让我们来创建一个爆款视频！")
        print("")

        # 获取视频主题
        print("🎯 第一步：输入视频主题")
        print("主题示例：")
        print("  - 职场励志故事")
        print("  - 美食制作教程")
        print("  - 旅行攻略分享")
        print("  - 科技产品评测")
        print("  - 情感故事分享")
        print("-" * 60)

        while True:
            video_theme = input("请输入视频主题（或输入 'q' 退出）: ").strip()

            if video_theme.lower() == "q":
                print("用户选择退出")
                return None

            if len(video_theme) < 2:
                print("❌ 视频主题太短，请输入至少2个字符")
                continue

            if len(video_theme) > 100:
                print("❌ 视频主题太长，请输入不超过100个字符")
                continue

            break

        # 获取风格提示
        print("\n🎨 第二步：输入风格提示（可选）")
        print("风格示例：")
        print("  - 温馨治愈风格")
        print("  - 搞笑幽默风格")
        print("  - 专业严肃风格")
        print("  - 时尚潮流风格")
        print("  - 复古怀旧风格")
        print("-" * 60)

        style_reference = input("请输入风格提示（可留空，直接回车跳过）: ").strip()
        if not style_reference:
            style_reference = "现代简约风格"

        # 获取场景数量
        print("\n📊 第三步：设置场景数量")
        print("建议场景数量：3-8个场景")
        print("-" * 60)

        while True:
            try:
                scene_count_input = input(
                    "请输入场景数量（默认5个，直接回车使用默认值）: "
                ).strip()

                if not scene_count_input:
                    scene_count = 5
                    break

                scene_count = int(scene_count_input)

                if scene_count < 1:
                    print("❌ 场景数量不能少于1个")
                    continue

                if scene_count > 20:
                    print("❌ 场景数量不能超过20个")
                    continue

                break

            except ValueError:
                print("❌ 请输入有效的数字")
                continue

        print("\n✅ 输入信息确认：")
        print(f"   视频主题：{video_theme}")
        print(f"   风格提示：{style_reference}")
        print(f"   场景数量：{scene_count}")

        return video_theme, style_reference, scene_count

    def generate_video_outline(
        self, video_theme: str, style_reference: str, scene_count: int
    ) -> Optional[Dict]:
        """
        生成视频大纲

        Args:
            video_theme: 视频主题
            style_reference: 风格提示
            scene_count: 场景数量

        Returns:
            Dict: 视频大纲JSON数据
        """
        print("\n🤖 正在生成视频大纲...")

        # 构建系统提示词
        system_prompt = """
# 爆款视频主题选择与场景生成器
## 任务：

你是一位经验丰富的爆款视频策划师。当用户提供视频主题时，你需要：

1. 将用户提供的视频主题{video_theme}，作为本次生成内容的基础。
2. 针对这个给定的主题，参考用户提供的爆款视频画面提示词示例{style_reference}，构思并生成包含中英文场景描述的视频场景。
3. 最终结果必须以包含主题中文、英文、场景数量及场景中英文描述的JSON格式输出。

## 用户输入说明：
从用户那里获取以下三类信息：
1. 爆款视频画面提示词的示例：
用户可以提供一些他们认为能够构成爆款视频的典型画面或场景的描述性提示词。这些示例将帮助AI理解用户期望的画面风格和内容方向。
2. 场景数量{scene_count}
3. 用户提供视频主题{video_theme}

## 输出规则：
### 1. 主题理解
准确理解用户提供的视频主题。

### 2. 场景构思与描述
对于选定的主题和确定的场景数量，你需要为每个场景构思具体内容：
a. 参考用户示例: 在构思场景时，应积极参考用户提供的“爆款视频画面提示词的示例”，理解用户期望的视觉风格、节奏感、情感基调或内容倾向，并将这些元素融入到为选定主题设计的场景中。
b. 主题相关性: 每个场景都必须紧密围绕选定的视频主题展开，共同构成一个有逻辑、有吸引力的叙事或展示序列。确保场景之间有自然的过渡和联系。
c. 中英文描述: 为每个构思出的场景提供简洁、生动、且具有画面感的中文描述和对应的准确英文翻译。描述应能清晰传达场景的核心内容和视觉效果。

### 3. 主题翻译
为选定的视频主题提供准确的中文名称。如果用户提供的主题本身是对象且包含明确的标题，则直接使用该标题。
为选定的视频主题提供对应的、自然的英文翻译。

## 输出格式要求,：
{{
"video_description_zh": "视频主题的中文描述",
"video_description_en": "视频主题的英文描述",
"suitable_scene_count": {scene_count},
"scenes": [
    {{
        "scene_id": 1,
        "chinese_description": "场景的中文描述",
        "english_description": "场景的英文描述"
    }}
]
}}
"""

        user_prompt = """
请根据以下信息生成爆款视频大纲：

视频主题：{video_theme}
风格提示：{style_reference}
场景数量：{scene_count}

请严格按照JSON格式输出，确保包含所有必需字段。
"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = llm_client.chat_completion(
                messages=messages, max_tokens=2000, temperature=0.7
            )

            # 尝试解析JSON响应
            try:
                # 提取JSON部分（去除可能的markdown格式）
                json_start = response.find("{")
                json_end = response.rfind("}") + 1

                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end]

                    # 尝试修复常见的JSON格式问题
                    json_str = self._fix_json_format(json_str)

                    outline_data = json.loads(json_str)

                    # 验证必需字段
                    required_fields = [
                        "video_description_zh",
                        "video_description_en",
                        "suitable_scene_count",
                    ]
                    for field in required_fields:
                        if field not in outline_data:
                            raise ValueError(f"缺少必需字段: {field}")

                    # 如果没有scenes字段，生成默认场景
                    if "scenes" not in outline_data:
                        outline_data["scenes"] = []
                        for i in range(scene_count):
                            outline_data["scenes"].append(
                                {
                                    "scene_id": i + 1,
                                    "chinese_description": f"场景{i+1}：{video_theme}相关内容",
                                    "english_description": f"Scene {i+1}: Content related to {video_theme}",
                                }
                            )

                    print("✅ 视频大纲生成成功！")
                    return outline_data
                else:
                    raise ValueError("响应中未找到有效的JSON格式")

            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"原始响应前500字符: {response[:500]}...")

                # 尝试生成备用的简化大纲
                print("🔄 尝试生成备用大纲...")
                return self._generate_fallback_outline(video_theme, scene_count)

            except Exception as e:
                print(f"❌ 处理响应时出错: {e}")
                return self._generate_fallback_outline(video_theme, scene_count)

        except Exception as e:
            print(f"❌ 生成视频大纲时出错: {e}")
            return None

    def _fix_json_format(self, json_str: str) -> str:
        """
        修复常见的JSON格式问题
        """
        # 移除可能的markdown代码块标记
        json_str = json_str.replace("```json", "").replace("```", "")

        # 移除多余的空白字符
        json_str = json_str.strip()

        # 尝试修复截断的JSON（如果以逗号结尾但没有闭合）
        if json_str.endswith(","):
            json_str = json_str.rstrip(",")

        # 确保JSON以}结尾
        if not json_str.endswith("}"):
            # 计算需要添加的闭合括号数量
            open_braces = json_str.count("{")
            close_braces = json_str.count("}")
            missing_braces = open_braces - close_braces

            if missing_braces > 0:
                json_str += "}" * missing_braces

        return json_str

    def _generate_fallback_outline(self, video_theme: str, scene_count: int) -> Dict:
        """
        生成备用的简化视频大纲
        """
        print("📝 生成简化版视频大纲...")

        # 简单的英文翻译（基础版本）
        theme_en = (
            video_theme.replace("男女", "couple")
            .replace("相爱", "love")
            .replace("结婚", "marriage")
            .replace("相伴", "companionship")
            .replace("时间流逝", "passage of time")
            .replace("伤感", "melancholy")
        )

        outline_data = {
            "video_description_zh": video_theme,
            "video_description_en": theme_en,
            "suitable_scene_count": scene_count,
            "scenes": [],
        }

        # 生成基础场景
        scene_templates = [
            ("初遇相识", "First meeting"),
            ("甜蜜恋爱", "Sweet romance"),
            ("浪漫求婚", "Romantic proposal"),
            ("幸福婚礼", "Happy wedding"),
            ("相伴岁月", "Years together"),
            ("温馨日常", "Warm daily life"),
            ("共同成长", "Growing together"),
            ("时光流逝", "Time passing"),
        ]

        for i in range(scene_count):
            if i < len(scene_templates):
                zh_desc, en_desc = scene_templates[i]
            else:
                zh_desc = f"场景{i+1}：{video_theme}相关内容"
                en_desc = f"Scene {i+1}: Content related to {theme_en}"

            outline_data["scenes"].append(
                {
                    "scene_id": i + 1,
                    "chinese_description": zh_desc,
                    "english_description": en_desc,
                }
            )

        return outline_data

    def generate_flux_prompts(
        self, outline_data: Dict, trigger_word: str = "", special_requirements: str = ""
    ) -> Optional[Dict]:
        """
        生成Flux1格式的生图提示词

        Args:
            outline_data: 视频大纲数据
            trigger_word: 触发词（可选）
            special_requirements: 特殊要求（可选）

        Returns:
            Dict: Flux1提示词JSON数据
        """
        print("\n🎨 正在生成生图提示词...")

        video_description_en = outline_data.get("video_description_en", "")
        suitable_scene_count = outline_data.get("suitable_scene_count", 5)
        scenes = outline_data.get("scenes", [])

        # 构建系统提示词
        system_prompt = """
# 角色：爆款短视频复刻与创意大师

你是一位专注于TikTok、Shorts等短视频平台的爆款内容复刻与创新专家。
你的任务是：精准分析用户提供的【新视频主题】，设计一系列具备爆款潜质的图片提示词。这些提示词应明确体现短视频成功元素及视频主题中创意应用，确保每个分镜具备强烈的病毒传播潜力。

## 输入信息：

1. 新视频主题：
   {video_description_en}

2. 分镜数量：
   {suitable_scene_count}

3. 触发词：
   {trigger_word}
   （若触发词存在，每个场景提示词句首放置；若为空则无需放置）

4. 额外要求：
   {special_requirements}
   （若额外要求存在，则需要遵循额外要求的规则；若为空则无需遵守）

## 核心目标：
每一条生成的图片提示词需精准体现新主题，并且巧妙融入参考视频中分析得出的“病毒传播基因”，同时创新性地借鉴参考图片提示词中的优秀元素，以达到甚至超越原作的传播效果。

## 输出要求：
1. 严格按以下JSON格式输出：
{{
"storyboards": [
    {{
        "scene_id": "场景ID",
        "narration": "不超过20字的英文台词",
        "chinese_prompt": "中文提示词",
        "english_prompt": "英文提示词"
    }}
]
}}
每个提示词需精心设计，明确体现爆款特质，无需创作说明，融合图片参考的优秀元素，激发观看者兴趣。
每个场景的narration字段需要生成简洁有力的英文台词，字数不超过20字，能够概括该场景的核心内容或情感。
2. 每条提示词需精心雕琢，准确捕捉爆款视频的核心要素，确保具备强烈的视觉冲击力和病毒式传播潜力。
3. 提示词应简洁直接，无需包含任何创作指导或说明性文字。
4. 请控制每条提示词的字数在 100-250 字范围内，确保完全符合 Flux 图像生成模型的输入要求和最佳实践。
"""

        # 构建场景信息
        scene_info = "\n".join(
            [
                f"场景{scene['scene_id']}: {scene.get('chinese_description', '')} / {scene.get('english_description', '')}"
                for scene in scenes
            ]
        )

        user_prompt = """
请根据以下视频大纲生成Flux1格式的生图提示词：

视频主题（英文）：{video_description_en}
场景数量：{suitable_scene_count}
触发词：{trigger_word if trigger_word else '无'}
特殊要求：{special_requirements if special_requirements else '无'}

场景信息：
{scene_info}

请为每个场景生成详细的中英文提示词和英文台词，确保提示词具有视觉冲击力和爆款潜质。
每个场景必须包含narration字段，生成不超过20字的英文台词。
严格按照JSON格式输出。
"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = llm_client.chat_completion(
                messages=messages, max_tokens=3000, temperature=0.8
            )

            # 尝试解析JSON响应
            try:
                # 提取JSON部分
                json_start = response.find("{")
                json_end = response.rfind("}") + 1

                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end]
                    prompts_data = json.loads(json_str)

                    # 验证必需字段
                    if "storyboards" not in prompts_data:
                        raise ValueError("缺少必需字段: storyboards")

                    print("✅ 生图提示词生成成功！")
                    return prompts_data
                else:
                    raise ValueError("响应中未找到有效的JSON格式")

            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"原始响应: {response}")
                return None

        except Exception as e:
            print(f"❌ 生成生图提示词时出错: {e}")
            return None

    def save_outline_to_input(self, outline_data: Dict, video_theme: str) -> bool:
        """
        保存视频大纲到input文件夹

        Args:
            outline_data: 视频大纲数据
            video_theme: 视频主题（用于文件命名）

        Returns:
            bool: 保存是否成功
        """
        try:
            # 生成文件名（使用时间戳避免冲突）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_theme = "".join(
                c for c in video_theme if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            safe_theme = safe_theme.replace(" ", "_")[:20]  # 限制长度

            filename = f"video_outline_{safe_theme}_{timestamp}.json"
            file_path = self.input_dir / filename

            # 添加元数据
            output_data = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "video_theme": video_theme,
                    "file_type": "video_outline",
                },
                **outline_data,
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            print(f"✅ 视频大纲已保存到: {file_path}")
            return True

        except Exception as e:
            print(f"❌ 保存视频大纲时出错: {e}")
            return False

    def save_prompts_to_processed(self, prompts_data: Dict, video_theme: str) -> bool:
        """
        保存生图提示词到processed文件夹，命名为Flux1_prompt.json

        Args:
            prompts_data: 生图提示词数据
            video_theme: 视频主题

        Returns:
            bool: 保存是否成功
        """
        try:
            # 使用固定文件名
            file_path = self.processed_dir / "Flux1_prompt.json"

            # 添加元数据
            output_data = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "video_theme": video_theme,
                    "file_type": "flux1_prompts",
                },
                **prompts_data,
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            print(f"✅ 生图提示词已保存到: {file_path}")
            return True

        except Exception as e:
            print(f"❌ 保存生图提示词时出错: {e}")
            return False

    def generate_complete_workflow(self) -> bool:
        """
        执行完整的爆款视频生成工作流

        Returns:
            bool: 是否成功完成整个流程
        """
        try:
            # 第一步：获取用户输入
            user_input = self.get_user_input()
            if user_input is None:
                return False

            video_theme, style_reference, scene_count = user_input

            # 第二步：生成视频大纲
            outline_data = self.generate_video_outline(
                video_theme, style_reference, scene_count
            )
            if outline_data is None:
                print("❌ 视频大纲生成失败")
                return False

            # 第三步：保存视频大纲到input文件夹
            if not self.save_outline_to_input(outline_data, video_theme):
                print("❌ 视频大纲保存失败")
                return False

            # 第四步：生成生图提示词
            prompts_data = self.generate_flux_prompts(outline_data)
            if prompts_data is None:
                print("❌ 生图提示词生成失败")
                return False

            # 第五步：保存生图提示词到processed文件夹
            if not self.save_prompts_to_processed(prompts_data, video_theme):
                print("❌ 生图提示词保存失败")
                return False

            print("\n🎉 爆款视频大纲和生图提示词生成完成！")
            print("\n📁 生成的文件：")
            print(f"   - 视频大纲：{self.input_dir} (以video_outline_开头的JSON文件)")
            print(f"   - 生图提示词：{self.processed_dir}/Flux1_prompt.json")

            return True

        except Exception as e:
            print(f"❌ 执行工作流时出错: {e}")
            return False


# 创建全局实例
viral_video_generator = ViralVideoGenerator()


if __name__ == "__main__":
    # 直接运行时执行完整工作流
    viral_video_generator.generate_complete_workflow()
