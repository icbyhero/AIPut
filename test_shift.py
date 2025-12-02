"""
测试 Shift+Insert 的诊断脚本
用于诊断 Shift 键是否被正确发送
"""
import ctypes
import time
import pyperclip

# Windows API 常量
VK_SHIFT = 0x10
VK_INSERT = 0x2D
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

def test_method_1():
    """方法1: 使用 keybd_event (当前方法)"""
    print("\n=== 测试方法1: keybd_event ===")
    user32 = ctypes.windll.user32

    print("按下 Shift...")
    user32.keybd_event(VK_SHIFT, 0, 0, 0)
    time.sleep(0.1)

    print("按下 Insert...")
    user32.keybd_event(VK_INSERT, 0, 0, 0)
    time.sleep(0.05)

    print("释放 Insert...")
    user32.keybd_event(VK_INSERT, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)

    print("释放 Shift...")
    user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
    print("完成！")

def test_method_2():
    """方法2: 使用 SendInput (更现代的 API)"""
    print("\n=== 测试方法2: SendInput ===")

    # 定义 INPUT 结构
    PUL = ctypes.POINTER(ctypes.c_ulong)

    class KeyBdInput(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_ushort),
                    ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong),
                    ("dwExtraInfo", PUL)]

    class HardwareInput(ctypes.Structure):
        _fields_ = [("uMsg", ctypes.c_ulong),
                    ("wParamL", ctypes.c_short),
                    ("wParamH", ctypes.c_ushort)]

    class MouseInput(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long),
                    ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong),
                    ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong),
                    ("dwExtraInfo", PUL)]

    class Input_I(ctypes.Union):
        _fields_ = [("ki", KeyBdInput),
                    ("mi", MouseInput),
                    ("hi", HardwareInput)]

    class Input(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong),
                    ("ii", Input_I)]

    # 创建输入事件
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()

    # Shift 按下
    ii_.ki = KeyBdInput(VK_SHIFT, 0, 0, 0, ctypes.pointer(extra))
    shift_down = Input(ctypes.c_ulong(1), ii_)

    # Insert 按下
    ii_.ki = KeyBdInput(VK_INSERT, 0, 0, 0, ctypes.pointer(extra))
    insert_down = Input(ctypes.c_ulong(1), ii_)

    # Insert 释放
    ii_.ki = KeyBdInput(VK_INSERT, 0, KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
    insert_up = Input(ctypes.c_ulong(1), ii_)

    # Shift 释放
    ii_.ki = KeyBdInput(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
    shift_up = Input(ctypes.c_ulong(1), ii_)

    # 发送输入
    user32 = ctypes.windll.user32
    print("发送 Shift+Insert...")
    user32.SendInput(1, ctypes.pointer(shift_down), ctypes.sizeof(shift_down))
    time.sleep(0.05)
    user32.SendInput(1, ctypes.pointer(insert_down), ctypes.sizeof(insert_down))
    time.sleep(0.02)
    user32.SendInput(1, ctypes.pointer(insert_up), ctypes.sizeof(insert_up))
    time.sleep(0.02)
    user32.SendInput(1, ctypes.pointer(shift_up), ctypes.sizeof(shift_up))
    print("完成！")

def test_method_3():
    """方法3: 使用扫描码"""
    print("\n=== 测试方法3: 使用扫描码 ===")
    user32 = ctypes.windll.user32

    # 获取扫描码
    MAPVK_VK_TO_VSC = 0
    shift_scan = user32.MapVirtualKeyW(VK_SHIFT, MAPVK_VK_TO_VSC)
    insert_scan = user32.MapVirtualKeyW(VK_INSERT, MAPVK_VK_TO_VSC)

    print(f"Shift 扫描码: {shift_scan}, Insert 扫描码: {insert_scan}")

    KEYEVENTF_SCANCODE = 0x0008

    print("按下 Shift (扫描码)...")
    user32.keybd_event(VK_SHIFT, shift_scan, KEYEVENTF_SCANCODE, 0)
    time.sleep(0.1)

    print("按下 Insert (扫描码)...")
    user32.keybd_event(VK_INSERT, insert_scan, KEYEVENTF_SCANCODE | KEYEVENTF_EXTENDEDKEY, 0)
    time.sleep(0.05)

    print("释放 Insert (扫描码)...")
    user32.keybd_event(VK_INSERT, insert_scan, KEYEVENTF_SCANCODE | KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)

    print("释放 Shift (扫描码)...")
    user32.keybd_event(VK_SHIFT, shift_scan, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0)
    print("完成！")

def check_keyboard_state():
    """检查键盘状态"""
    print("\n=== 检查键盘状态 ===")
    user32 = ctypes.windll.user32

    shift_state = user32.GetKeyState(VK_SHIFT)
    print(f"Shift 键状态: {shift_state} (0=未按下, 负数=按下)")

    # 如果 Shift 卡住了，尝试释放
    if shift_state < 0:
        print("检测到 Shift 键卡住，尝试释放...")
        user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.1)
        shift_state = user32.GetKeyState(VK_SHIFT)
        print(f"释放后 Shift 键状态: {shift_state}")

if __name__ == '__main__':
    print("=" * 50)
    print("Shift+Insert 诊断工具")
    print("=" * 50)
    print("\n请将光标放在一个文本框中（比如记事本）")
    print("脚本将在 5 秒后开始测试...")

    # 先复制一些测试文本
    pyperclip.copy("测试文本 - Test Text")

    for i in range(5, 0, -1):
        print(f"{i}...", end=" ", flush=True)
        time.sleep(1)
    print("\n")

    # 检查键盘状态
    check_keyboard_state()

    # 测试方法1
    print("\n准备测试方法1，请确保光标在文本框中...")
    time.sleep(2)
    test_method_1()

    # 等待
    print("\n等待 3 秒...")
    time.sleep(3)

    # 测试方法2
    print("\n准备测试方法2，请确保光标在文本框中...")
    time.sleep(2)
    test_method_2()

    # 等待
    print("\n等待 3 秒...")
    time.sleep(3)

    # 测试方法3
    print("\n准备测试方法3，请确保光标在文本框中...")
    time.sleep(2)
    test_method_3()

    print("\n" + "=" * 50)
    print("测试完成！请检查哪个方法成功粘贴了文本")
    print("=" * 50)

    # 最后检查键盘状态
    check_keyboard_state()
