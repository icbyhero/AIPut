"""
macOS 平台适配器测试脚本。

运行此脚本来验证 macOS 适配器的所有功能。
"""

import asyncio
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from platform_detection.detector import PlatformDetector
from platform_adapters.macos.adapter import MacOSAdapter


async def test_macos_adapter():
    """测试所有 macOS 适配器功能。"""

    print("=" * 60)
    print("macOS 平台适配器测试")
    print("=" * 60)

    # 1. 检测平台
    print("\n=== 1. 平台检测 ===")
    platform_info = PlatformDetector.detect()
    print(f"操作系统: {platform_info.os_name} {platform_info.os_version}")
    print(f"桌面环境: {platform_info.desktop_environment}")
    print(f"显示协议: {platform_info.display_protocol}")

    if platform_info.os_name != 'Darwin':
        print("\n警告：此测试仅在 macOS 上运行。")
        print(f"当前系统: {platform_info.os_name}")
        return

    print("\n检测到的功能:")
    additional_info = platform_info.additional_info
    print(f"  - AppKit: {'✓' if additional_info.get('appkit_available') else '✗'}")
    print(f"  - Quartz: {'✓' if additional_info.get('quartz_available') else '✗'}")
    print(f"  - pyautogui: {'✓' if additional_info.get('pyautogui_available') else '✗'}")
    print(f"  - pynput: {'✓' if additional_info.get('pynput_available') else '✗'}")
    print(f"  - CLI 工具: {', '.join(additional_info.get('cli_tools', []))}")
    print(f"  - 辅助功能权限: {'✓ 已授予' if additional_info.get('accessibility_enabled') else '✗ 未授予'}")

    # 2. 创建适配器
    print("\n=== 2. 创建适配器 ===")
    adapter = MacOSAdapter(platform_info)
    adapter.initialize()
    print("适配器创建成功 ✓")

    # 3. 测试键盘适配器
    print("\n=== 3. 测试键盘适配器 ===")
    print(f"可用方法: {adapter.keyboard.get_available_methods()}")
    print(f"是否可用: {'是' if adapter.keyboard.is_available() else '否'}")

    # 4. 测试剪贴板适配器
    print("\n=== 4. 测试剪贴板适配器 ===")
    test_text = "Test from macOS adapter - 测试中文"
    success = await adapter.clipboard.copy_text(test_text)
    print(f"复制测试: {'✓ 成功' if success else '✗ 失败'}")
    print(f"  复制的内容: {test_text}")
    print(f"  首选工具: {adapter.clipboard.get_preferred_tool()}")

    # 5. 测试粘贴命令
    print("\n=== 5. 测试粘贴命令 ===")
    print("请在以下 5 秒内打开一个文本编辑器并聚焦...")
    print("(例如: TextEdit, Notes, Terminal 等)")
    await asyncio.sleep(5)

    success = await adapter.keyboard.send_paste_command()
    print(f"粘贴命令 (Cmd+V): {'✓ 成功' if success else '✗ 失败'}")

    # 6. 测试 Ctrl+Enter
    print("\n=== 6. 测试 Ctrl+Enter ===")
    print("测试 Ctrl+Enter (将在 2 秒后发送)...")
    print("确保文本编辑器仍然聚焦...")
    await asyncio.sleep(2)
    success = await adapter.keyboard.send_ctrl_enter()
    print(f"Ctrl+Enter: {'✓ 成功' if success else '✗ 失败'}")

    # 7. 测试 keep-alive
    print("\n=== 7. 测试 Keep-Alive ===")
    print("测试保持活跃功能 (F15 键)...")
    success = await adapter.keyboard.keep_alive()
    print(f"Keep-Alive (F15): {'✓ 成功' if success else '✗ 失败'}")
    print("  (应该没有可见效果，这是正常的)")

    # 8. 测试通知声音
    print("\n=== 8. 测试通知声音 ===")
    print("准备播放通知声音...")
    success = adapter.notifications.play_notification_sound()
    print(f"声音播放: {'✓ 成功' if success else '✗ 失败'}")

    # 9. 测试 send_text
    print("\n=== 9. 测试直接文本输入 ===")
    print("测试 send_text() (将在 3 秒后发送 'Hello World')...")
    print("确保文本编辑器仍然聚焦...")
    await asyncio.sleep(3)
    success = await adapter.keyboard.send_text("Hello World")
    print(f"直接文本输入: {'✓ 成功' if success else '✗ 失败'}")

    # 总结
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

    # 提供设置建议
    if not additional_info.get('accessibility_enabled', False):
        print("\n⚠️  辅助功能权限未授予")
        print("如果键盘模拟不工作，请按照以下步骤操作:")
        print("1. 打开「系统设置」")
        print("2. 进入「隐私与安全性」→「辅助功能」")
        print("3. 点击锁图标并解锁")
        print("4. 添加「终端」或「Python」到允许列表")
        print("5. 重启 AIPut 应用")

    # 检测结果总结
    print("\n检测到的键盘模拟方法:")
    methods = adapter.keyboard.get_available_methods()
    for i, method in enumerate(methods, 1):
        print(f"  {i}. {method}")

    if 'cgevent' in methods:
        print("\n✓ 使用 CGEvent/Quartz (最可靠的方法)")
    elif 'pyautogui' in methods:
        print("\n✓ 使用 pyautogui (跨平台方法)")
    else:
        print("\n⚠️  仅使用 osascript (较慢的方法)")


if __name__ == "__main__":
    try:
        asyncio.run(test_macos_adapter())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
