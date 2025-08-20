#!/usr/bin/env python3
"""
故事生成器模块
根据用户输入的主题，使用大模型生成完整的故事内容
"""

import os
from pathlib import Path
from typing import Optional
from src.config import config
from src.llm_client import llm_client

class StoryGenerator:
    """故事生成器类"""
    
    def __init__(self):
        self.input_file = config.input_dir / "input.md"
    
    def check_input_file_exists(self) -> bool:
        """检查input.md文件是否存在且包含有效内容"""
        if not self.input_file.exists():
            return False
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # 检查文件是否有实际内容（不只是空白字符）
                return len(content) > 0 and not content.isspace()
        except Exception as e:
            print(f"读取input.md文件时出错: {e}")
            return False
    
    def get_story_info_from_user(self) -> Optional[tuple[str, str]]:
        """从用户获取故事类型和主题
        
        Returns:
            tuple[str, str] | None: (故事类型, 故事主题) 或 None（用户退出）
        """
        print("\n" + "="*60)
        print("📝 故事生成器")
        print("="*60)
        print("没有找到有效的input.md文件，让我们来创建一个新的故事！")
        print("")
        print("请按照提示输入故事信息：")
        print("")
        
        # 获取故事类型
        print("📚 第一步：选择故事类型")
        print("可选类型：童话、科幻、悬疑、爱情、历史、奇幻、冒险、励志等")
        print("-"*60)
        
        while True:
            story_type = input("请输入故事类型（或输入 'q' 退出）: ").strip()
            
            if story_type.lower() == 'q':
                print("用户选择退出")
                return None
            
            if len(story_type) < 2:
                print("❌ 故事类型太短，请输入至少2个字符")
                continue
            
            if len(story_type) > 20:
                print("❌ 故事类型太长，请输入不超过20个字符")
                continue
            
            break
        
        # 获取故事主题
        print("\n🎯 第二步：输入故事主题/关键字")
        print("主题示例：")
        print("  - 太空探索、外星文明、时间旅行")
        print("  - 魔法学院、龙与骑士、失落王国")
        print("  - 密室逃脱、连环杀手、失踪案件")
        print("  - 时空恋人、青梅竹马、异地恋")
        print("  - 古代英雄、战国风云、丝绸之路")
        print("-"*60)
        
        while True:
            theme = input("请输入故事主题/关键字（或输入 'q' 退出）: ").strip()
            
            if theme.lower() == 'q':
                print("用户选择退出")
                return None
            
            if len(theme) < 2:
                print("❌ 主题太短，请输入至少2个字符的主题")
                continue
            
            if len(theme) > 100:
                print("❌ 主题太长，请输入不超过100个字符的主题")
                continue
            
            break
        
        print(f"\n✅ 故事信息确认：")
        print(f"   故事类型：{story_type}")
        print(f"   故事主题：{theme}")
        
        return (story_type, theme)
    
    def generate_story_content(self, story_type: str, theme: str) -> str:
        """根据故事类型和主题生成故事内容
        
        Args:
            story_type: 故事类型（如童话、科幻、悬疑等）
            theme: 故事主题/关键字
        """
        print(f"\n🤖 正在生成 '{story_type}' 类型的故事，主题：'{theme}'...")
        
        # 构建系统提示词，替换占位符
        system_prompt = f"""
你的任务是根据用户输入的关键字或主题，生成一个{story_type}短视频故事。请仔细阅读以下信息，并按照指定的逻辑和结构来创作故事。
故事类型:
<故事类型>
{story_type}
</故事类型>
关键字或主题:
<关键字或主题>
{theme}
</关键字或主题>
讲故事的逻辑和结构如下：
1. **悬念开场**：以"场景/背景+反常识疑问/断言"开篇，激发观众兴趣。
2. **身份代入**：用第二人称"你"描述主角身份、时代背景及面临的危机，不要出现"想象一下"等过渡词，直接进入主题。
3. **冲突升级**：外部压力或遇到什么挫折。
4. **破局细节**：主角采取哪些递进行动，扭转局面，解决问题。
5. **主题收尾**：通过主角结局引出金句。
请在<故事>标签内写下生成的短视频故事。确保故事结构完整，逻辑连贯，语言生动，能够吸引观众的注意力。
<故事>
[在此生成短视频故事]
</故事>
注意：只需要生成并返回故事本身，不要说其它与故事无关的话，不要返回任何XML标签！
要求：
1. 语言要生动有趣，适合制作成视频
2. 每个章节的内容要足够详细，便于后续的图像生成和语音合成

请确保故事内容积极向上，适合所有年龄段观看。
"""
        
        user_prompt = f"请根据故事类型'{story_type}'和主题'{theme}'创作一个完整的故事。"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # 调用大模型生成故事，使用专门的故事生成模型
            if config.llm_provider == 'deepseek':
                # 使用DeepSeek的故事生成专用模型
                story_content = llm_client.chat_completion_with_model(
                    messages=messages,
                    model=config.deepseek_story_model,
                    max_tokens=2000,  # 增加token数以生成更完整的故事
                    temperature=0.8   # 提高创造性
                )
            else:
                # 使用默认模型
                story_content = llm_client.chat_completion(
                    messages=messages,
                    max_tokens=2000,  # 增加token数以生成更完整的故事
                    temperature=0.8   # 提高创造性
                )
            
            return story_content
            
        except Exception as e:
            print(f"❌ 生成故事时出错: {e}")
            raise
    
    def save_story_to_file(self, content: str) -> bool:
        """将生成的故事保存到input.md文件"""
        try:
            # 确保输入目录存在
            config.input_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存故事内容
            with open(self.input_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 故事已保存到: {self.input_file}")
            return True
            
        except Exception as e:
            print(f"❌ 保存故事文件时出错: {e}")
            return False
    
    def generate_and_save_story(self, force_overwrite: bool = False) -> bool:
        """完整的故事生成和保存流程
        
        Args:
            force_overwrite: 是否强制覆盖现有文件
        """
        # 如果文件已存在且不是强制覆盖模式，询问用户
        if not force_overwrite and self.check_input_file_exists():
            print(f"\n⚠️  检测到已存在input.md文件: {self.input_file}")
            while True:
                choice = input("是否要覆盖现有故事？(y/n): ").strip().lower()
                if choice in ['y', 'yes', '是']:
                    break
                elif choice in ['n', 'no', '否']:
                    print("取消故事生成")
                    return False
                else:
                    print("请输入 y 或 n")
        
        # 获取用户输入的故事信息
        story_info = self.get_story_info_from_user()
        if not story_info:
            return False
        
        story_type, theme = story_info
        
        try:
            # 生成故事内容
            story_content = self.generate_story_content(story_type, theme)
            
            # 保存到文件
            success = self.save_story_to_file(story_content)
            
            if success:
                print("\n🎉 故事生成完成！")
                print(f"您可以在 {self.input_file} 中查看生成的故事")
                print("现在可以继续执行后续的处理流程")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ 故事生成过程中出现错误: {e}")
            return False
    
    def generate_new_story_force(self) -> bool:
        """强制生成新故事，覆盖现有文件"""
        print("\n============================================================")
        print("📝 故事生成器")
        print("============================================================")
        print("正在生成新故事，将覆盖现有的input.md文件！\n")
        
        print("请按照提示输入故事信息：")
        print("")
        
        # 获取故事类型
        print("📚 第一步：选择故事类型")
        print("可选类型：童话、科幻、悬疑、爱情、历史、奇幻、冒险、励志等")
        print("-" * 60)
        
        try:
            story_type = input("请输入故事类型（或输入 'q' 退出）: ").strip()
            
            if story_type.lower() == 'q':
                print("\n👋 已取消故事生成")
                return False
            
            if not story_type or len(story_type) < 2:
                print("\n❌ 故事类型不能为空且至少2个字符")
                return False
            
            # 获取故事主题
            print("\n🎯 第二步：输入故事主题/关键字")
            print("主题示例：")
            print("  - 太空探索、外星文明、时间旅行")
            print("  - 魔法学院、龙与骑士、失落王国")
            print("  - 密室逃脱、连环杀手、失踪案件")
            print("  - 时空恋人、青梅竹马、异地恋")
            print("  - 古代英雄、战国风云、丝绸之路")
            print("-" * 60)
            
            theme = input("请输入故事主题/关键字（或输入 'q' 退出）: ").strip()
            
            if theme.lower() == 'q':
                print("\n👋 已取消故事生成")
                return False
            
            if not theme or len(theme) < 2:
                print("\n❌ 故事主题不能为空且至少2个字符")
                return False
            
            print(f"\n✅ 故事信息确认：")
            print(f"   故事类型：{story_type}")
            print(f"   故事主题：{theme}")
            
            # 生成故事内容
            story_content = self.generate_story_content(story_type, theme)
            
            if not story_content:
                print("\n❌ 故事生成失败")
                return False
            
            # 保存故事到文件（强制覆盖）
            if self.save_story_to_file(story_content):
                print(f"\n✅ 故事已保存到: {self.input_file}")
                print("\n🎉 故事生成完成！")
                print(f"您可以在 {self.input_file} 中查看生成的故事")
                print("现在可以继续执行后续的处理流程")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ 故事生成过程中出现错误: {e}")
            return False

# 创建全局实例
story_generator = StoryGenerator()

if __name__ == "__main__":
    # 测试故事生成功能
    if not story_generator.check_input_file_exists():
        print("测试故事生成功能...")
        success = story_generator.generate_and_save_story()
        if success:
            print("测试成功！")
        else:
            print("测试失败！")
    else:
        print("input.md文件已存在且包含内容")