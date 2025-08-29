#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语义分析模块
使用deepseek-chat模型对故事进行深度语义分析，识别角色和背景信息
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.llm_client import LLMClient


class SemanticAnalyzer:
    """语义分析器，用于分析故事内容并生成角色映射"""

    def __init__(self):
        self.llm_client = LLMClient()
        self.input_file = config.input_md_file
        self.character_mapping_file = (
            config.project_root / "data" / "input" / "character_mapping.json"
        )

    def read_story_content(self) -> str:
        """读取故事内容"""
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"故事文件不存在: {self.input_file}")
        except Exception as e:
            raise Exception(f"读取故事文件失败: {e}")

    def create_analysis_prompt(self, story_content: str) -> str:
        """创建语义分析的提示词"""
        prompt = (
            """
对故事进行深度语义分析，输出故事背景，识别主要角色和特征：
<故事>
"""
            + story_content
            + """
</故事>

故事背景总结必须包含以下结构化内容：

【故事背景】不超过20字

- 故事发生的具体年代和历史时期
- 描述故事所处的总体氛围或气氛

【角色档案】不超过50字

- 姓名与身份：准确记录故事中出现的角色的全名和社会身份，包括但不限于主角、配角、反派

- 性格特征：系统描述角色的性格特质和行为模式

- 外貌特征：记录身高体型数据、面部特征细节及其他显著身体特征

- 着装风格：完整说明角色的穿着和服饰特点

注意事项：

- 严格确保系统现有功能的正常运行不受影响

- 总结后按
[
  {
    "story_bg": "故事背景描述"
  },
  {
    "original_name": "角色原名",
    "new_name": "角色新描述",
    "lora_id": "0"
  }
]
格式输出json：

- original_name字段需完整体现角色在故事中的称谓
# TODO: 手动修复长行 - - new_name字段需严格遵循"数量+着装风格+性格特征+外貌特征+年龄性别+种族"格式（要简洁），例：例子："1个穿着便携宇航服的中等体型的刚毅神情的年轻男人"，"3个穿着破烂衬衫的肥胖体型的颓废老男人"
- 确保original_name与new_name建立N:1的映射关系
-"story_bg"字段是故事背景
-注意："种族"不要出现"族""角色""类""人员"这种泛词，要具体如"小猪""狼""大灰狼""女人""女孩""男人""男孩""老人""青蛙"等
-只需要输出json
"""
        )
        return prompt

    def analyze_story(self) -> Dict[str, Any]:
        """分析故事内容，返回语义分析结果"""
        try:
            # 读取故事内容
            story_content = self.read_story_content()
            print(f"读取故事内容成功，长度: {len(story_content)} 字符")

            # 创建分析提示词
            prompt = self.create_analysis_prompt(story_content)

            # 构建消息
            messages = [{"role": "user", "content": prompt}]

            # 使用deepseek-chat模型进行分析
            print("开始使用deepseek-chat模型进行语义分析...")
            response = self.llm_client.chat_completion_with_model(
                messages=messages,
                model=config.deepseek_model,
                max_tokens=2000,
                temperature=0.3,
            )

            print(f"模型响应: {response}")

            # 解析JSON响应
            try:
                # 清理响应内容，移除可能的markdown格式
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()

                result = json.loads(cleaned_response)
                return result
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"原始响应: {response}")
                raise Exception(f"模型返回的不是有效的JSON格式: {e}")

        except Exception as e:
            print(f"语义分析失败: {e}")
            raise

    def save_character_mapping(self, analysis_result: Dict[str, Any]) -> None:
        """保存角色映射到JSON文件"""
        try:
            # 确保目录存在
            self.character_mapping_file.parent.mkdir(parents=True, exist_ok=True)

            # 写入JSON文件
            with open(self.character_mapping_file, "w", encoding="utf-8") as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)

            print(f"角色映射已保存到: {self.character_mapping_file}")

        except Exception as e:
            print(f"保存角色映射失败: {e}")
            raise

    def run_analysis(self) -> Dict[str, Any]:
        """运行完整的语义分析流程"""
        try:
            print("开始语义分析...")

            # 执行语义分析
            analysis_result = self.analyze_story()

            # 保存结果
            self.save_character_mapping(analysis_result)

            print("语义分析完成！")
            return analysis_result

        except Exception as e:
            print(f"语义分析流程失败: {e}")
            raise


def main():
    """主函数"""
    try:
        analyzer = SemanticAnalyzer()
        result = analyzer.run_analysis()

        print("\n=== 分析结果 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"程序执行失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
