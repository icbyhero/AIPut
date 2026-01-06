# macOS 设置指南

本文档说明如何在 macOS 上设置和使用 AIPut。

## 安装步骤

### 1. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/newbe36524/AIPut.git
cd AIPut

# 安装 Python 依赖
pip install -e .
```

**注意**：PyObjC 框架会自动安装在 macOS 上，但在 Linux/Windows 上不会安装。

### 2. 授予辅助功能权限

AIPut 需要辅助功能权限才能模拟键盘输入。这是 macOS 的安全要求。

#### macOS 13 (Ventura) 及更高版本

1. 打开「系统设置」
2. 进入「隐私与安全性」→「辅助功能」
3. 点击锁图标并解锁（需要管理员密码）
4. 点击「+」按钮
5. 选择「终端」或「Python」（取决于你如何运行 AIPut）
6. 确保新添加的应用已启用

#### macOS 12 (Monterey) 及更低版本

1. 打开「系统偏好设置」
2. 进入「安全性与隐私」→「隐私」→「辅助功能」
3. 点击锁图标并解锁
4. 勾选「终端」或「Python」

### 3. 验证安装

运行测试脚本验证一切正常：

```bash
python tests/test_macos_adapter.py
```

测试脚本会：
- 检测平台和可用功能
- 测试剪贴板操作
- 测试键盘模拟（粘贴、Ctrl+Enter）
- 测试保持活跃功能
- 测试通知声音

**重要**：在测试过程中，按照脚本提示打开一个文本编辑器（如 TextEdit）并聚焦。

## 功能说明

### 键盘模拟方法

AIPut 在 macOS 上使用以下优先级的键盘模拟方法：

1. **CGEvent/Quartz** (最可靠)
   - 低级别 macOS API
   - 直接硬件访问
   - 需要 PyObjC 框架

2. **pyautogui** (跨平台)
   - 经过良好测试
   - 性能优秀

3. **AppKit/NSEvent** (原生 API)
   - macOS 高级别 API

4. **pynput** (替代库)
   - 另一种跨平台方案

5. **osascript** (内置，始终可用)
   - AppleScript
   - 较慢但可靠

### 保持活跃功能

AIPut 使用 F15 键来防止系统进入空闲状态。

**为什么使用 F15？**
- F15 是一个虚拟功能键（键码 160）
- 不存在于物理键盘上
- 对用户不可见，但仍能重置空闲计时器

**回退方法**（如果 F15 不可用）：
- Caps Lock 切换（可见但有效）
- caffeinate 命令（防止休眠）

### 剪贴板操作

- **方法 1**: pyperclip（Python 库）
- **方法 2**: pbcopy（macOS 内置命令）

### 通知声音

- **方法 1**: afplay（macOS 内置音频播放器）
- **方法 2**: NSSound via AppKit
- **方法 3**: osascript beep
- **方法 4**: 终端蜂鸣 (`\a`)

## 故障排除

### 键盘模拟不工作

**症状**：粘贴命令、Ctrl+Enter 等没有效果

**解决方案**：
1. 确认已授予辅助功能权限（见步骤 2）
2. 检查控制台输出，查看哪些方法可用
3. 如果看到 "未授予辅助功能权限" 警告，请重新授予权限并重启应用

### 声音不播放

**症状**：没有听到通知声音

**解决方案**：
1. 检查声音文件路径：`src/assets/029_Decline_09.wav`
2. 检查系统音量是否开启
3. 查看控制台 DEBUG 输出了解哪个方法失败

### PyObjC 安装失败

**症状**：`pip install` 时 PyObjC 相关错误

**解决方案**：
1. 确保使用 macOS 系统
2. 更新 pip：`pip install --upgrade pip`
3. 手动安装：`pip install pyobjc-core pyobjc-framework-Quartz pyobjc-framework-Cocoa`

## 与 Linux 的区别

| 功能 | Linux | macOS |
|------|-------|-------|
| 粘贴命令 | Shift+Insert | Cmd+V |
| 保持活跃键 | Scroll Lock | F15 |
| 显示协议 | X11/Wayland | Cocoa |
| 剪贴板工具 | xclip/wl-copy | pbcopy |
| 音频工具 | aplay/paplay | afplay |

## 技术细节

### 文件结构

```
src/platform_adapters/macos/
├── adapter.py          # 主适配器（所有功能）
└── (其他文件将来可能添加)

src/platform_detection/
└── detector.py         # 平台检测（已增强）

tests/
└── test_macos_adapter.py  # 测试脚本
```

### 架构

macOS 适配器遵循与 Linux 适配器相同的架构模式：

- **优先级回退链**：多个方法，自动回退
- **超时保护**：所有 subprocess 调用都有超时
- **错误处理**：完善的异常捕获和日志记录
- **平台检测**：自动检测可用工具和权限

## 性能

| 操作 | 预期时间 |
|------|---------|
| 粘贴命令 | < 2 秒 |
| Ctrl+Enter | < 2 秒 |
| 保持活跃 | < 1 秒 |
| 剪贴板复制 | < 1 秒 |
| 通知声音 | < 500ms |

## 支持

如有问题，请：
1. 查看控制台 DEBUG 输出
2. 运行测试脚本收集信息
3. 在 GitHub 上提 Issue：https://github.com/newbe36524/AIPut/issues
