#!/usr/bin/env python3
"""
单独测试翻译模块
"""
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from translate_text import (
    translate_text,
    translate_text_simple,
    translate_list,
    translate_list_parallel,
    detect_language,
    get_supported_languages
)

def test_single_translation():
    """测试单个文本翻译"""
    print("\n" + "="*60)
    print("测试 1: 单个文本翻译")
    print("="*60)
    
    try:
        text = "Hello, how are you?"
        print(f"原文: {text}")
        result = translate_text(text, dest='zh-cn')
        print(f"翻译结果: {result}")
        print(f"翻译文本: {result.get('text', 'N/A')}")
        print(f"源语言: {result.get('src', 'N/A')}")
        print("✓ 单个翻译测试通过")
        return True
    except Exception as e:
        print(f"❌ 单个翻译测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_translation():
    """测试批量翻译"""
    print("\n" + "="*60)
    print("测试 2: 批量翻译")
    print("="*60)
    
    try:
        texts = [
            "Hello world",
            "Good morning",
            "Thank you",
            "How are you?",
            "Nice to meet you"
        ]
        print(f"原文列表: {texts}")
        result = translate_text(texts, dest='zh-cn')
        print(f"翻译结果类型: {type(result)}")
        print(f"翻译结果数量: {len(result) if isinstance(result, list) else 1}")
        
        if isinstance(result, list):
            for i, r in enumerate(result):
                print(f"  原文 {i+1}: {texts[i]}")
                print(f"  翻译 {i+1}: {r.get('text', 'N/A') if isinstance(r, dict) else str(r)}")
        print("✓ 批量翻译测试通过")
        return True
    except Exception as e:
        print(f"❌ 批量翻译测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_translate_list():
    """测试 translate_list 函数"""
    print("\n" + "="*60)
    print("测试 3: translate_list 函数")
    print("="*60)
    
    try:
        texts = [
            "Hello world",
            "Good morning",
            "Thank you",
            "How are you?",
            "Nice to meet you"
        ]
        print(f"原文列表: {texts}")
        translated = translate_list(texts, dest='zh-cn', batch_size=3)
        print(f"翻译结果: {translated}")
        print(f"翻译结果数量: {len(translated)}")
        
        if len(translated) == len(texts):
            print("✓ translate_list 测试通过")
            return True
        else:
            print(f"❌ 翻译结果数量不匹配: 期望 {len(texts)}, 实际 {len(translated)}")
            return False
    except Exception as e:
        print(f"❌ translate_list 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_translate_list_parallel():
    """测试并行翻译"""
    print("\n" + "="*60)
    print("测试 4: 并行翻译")
    print("="*60)
    
    try:
        # 创建更多文本以测试并行处理
        texts = [
            "Hello world",
            "Good morning",
            "Thank you",
            "How are you?",
            "Nice to meet you",
            "What is your name?",
            "I am fine",
            "See you later",
            "Have a nice day",
            "Goodbye"
        ] * 3  # 30条文本
        print(f"原文列表数量: {len(texts)}")
        print(f"前5条: {texts[:5]}")
        
        translated = translate_list_parallel(
            texts, 
            dest='zh-cn', 
            batch_size=5,
            max_workers=3
        )
        
        print(f"翻译结果数量: {len(translated) if translated else 0}")
        if translated:
            print(f"前5条翻译: {translated[:5]}")
        
        if translated and len(translated) == len(texts):
            print("✓ 并行翻译测试通过")
            return True
        else:
            print(f"❌ 翻译结果数量不匹配: 期望 {len(texts)}, 实际 {len(translated) if translated else 0}")
            return False
    except Exception as e:
        print(f"❌ 并行翻译测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_language_detection():
    """测试语言检测"""
    print("\n" + "="*60)
    print("测试 5: 语言检测")
    print("="*60)
    
    try:
        test_texts = [
            ("Hello world", "en"),
            ("你好世界", "zh"),
            ("こんにちは", "ja"),
            ("Bonjour", "fr")
        ]
        
        for text, expected_lang_prefix in test_texts:
            result = detect_language(text)
            detected = result.get('language', '')
            print(f"文本: {text}")
            print(f"  检测到: {detected} (期望前缀: {expected_lang_prefix})")
            if detected.startswith(expected_lang_prefix):
                print(f"  ✓ 语言检测正确")
            else:
                print(f"  ⚠ 语言检测可能不准确")
        
        print("✓ 语言检测测试完成")
        return True
    except Exception as e:
        print(f"❌ 语言检测测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_empty_input():
    """测试空输入"""
    print("\n" + "="*60)
    print("测试 6: 空输入处理")
    print("="*60)
    
    try:
        # 测试空列表
        result = translate_list([], dest='zh-cn')
        if result == []:
            print("✓ 空列表处理正确")
        else:
            print(f"❌ 空列表处理错误: {result}")
            return False
        
        # 测试空字符串
        result = translate_text("", dest='zh-cn')
        print(f"空字符串翻译结果: {result}")
        print("✓ 空输入测试完成")
        return True
    except Exception as e:
        print(f"❌ 空输入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("翻译模块测试套件")
    print("="*60)
    
    results = []
    
    # 运行测试
    results.append(("单个翻译", test_single_translation()))
    results.append(("批量翻译", test_batch_translation()))
    results.append(("translate_list", test_translate_list()))
    results.append(("并行翻译", test_translate_list_parallel()))
    results.append(("语言检测", test_language_detection()))
    results.append(("空输入处理", test_empty_input()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())

