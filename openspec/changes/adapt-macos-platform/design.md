# Design: macOS Platform Adapter Enhancement

## Overview

This document describes the design for enhancing the macOS platform adapter to match the robustness and reliability of the Linux implementation.

## Architecture

### Current Linux Architecture

```
LinuxAdapter
├── LinuxKeyboardAdapter
│   ├── WaylandKeyboardAdapter (wtype, ydotool, xdotool)
│   └── X11KeyboardAdapter (xdotool, xte, xvkbd)
├── LinuxClipboardAdapter (wl-copy, xclip, xsel)
├── LinuxNotificationAdapter (aplay, paplay)
└── LinuxResourceAdapter
```

**Key Features**:
- Display protocol detection (X11 vs Wayland)
- Specialized adapters for each environment
- Multiple automation tools with priority fallback
- Timeout protection on subprocess calls
- Keep-alive via Scroll Lock toggle

### Proposed macOS Architecture

```
MacOSAdapter
├── MacOSKeyboardAdapter (Enhanced)
│   ├── Priority 1: CGEvent/Quartz (low-level, most reliable)
│   ├── Priority 2: pyautogui (cross-platform)
│   ├── Priority 3: AppKit/NSEvent (native API)
│   ├── Priority 4: pynput (alternative library)
│   └── Priority 5: osascript (built-in, always available)
├── MacOSClipboardAdapter (pyperclip, pbcopy)
├── MacOSNotificationAdapter (afplay, NSSound, osascript)
└── MacOSResourceAdapter
```

**Key Features**:
- Priority-based fallback chain
- Low-level Quartz/CGEvent integration
- Keep-alive via F15 key toggle
- Timeout protection on subprocess calls
- Accessibility permission detection

## Component Design

### 1. Enhanced Platform Detection

**File**: `src/platform_detection/detector.py`

**Changes**:
```python
@staticmethod
def _detect_macos_capabilities() -> Dict[str, Any]:
    capabilities = {}

    # Python modules
    capabilities['quartz_available'] = check_module('Quartz')
    capabilities['appkit_available'] = check_module('AppKit')
    capabilities['pyautogui_available'] = check_module('pyautogui')
    capabilities['pynput_available'] = check_module('pynput')

    # CLI tools
    capabilities['cli_tools'] = detect_tools(['osascript', 'afplay', 'pbcopy', 'pbpaste'])

    # Accessibility permissions
    capabilities['accessibility_enabled'] = check_accessibility_permissions()

    return capabilities
```

**Rationale**:
- Mirrors Linux capability detection structure
- Provides detailed information for adapter to use
- Enables proper fallback chain based on available tools

### 2. MacOSKeyboardAdapter Enhancement

**Priority Order Justification**:

| Priority | Method | Reliability | Speed | Dependencies | Reason |
|----------|--------|-------------|-------|--------------|---------|
| 1 | CGEvent/Quartz | Highest | Fast | PyObjC | Low-level API, direct hardware access |
| 2 | pyautogui | High | Fast | pyautogui | Well-tested, cross-platform |
| 3 | AppKit/NSEvent | Medium | Medium | PyObjC | Native API, but higher-level |
| 4 | pynput | Medium | Slow | pynput | Alternative implementation |
| 5 | osascript | Low | Slow | None | Built-in, but slow due to subprocess |

**Method Detection**:
```python
def _detect_methods(self):
    self._methods = []

    # Detect in priority order
    if has_quartz():
        self._methods.append('cgevent')
    if has_pyautogui():
        self._methods.append('pyautogui')
    if has_appkit():
        self._methods.append('appkit')
    if has_pynput():
        self._methods.append('pynput')
    if has_osascript():
        self._methods.append('osascript')
```

**Paste Command Implementation**:

macOS uses `Cmd+V` (not `Shift+Insert` like Linux):

```python
async def send_paste_command(self) -> bool:
    # Try each method in priority order
    for method in self._methods:
        try:
            if await self._try_paste_with_method(method):
                return True
        except Exception:
            continue  # Try next method
    return False
```

**Key Differences from Linux**:
- macOS uses Command key instead of Shift
- Virtual key codes are different (kVK_Command vs Shift_L)
- Event posting system (CGEventPost vs xdotool subprocess)

### 3. Keep-Alive Implementation

**Challenge**: macOS doesn't have Scroll Lock key

