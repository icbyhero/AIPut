"""
macOS-specific platform adapter implementation.
"""

import asyncio
import os
import sys
import subprocess
from typing import List, Optional, Dict, Any
from pathlib import Path

# macOS 虚拟键码常量（定义在 HIToolbox/Events.h 中）
# 这些是标准的 macOS 键码值，直接使用十六进制值
kVK_ANSI_A = 0x00
kVK_ANSI_B = 0x0B
kVK_ANSI_C = 0x08
kVK_ANSI_D = 0x02
kVK_ANSI_E = 0x0E
kVK_ANSI_F = 0x03
kVK_ANSI_G = 0x05
kVK_ANSI_H = 0x04
kVK_ANSI_I = 0x22
kVK_ANSI_J = 0x26
kVK_ANSI_K = 0x28
kVK_ANSI_L = 0x25
kVK_ANSI_M = 0x2E
kVK_ANSI_N = 0x2D
kVK_ANSI_O = 0x1F
kVK_ANSI_P = 0x23
kVK_ANSI_Q = 0x0C
kVK_ANSI_R = 0x0F
kVK_ANSI_S = 0x01
kVK_ANSI_T = 0x11
kVK_ANSI_U = 0x20
kVK_ANSI_V = 0x09
kVK_ANSI_W = 0x0D
kVK_ANSI_X = 0x07
kVK_ANSI_Y = 0x10
kVK_ANSI_Z = 0x06

kVK_ANSI_0 = 0x1D
kVK_ANSI_1 = 0x12
kVK_ANSI_2 = 0x13
kVK_ANSI_3 = 0x14
kVK_ANSI_4 = 0x15
kVK_ANSI_5 = 0x17
kVK_ANSI_6 = 0x16
kVK_ANSI_7 = 0x1A
kVK_ANSI_8 = 0x1C
kVK_ANSI_9 = 0x19

kVK_Space = 0x31
kVK_Return = 0x24
kVK_Tab = 0x30
kVK_Escape = 0x35

kVK_Command = 0x37
kVK_Shift = 0x38
kVK_CapsLock = 0x39
kVK_Option = 0x3A
kVK_Control = 0x3B

kVK_F1 = 0x7A
kVK_F2 = 0x78
kVK_F3 = 0x63
kVK_F4 = 0x76
kVK_F5 = 0x60
kVK_F6 = 0x61
kVK_F7 = 0x62
kVK_F8 = 0x64
kVK_F9 = 0x65
kVK_F10 = 0x6D
kVK_F11 = 0x67
kVK_F12 = 0x6F
kVK_F13 = 0x69
kVK_F14 = 0x6B
kVK_F15 = 0x71
kVK_F16 = 0x6A
kVK_F17 = 0x40
kVK_F18 = 0x4F
kVK_F19 = 0x50
kVK_F20 = 0x5A

kVK_ANSI_Grave = 0x32
kVK_ANSI_Minus = 0x1B
kVK_ANSI_Equal = 0x18
kVK_ANSI_LeftBracket = 0x21
kVK_ANSI_RightBracket = 0x1E
kVK_ANSI_Backslash = 0x2A
kVK_ANSI_Semicolon = 0x29
kVK_ANSI_Quote = 0x27
kVK_ANSI_Comma = 0x2B
kVK_ANSI_Period = 0x2F
kVK_ANSI_Slash = 0x2C

try:
    import pyautogui
    pyautogui.PAUSE = 0.1
    pyautogui.FAILSAFE = False
    PYAUTOGUI_AVAILABLE = True
except (ImportError, Exception):
    # 捕获 ImportError 和其他异常（例如 X11 连接错误）
    PYAUTOGUI_AVAILABLE = False
    pyautogui = None

try:
    import pyperclip
    PIPERCLIP_AVAILABLE = True
except (ImportError, Exception):
    PIPERCLIP_AVAILABLE = False
    pyperclip = None

try:
    import pystray
    from PIL import Image
    PYSTRAY_AVAILABLE = True
except (ImportError, Exception):
    # pystray 在导入时会尝试连接 X11，在 Linux 上可能失败
    PYSTRAY_AVAILABLE = False
    pystray = None
    Image = None

from platform_adapters.base import (
    KeyboardAdapter, ClipboardAdapter, SystemTrayAdapter,
    ResourceAdapter, NotificationAdapter, MenuItem
)
from platform_detection.detector import PlatformInfo


