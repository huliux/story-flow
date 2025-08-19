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
    
    def get_story_theme_from_user(self) -> Optional[str]:
        """从用户获取故事主题"""
        print("\n" + "="*60)
        print("📝 故事生成器")
        print("="*60)
        print("没有找到有效的input.md文件，让我们来创建一个新的故事！")
        print("")
        print("请输入您想要的故事主题，例如：")
        print("  - 科幻冒险：太空探索")
        print("  - 奇幻魔法：魔法学院")
        print("  - 悬疑推理：密室逃脱")
        print("  - 爱情故事：时空恋人")
        print("  - 历史传奇：古代英雄")
        print("")
        print("-"*60)
        
        while True:
            theme = input("请输入故事主题（或输入 'q' 退出）: ").strip()
            
            if theme.lower() == 'q':
                print("用户选择退出")
                return None
            
            if len(theme) < 2:
                print("❌ 主题太短，请输入至少2个字符的主题")
                continue
            
            if len(theme) > 100:
                print("❌ 主题太长，请输入不超过100个字符的主题")
                continue
            
            return theme
    
    def generate_story_content(self, theme: str) -> str:
        """根据主题生成故事内容"""
        print(f"\n🤖 正在根据主题 '{theme}' 生成故事...")
        
        # 构建系统提示词
        system_prompt = """
你是一位专业的故事创作者。请根据用户提供的主题创作一个完整的故事。

要求：
1. 故事应该包含4-6个章节
2. 每个章节应该有明确的标题（使用## 格式）
3. 故事情节要完整，有开头、发展、高潮和结尾
4. 语言要生动有趣，适合制作成视频
5. 每个章节的内容要足够详细，便于后续的图像生成和语音合成
6. 总字数控制在800-1500字之间
7. 使用Markdown格式，包含一个主标题（# 格式）

请确保故事内容积极向上，适合所有年龄段观看。
"""
        
        user_prompt = f"请根据以下主题创作一个完整的故事：{theme}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # 调用大模型生成故事
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
        
        # 获取用户输入的主题
        theme = self.get_story_theme_from_user()
        if not theme:
            return False
        
        try:
            # 生成故事内容
            story_content = self.generate_story_content(theme)
            
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
        
        print("请输入您想要的故事主题，例如：")
        print("  - 科幻冒险：太空探索")
        print("  - 奇幻魔法：魔法学院")
        print("  - 悬疑推理：密室逃脱")
        print("  - 爱情故事：时空恋人")
        print("  - 历史传奇：古代英雄")
        print()
        print("-" * 60)
        
        try:
            theme = input("请输入故事主题（或输入 'q' 退出）: ").strip()
            
            if theme.lower() == 'q':
                print("\n👋 已取消故事生成")
                return False
            
            if not theme:
                print("\n❌ 主题不能为空")
                return False
            
            print(f"\n🤖 正在根据主题 '{theme}' 生成故事...")
            
            # 生成故事内容
            story_content = self.generate_story_content(theme)
            
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