**Solution**: Use F15 key (function key that doesn't exist on physical keyboards)

**Why F15?**:
- F15 is a virtual function key (key code 160)
- Doesn't exist on physical keyboards, so pressing it has no visible effect
- macOS recognizes it as valid keyboard input
- Prevents system idle detection without affecting user

**Alternatives Considered**:
1. **Caps Lock Toggle**: Visible to user (caps lock indicator), intrusive
2. **Mouse Movement**: Requires CGEvent mouse APIs, more complex
3. **caffeinate Command**: Prevents sleep but doesn't generate keyboard events
4. **F15 Key (Selected)**: Invisible, simple, effective

**Implementation**:
```python
async def keep_alive(self) -> bool:
    for method in self._methods:
        try:
            if method == 'cgevent':
                return await self._keep_alive_f15_cgevent()
            elif method == 'pyautogui':
                return await self._keep_alive_f15_pyautogui()
            elif method == 'osascript':
                return await self._keep_alive_capslock()  # Fallback
        except Exception:
            continue
    return False
```

**Pattern Matching Linux**:
- Send F15 twice with 0.1s delay (matches Linux Scroll Lock pattern)
- Multiple fallback methods
- Async implementation

### 4. Clipboard Enhancement

**Current Implementation**: Already good, minor improvements needed

**Enhancements**:
1. Add timeout protection to pbcopy subprocess call
2. Detect pbcopy/pbpaste availability from platform detection
3. Improve error messages for debugging

**No Major Changes Needed** - pyperclip and pbcopy work well on macOS.

### 5. Notification Enhancement

**Current Implementation**: Already good, minor improvements needed

**Enhancements**:
1. Verify sound file path is dynamic (not hardcoded)
2. Add better error handling for afplay
3. Improve fallback chain (NSSound, osascript beep)

**No Major Changes Needed** - afplay is built-in and reliable on macOS.

## Dependency Management

### PyObjC Frameworks

**Required Packages**:
```toml
"pyobjc-core>=10.0; platform_system=='Darwin'"
"pyobjc-framework-Quartz>=10.0; platform_system=='Darwin'"
"pyobjc-framework-Cocoa>=10.0; platform_system=='Darwin'"
```

**Environment Markers**:
- `; platform_system=='Darwin'` ensures these only install on macOS
- Linux/Windows users won't download these dependencies
- Uses `pyproject.toml` conditional dependencies

**Version Selection**:
- PyObjC 10.0+ supports macOS 10.9+
- Aligns with Python 3.8+ requirement
- Active maintenance and good compatibility

### Optional Dependencies

**Already in Project**:
- pyautogui: Cross-platform automation
- pyperclip: Cross-platform clipboard
- pystray: Cross-platform system tray

**No Additional Dependencies Required**

## Error Handling Strategy

### Pattern from Linux Implementation

```python
# Linux pattern (example from x11.py)
if 'xdotool' in self._methods:
    try:
        subprocess.run(['xdotool', 'key', 'Shift+Insert'],
                      check=False, timeout=1)
        return True
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass  # Try next method
```

### macOS Adaptation

```python
# macOS pattern (matching Linux)
if 'cgevent' in self._methods:
    try:
        # CGEvent implementation
        return True
    except Exception as e:
        print(f"[DEBUG] CGEvent failed: {e}")
        pass  # Try next method

if 'pyautogui' in self._methods:
    try:
        pyautogui.hotkey('command', 'v')
        return True
    except Exception as e:
        print(f"[DEBUG] pyautogui failed: {e}")
        pass  # Try next method
```

**Key Principles**:
1. Try methods in priority order
2. Catch specific exceptions
3. Log debug information
4. Continue to next method on failure
5. Return False only if all methods fail

### Timeout Protection

**Linux Example**:
```python
subprocess.run(['xdotool', ...], timeout=1)
```

**macOS Adaptation**:
```python
subprocess.run(['osascript', ...], timeout=2)
```

**Timeout Values**:
- xdotool: 1 second (fast, direct X11)
- osascript: 2 seconds (slower, AppleScript compilation)
- pbcopy: 1 second (fast, built-in)
- afplay: No timeout (async Popen, background process)

## Accessibility Permissions

### macOS Security Model

macOS requires applications to have Accessibility permissions to:
- Simulate keyboard input
- Simulate mouse events
- Control other applications

### Detection Method

```python
def check_accessibility_permissions() -> bool:
    try:
        from AppKit import AXIsProcessTrusted
        return AXIsProcessTrusted()
    except Exception:
        return False
```

### User Guidance

If permissions are missing, provide clear instructions:

```
macOS Accessibility Permissions Required:

AIPut needs Accessibility permissions to simulate keyboard input.

To grant permissions:
1. Open System Settings
2. Go to Privacy & Security → Accessibility
3. Click the lock icon to unlock
4. Add Terminal or Python to the list
5. Restart AIPut

For more information: https://support.apple.com/guide/mac-help/change-accessibility-preferences-mh43185/mac
```

### Implementation Location

Add to MacOSKeyboardAdapter initialization:

```python
def __init__(self, platform_info: PlatformInfo):
    self.platform_info = platform_info
    self._detect_methods()

    # Warn if accessibility is not enabled
    if not platform_info.additional_info.get('accessibility_enabled', False):
        print("WARNING: Accessibility permissions not granted.")
        print("Keyboard simulation may not work correctly.")
        print("Please grant permissions in System Settings.")
```

## Testing Strategy

### Unit Testing

Each method tested independently:

```python
async def test_cgevent_paste():
    adapter = MacOSKeyboardAdapter(platform_info)
    assert 'cgevent' in adapter.get_available_methods()
    result = await adapter.send_paste_command()
    assert result is True
```

### Integration Testing

Test full workflow:

```python
async def test_full_workflow():
    # 1. Copy text to clipboard
    await adapter.clipboard.copy_text("Hello World")

    # 2. Send paste command
    await adapter.keyboard.send_paste_command()

    # 3. Send Ctrl+Enter
    await adapter.keyboard.send_ctrl_enter()

    # 4. Keep-alive
    await adapter.keyboard.keep_alive()
```

### Manual Testing

User-facing test script:

```python
# test_macos_manual.py
# - Guides user through manual testing
# - Provides clear instructions
# - Collects feedback on each operation
```

## Performance Considerations

### Method Speed Comparison

| Method | Speed | Notes |
|--------|-------|-------|
| CGEvent/Quartz | ~1ms | Direct hardware access |
| pyautogui | ~5ms | Cross-platform overhead |
| AppKit/NSEvent | ~10ms | Higher-level API |
| pynput | ~20ms | Additional abstraction layer |
| osascript | ~100ms | Subprocess + AppleScript compilation |

### Optimization Strategies

1. **Cache Available Methods**: Don't re-detect on every call
2. **Reuse Event Objects**: For CGEvent, create and reuse
3. **Async Operations**: All methods are async for non-blocking
4. **Timeout Protection**: Prevent hanging on slow methods

### Memory Usage

- PyObjC frameworks: ~10MB (loaded once)
- pyautogui: ~5MB
- Adapter objects: <1KB

**No Memory Leaks**: Proper cleanup of all resources.

## Security Considerations

### Accessibility Permissions

- Required for keyboard simulation
- User must explicitly grant
- System enforces permission checking

### Subprocess Execution

- osascript commands: Escaped to prevent injection
- No user input directly passed to shell
- Use list arguments, not string commands

### Clipboard Access

- Read/write clipboard
- No sensitive data storage
- Local operations only

## Future Enhancements

### Potential Improvements

1. **iWork Support**: Special handling for Numbers/Pages/Keynote
2. **Keyboard Layouts**: Better international keyboard support
3. **Mouse Simulation**: Add mouse movement if needed
4. **Voice Direct**: Microphone input on desktop (if requested)

### Extension Points

- Easy to add new keyboard simulation methods
- Modular adapter architecture allows per-platform customization
- Fallback chain can be extended

## Compatibility Matrix

| macOS Version | Quartz | pyautogui | AppKit | pynput | osascript |
|---------------|--------|-----------|--------|--------|-----------|
| 10.9+         | ✅     | ✅        | ✅     | ✅     | ✅        |
| 10.15+        | ✅     | ✅        | ✅     | ✅     | ✅        |
| 11.0+         | ✅     | ✅        | ✅     | ✅     | ✅        |
| 12.0+         | ✅     | ✅        | ✅     | ✅     | ✅        |
| 13.0+         | ✅     | ✅        | ✅     | ✅     | ✅        |
| 14.0+         | ✅     | ✅        | ✅     | ⚠️     | ✅        |

**Notes**:
- All methods work on macOS 10.9+ (Python 3.8 requirement)
- pynput may have issues on macOS 14+ (sandboxing)
- osascript always available (built-in)

## Conclusion

This design brings macOS adapter to feature parity with Linux implementation while accounting for platform-specific differences. The priority-based fallback chain ensures reliability, and the low-level Quartz integration provides the best possible performance on macOS.

The architecture maintains the existing project patterns (delegation, fallback chains, error handling) while respecting macOS's unique characteristics (security model, key codes, APIs).