class MacOSKeyboardAdapter(KeyboardAdapter):
    """macOS keyboard adapter using pyautogui or AppleScript."""

    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
        self._methods = []
        self._detect_methods()

    def _detect_methods(self):
        """Detect available keyboard input methods with priority."""
        self._methods = []
        tools = self.platform_info.additional_info.get('cli_tools', [])
        capabilities = self.platform_info.additional_info

        # Priority 1: CGEvent/Quartz (最可靠，低级别 API)
        if capabilities.get('quartz_available'):
            try:
                from Quartz.CoreGraphics import CGEventCreateKeyboardEvent
                self._methods.append('cgevent')
            except Exception:
                pass

        # Priority 2: pyautogui (跨平台，经过良好测试)
        if PYAUTOGUI_AVAILABLE:
            try:
                # 快速测试确保它工作正常
                pyautogui.PAUSE = 0.1
                pyautogui.FAILSAFE = False
                self._methods.append('pyautogui')
            except Exception:
                pass

        # Priority 3: AppKit/NSEvent (原生 API)
        if capabilities.get('appkit_available'):
            try:
                from AppKit import NSEvent
                self._methods.append('appkit')
            except Exception:
                pass

        # Priority 4: pynput (替代库)
        if capabilities.get('pynput_available'):
            try:
                import pynput
                self._methods.append('pynput')
            except Exception:
                pass

        # Priority 5: osascript (内置，始终可用)
        if 'osascript' in tools:
            self._methods.append('osascript')

        # 警告：如果没有辅助功能权限
        if not capabilities.get('accessibility_enabled', False):
            print("警告：未授予辅助功能权限。键盘模拟可能无法正常工作。")
            print("请在系统设置 → 隐私与安全性 → 辅助功能中授权。")

    async def send_paste_command(self) -> bool:
        """发送粘贴命令（macOS 上为 Cmd+V），带回退链。"""
        # 方法 1: CGEvent/Quartz (优先级 1)
        if 'cgevent' in self._methods:
            try:
                from Quartz.CoreGraphics import (
                    CGEventCreateKeyboardEvent,
                    kCGEventFlagMaskCommand,
                    CGEventSetFlags,
                    CGEventPost,
                    kCGHIDEventTap
                )

                # 创建 Cmd+V 组合键事件
                # 方式：在 V 键按下事件上直接设置 Command 标志
                v_press = CGEventCreateKeyboardEvent(None, kVK_ANSI_V, True)
                CGEventSetFlags(v_press, kCGEventFlagMaskCommand)

                v_release = CGEventCreateKeyboardEvent(None, kVK_ANSI_V, False)
                CGEventSetFlags(v_release, kCGEventFlagMaskCommand)

                # 发送事件
                CGEventPost(kCGHIDEventTap, v_press)
                await asyncio.sleep(0.01)
                CGEventPost(kCGHIDEventTap, v_release)

                await asyncio.sleep(0.05)
                return True
            except Exception as e:
                print(f"[DEBUG] CGEvent 粘贴失败: {e}")

        # 方法 2: pyautogui (优先级 2)
        if 'pyautogui' in self._methods:
            try:
                pyautogui.hotkey('command', 'v')
                return True
            except Exception as e:
                print(f"[DEBUG] pyautogui 粘贴失败: {e}")

        # 方法 3: AppKit (优先级 3)
        if 'appkit' in self._methods:
            try:
                from AppKit import NSEvent, NSApplication
                event = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                    14,  # NSSystemDefined
                    (0, 0),
                    0x100000008,  # Cmd+V
                    0, 0, 0, 0, 0,
                    (35 << 16) | 0x0b,  # V 的 VK 码加上 Cmd
                    -1
                )
                NSApplication.sharedApplication().sendEvent_(event)
                return True
            except Exception as e:
                print(f"[DEBUG] AppKit 粘贴失败: {e}")

        # 方法 4: osascript (优先级 4 - 内置，始终可用)
        if 'osascript' in self._methods:
            try:
                script = '''
                tell application "System Events"
                    keystroke "v" using command down
                end tell
                '''
                proc = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    timeout=2,
                    check=False
                )
                return proc.returncode == 0
            except subprocess.TimeoutExpired:
                print("[DEBUG] osascript 粘贴超时")
                return False
            except Exception as e:
                print(f"[DEBUG] osascript 粘贴失败: {e}")

        return False

    async def send_ctrl_enter(self) -> bool:
        """发送 Ctrl+Enter 组合键（macOS 上为 Ctrl+Return），带回退链。"""
        # 方法 1: CGEvent/Quartz
        if 'cgevent' in self._methods:
            try:
                from Quartz.CoreGraphics import (
                    CGEventCreateKeyboardEvent,
                    kCGEventFlagMaskControl,
                    CGEventSetFlags,
                    CGEventPost,
                    kCGHIDEventTap
                )

                # 创建 Ctrl+Return 组合键事件
                return_press = CGEventCreateKeyboardEvent(None, kVK_Return, True)
                CGEventSetFlags(return_press, kCGEventFlagMaskControl)

                return_release = CGEventCreateKeyboardEvent(None, kVK_Return, False)
                CGEventSetFlags(return_release, kCGEventFlagMaskControl)

                # 发送事件
                CGEventPost(kCGHIDEventTap, return_press)
                await asyncio.sleep(0.01)
                CGEventPost(kCGHIDEventTap, return_release)

                await asyncio.sleep(0.05)
                return True
            except Exception as e:
                print(f"[DEBUG] CGEvent Ctrl+Enter 失败: {e}")

        # 方法 2: pyautogui
        if 'pyautogui' in self._methods:
            try:
                pyautogui.hotkey('ctrl', 'enter')
                return True
            except Exception as e:
                print(f"[DEBUG] pyautogui Ctrl+Enter 失败: {e}")

        # 方法 3: osascript
        if 'osascript' in self._methods:
            try:
                script = '''
                tell application "System Events"
                    keystroke return using control down
                end tell
                '''
                proc = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    timeout=2,
                    check=False
                )
                return proc.returncode == 0
            except (subprocess.TimeoutExpired, Exception) as e:
                print(f"[DEBUG] osascript Ctrl+Enter 失败: {e}")

        return False

    def is_available(self) -> bool:
        """Check if keyboard simulation is available."""
        return bool(self._methods)

    def get_available_methods(self) -> List[str]:
        """Get list of available methods."""
        return self._methods.copy()

    async def send_text(self, text: str) -> bool:
        """使用最可靠的方法直接发送文本。"""
        # 方法 1: CGEvent/Quartz (逐字符输入)
        if 'cgevent' in self._methods:
            try:
                from Quartz.CoreGraphics import (
                    CGEventCreateKeyboardEvent,
                    CGEventPost,
                    kCGHIDEventTap
                )

                for char in text:
                    # 将字符转换为键码
                    keycode = self._char_to_keycode(char)
                    if keycode is not None:
                        press = CGEventCreateKeyboardEvent(None, keycode, True)
                        release = CGEventCreateKeyboardEvent(None, keycode, False)
                        CGEventPost(kCGHIDEventTap, press)
                        CGEventPost(kCGHIDEventTap, release)
                        await asyncio.sleep(0.01)  # 字符之间的小延迟

                return True
            except Exception as e:
                print(f"[DEBUG] CGEvent send_text 失败: {e}")

        # 方法 2: pyautogui
        if 'pyautogui' in self._methods:
            try:
                pyautogui.typewrite(text, interval=0.01)
                return True
            except Exception as e:
                print(f"[DEBUG] pyautogui send_text 失败: {e}")

        return False

    def _char_to_keycode(self, char: str) -> Optional[int]:
        """将字符转换为 macOS 虚拟键码。"""
        # 字母
        if 'a' <= char.lower() <= 'z':
            return kVK_ANSI_A + (ord(char.lower()) - ord('a'))

        # 数字
        if '0' <= char <= '9':
            return kVK_ANSI_0 + int(char)

        # 常见标点符号
        mapping = {
            ' ': kVK_Space,
            '.': kVK_ANSI_Period,
            ',': kVK_ANSI_Comma,
            '/': kVK_ANSI_Slash,
            ';': kVK_ANSI_Semicolon,
            "'": kVK_ANSI_Quote,
            '[': kVK_ANSI_LeftBracket,
            ']': kVK_ANSI_RightBracket,
            '\\': kVK_ANSI_Backslash,
        }

        return mapping.get(char)

    async def keep_alive(self) -> bool:
        """macOS 保持活跃实现。

        macOS 没有 Scroll Lock 键，所以我们使用 F15 键（虚拟功能键）。
        这可以防止系统进入空闲/休眠状态。

        Returns:
            bool: 如果保持活跃成功执行返回 True，否则返回 False。
        """
        # 方法 1: CGEvent/Quartz 使用 F15 键
        if 'cgevent' in self._methods:
            try:
                from Quartz.CoreGraphics import (
                    CGEventCreateKeyboardEvent,
                    CGEventPost,
                    kCGHIDEventTap
                )

                # 发送 F15 两次，间隔 0.1 秒（匹配 Linux 模式）
                f15_press = CGEventCreateKeyboardEvent(None, kVK_F15, True)
                f15_release = CGEventCreateKeyboardEvent(None, kVK_F15, False)

                CGEventPost(kCGHIDEventTap, f15_press)
                CGEventPost(kCGHIDEventTap, f15_release)

                await asyncio.sleep(0.1)

                CGEventPost(kCGHIDEventTap, f15_press)
                CGEventPost(kCGHIDEventTap, f15_release)

                return True
            except Exception as e:
                print(f"[DEBUG] CGEvent keep-alive 失败: {e}")

        # 方法 2: pyautogui 使用 F15
        if 'pyautogui' in self._methods:
            try:
                pyautogui.press('f15')
                await asyncio.sleep(0.1)
                pyautogui.press('f15')
                return True
            except Exception as e:
                print(f"[DEBUG] pyautogui keep-alive 失败: {e}")

        # 方法 3: osascript - 切换 Caps Lock（可见但功能正常）
        if 'osascript' in self._methods:
            try:
                script = '''
                tell application "System Events"
                    key code 57  # Caps Lock
                end tell
                '''
                subprocess.run(['osascript', '-e', script], check=False, timeout=2, capture_output=True)
                await asyncio.sleep(0.1)
                subprocess.run(['osascript', '-e', script], check=False, timeout=2, capture_output=True)
                return True
            except Exception as e:
                print(f"[DEBUG] osascript keep-alive 失败: {e}")

        # 方法 4: caffeinate 命令（防止休眠，无键盘事件）
        try:
            # 这是回退方案 - 不理想因为需要进程管理
            # 但总比没有好
            subprocess.run(['caffeinate', '-u', '-t', '1'], check=False, timeout=2, capture_output=True)
            return True
        except Exception as e:
            print(f"[DEBUG] caffeinate keep-alive 失败: {e}")

        return False


class MacOSClipboardAdapter(ClipboardAdapter):
    """macOS clipboard adapter."""

    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
        cli_tools = platform_info.additional_info.get('cli_tools', [])
        self._has_pbcopy = 'pbcopy' in cli_tools
        self._has_pbpaste = 'pbpaste' in cli_tools
        self._preferred_tool = None

    def setup(self) -> None:
        """Initialize clipboard support."""
        # macOS has built-in clipboard support
        pass

    async def copy_text(self, text: str) -> bool:
        """复制文本到剪贴板，带回退链和超时保护。"""
        # 方法 1: pyperclip
        if PIPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(text)
                await asyncio.sleep(0.1)
                return True
            except Exception:
                pass

        # 方法 2: pbcopy 命令（内置）
        if self._has_pbcopy:
            try:
                proc = subprocess.run(
                    ['pbcopy'],
                    input=text.encode(),
                    timeout=1,
                    check=False
                )
                return proc.returncode == 0
            except subprocess.TimeoutExpired:
                print("[DEBUG] pbcopy 超时")
                return False
            except Exception as e:
                print(f"[DEBUG] pbcopy 失败: {e}")

        return False

    def is_available(self) -> bool:
        """Check if clipboard is available."""
        return True  # macOS always has clipboard

    def get_preferred_tool(self) -> Optional[str]:
        """Get preferred tool."""
        if PIPERCLIP_AVAILABLE:
            return 'pyperclip'
        if self._has_pbcopy:
            return 'pbcopy'
        return None


class MacOSSystemTrayAdapter(SystemTrayAdapter):
    """macOS system tray adapter."""

    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
        self.tray_icon = None

    def create_tray_icon(self, menu_items: List[MenuItem]) -> bool:
        """Create system tray icon."""
        if not self.is_supported():
            return False

        try:
            # Create menu items
            pystray_items = []
            for item in menu_items:
                pystray_items.append(
                    pystray.MenuItem(item.label, item.action)
                )

            # Create icon
            image = self._create_icon_image()

            # Create menu
            menu = pystray.Menu(*pystray_items)

            # Create tray icon
            self.tray_icon = pystray.Icon(
                "AIPut",
                image,
                "AIPut - Remote Input",
                menu
            )

            # Run in background
            import threading
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

            return True
        except Exception:
            return False

    def is_supported(self) -> bool:
        """Check if system tray is supported."""
        return PYSTRAY_AVAILABLE

    def hide_window(self) -> None:
        """Hide the main window."""
        pass

    def show_window(self) -> None:
        """Show the main window."""
        pass

    def stop(self) -> None:
        """Stop the tray icon."""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None

    def _create_icon_image(self):
        """Create macOS-style icon."""
        if Image:
            # Create a macOS-style icon
            image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            # Simple circle icon
            from PIL import ImageDraw
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 56, 56], fill='#007AFF')
            return image
        return None


class MacOSResourceAdapter(ResourceAdapter):
    """macOS resource adapter."""

    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info

    def get_icon_path(self, icon_names: List[str]) -> Optional[str]:
        """Get path to icon file."""
        # Check PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            for icon_name in icon_names:
                icon_path = os.path.join(sys._MEIPASS, icon_name)
                if os.path.exists(icon_path):
                    return icon_path

        # Check current directory
        for icon_name in icon_names:
            if os.path.exists(icon_name):
                return icon_name

        # Check Application Support directory
        app_support = self.get_app_data_dir()
        if app_support:
            for icon_name in icon_names:
                icon_path = os.path.join(app_support, 'icons', icon_name)
                if os.path.exists(icon_path):
                    return icon_path

        return None

    def get_resource_path(self, resource_name: str) -> Optional[str]:
        """Get path to resource file."""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            resource_path = os.path.join(sys._MEIPASS, resource_name)
            if os.path.exists(resource_path):
                return resource_path

        if os.path.exists(resource_name):
            return resource_name

        return None

    def load_image(self, path: str) -> Any:
        """Load an image file."""
        if Image:
            try:
                return Image.open(path)
            except:
                pass
        return path

    def get_app_data_dir(self) -> Optional[str]:
        """Get application data directory."""
        # Use ~/Library/Application Support on macOS
        home = os.path.expanduser('~')
        return os.path.join(home, 'Library', 'Application Support', 'AIPut')


class MacOSNotificationAdapter(NotificationAdapter):
    """macOS notification adapter using custom sound file."""

    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
        cli_tools = platform_info.additional_info.get('cli_tools', [])
        self._afplay_available = 'afplay' in cli_tools

        # 使用动态路径获取声音文件
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._custom_sound = os.path.join(base_dir, '..', '..', 'assets', '029_Decline_09.wav')
        self._custom_sound = os.path.abspath(self._custom_sound)

    def show_notification(self, title: str, message: str, duration: int = 5000) -> bool:
        """显示 macOS 通知（暂未实现）。"""
        return False

    def is_supported(self) -> bool:
        """Check if notifications are supported."""
        return True  # macOS 支持声音通知

    def play_notification_sound(self, sound_type: str = NotificationAdapter.SOUND_NOTIFICATION) -> bool:
        """播放自定义通知声音，带回退链。"""
        # 检查声音文件是否存在
        if not os.path.exists(self._custom_sound):
            print(f"[DEBUG] 声音文件未找到: {self._custom_sound}")
            return self._play_fallback_sounds()

        # 方法 1: afplay (内置，可靠)
        if self._afplay_available:
            try:
                subprocess.Popen(
                    ['afplay', self._custom_sound],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True
            except Exception as e:
                print(f"[DEBUG] afplay 失败: {e}")

        # 方法 2: NSSound via PyObjC
        try:
            from AppKit import NSSound
            sound = NSSound.alloc().initWithContentsOfFile_byReference_(self._custom_sound, True)
            if sound:
                sound.play()
                return True
        except Exception as e:
            print(f"[DEBUG] NSSound 失败: {e}")

        # 回退：系统蜂鸣
        return self._play_fallback_sounds()

    def _play_fallback_sounds(self) -> bool:
        """播放回退系统声音。"""
        # 尝试 osascript 播放系统声音
        try:
            script = 'beep'
            subprocess.Popen(['osascript', '-e', script],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"[DEBUG] osascript beep 失败: {e}")

        # 尝试 NSSound via PyObjC
        try:
            from AppKit import NSSound
            sound = NSSound.soundNamed_('Ping')
            if sound:
                sound.play()
                return True
        except Exception as e:
            print(f"[DEBUG] NSSound 失败: {e}")

        # 回退到终端蜂鸣
        try:
            print('\a', end='', flush=True)
            return True
        except:
            return False


class MacOSAdapter:
    """Main macOS adapter combining all sub-adapters."""

    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
        self.keyboard = MacOSKeyboardAdapter(platform_info)
        self.clipboard = MacOSClipboardAdapter(platform_info)
        self.system_tray = MacOSSystemTrayAdapter(platform_info)
        self.resources = MacOSResourceAdapter(platform_info)
        self.notifications = MacOSNotificationAdapter(platform_info)

    def initialize(self):
        """Initialize all adapters."""
        self.clipboard.setup()