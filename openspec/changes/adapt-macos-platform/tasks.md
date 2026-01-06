# Tasks: macOS Platform Adapter Enhancement

## Overview

Ordered list of work items to implement the macOS platform adapter enhancement. Tasks are designed to deliver user-visible progress and can be worked on independently where possible.

## Phase 1: Foundation (Required for all other tasks)

### Task 1.1: Enhance macOS Platform Detection
**File**: `src/platform_detection/detector.py`
**Effort**: 30 minutes
**Dependencies**: None

**Changes**:
- [ ] Add CLI tools detection (osascript, afplay, pbcopy, pbpaste)
- [ ] Add Quartz framework availability check
- [ ] Add accessibility permission check using AXIsProcessTrusted()
- [ ] Update `_detect_macos_capabilities()` method
- [ ] Test detection on macOS system

**Validation**:
- Run `python -c "from platform_detection.detector import PlatformDetector; print(PlatformDetector.detect())"`
- Verify `cli_tools` list contains detected tools
- Verify `quartz_available` is True if PyObjC installed
- Verify `accessibility_enabled` reflects actual permission state

**Acceptance Criteria**:
- All CLI tools properly detected
- Quartz/PyObjC detection working
- Accessibility permission check working
- No crashes on systems without PyObjC

---

## Phase 2: Core Keyboard Functionality

### Task 2.1: Implement Enhanced Tool Detection
**File**: `src/platform_adapters/macos/adapter.py`
**Effort**: 45 minutes
**Dependencies**: Task 1.1

**Changes**:
- [ ] Rewrite `MacOSKeyboardAdapter._detect_methods()`
- [ ] Implement priority order: CGEvent > pyautogui > AppKit > pynput > osascript
- [ ] Add CGEvent/Quartz detection with import test
- [ ] Add AppKit/NSEvent detection with import test
- [ ] Add pynput detection with import test
- [ ] Verify osascript availability from platform detection

**Validation**:
- Create adapter instance and print `get_available_methods()`
- Verify priority order is correct
- Test on system with all dependencies
- Test on system with minimal dependencies

**Acceptance Criteria**:
- Methods detected in correct priority order
- At least osascript always available
- No crashes if some dependencies missing

---

### Task 2.2: Implement send_paste_command() with Fallback Chain
**File**: `src/platform_adapters/macos/adapter.py`
**Effort**: 2 hours
**Dependencies**: Task 2.1

**Changes**:
- [ ] Implement CGEvent/Quartz paste method (Cmd+V)
- [ ] Implement pyautogui paste method
- [ ] Implement AppKit/NSEvent paste method
- [ ] Implement pynput paste method (if library supports it)
- [ ] Implement osascript paste method
- [ ] Add debug logging for each method attempt
- [ ] Add timeout protection for osascript method

**Implementation Details**:

**CGEvent Method**:
```python
from Quartz.CoreGraphics import (
    CGEventCreateKeyboardEvent,
    kCGEventFlagMaskCommand,
    kVK_Command, kVK_ANSI_V,
    CGEventPost, kCGHIDEventTap
)

# Press Cmd, press V, release V, release Cmd
```

**osascript Method**:
```python
script = 'tell application "System Events" to keystroke "v" using command down'
subprocess.run(['osascript', '-e', script], timeout=2)
```

**Validation**:
- Manual test with text editor open
- Test each method individually (disable others)
- Verify Cmd+V actually pastes
- Verify fallback chain works (if CGEvent fails, pyautogui tries)

**Acceptance Criteria**:
- Cmd+V successfully pastes clipboard content
- Multiple methods attempt in priority order
- Debug logging shows which method succeeded
- No subprocess hangs (timeout protection works)

---

### Task 2.3: Implement send_ctrl_enter() with Fallback Chain
**File**: `src/platform_adapters/macos/adapter.py`
**Effort**: 1.5 hours
**Dependencies**: Task 2.1

**Changes**:
- [ ] Implement CGEvent/Quartz Ctrl+Enter method
- [ ] Implement pyautogui Ctrl+Enter method
- [ ] Implement AppKit/NSEvent Ctrl+Enter method
- [ ] Implement osascript Ctrl+Enter method
- [ ] Add debug logging and timeout protection

**Implementation Details**:

**CGEvent Method**:
```python
# Press Ctrl, press Return, release Return, release Ctrl
# Use kCGEventFlagMaskControl and kVK_Control
```

**Validation**:
- Manual test with messaging app or text editor
- Verify Ctrl+Enter behavior
- Test fallback chain

**Acceptance Criteria**:
- Ctrl+Enter successfully sent
- Fallback chain works
- No hangs or crashes

---

### Task 2.4: Implement keep_alive() Method
**File**: `src/platform_adapters/macos/adapter.py`
**Effort**: 1 hour
**Dependencies**: Task 2.1

**Changes**:
- [ ] Implement CGEvent/Quartz F15 key method
- [ ] Implement pyautogui F15 key method
- [ ] Implement osascript Caps Lock toggle fallback
- [ ] Add caffeinate command as final fallback
- [ ] Add debug logging

**Implementation Details**:

**CGEvent F15**:
```python
from Quartz.CoreGraphics import CGEventCreateKeyboardEvent, kVK_F15

# Press F15, release F15
# Wait 0.1s
# Press F15, release F15
```

**osascript Caps Lock**:
```python
# key code 57 = Caps Lock
# Send twice with 0.1s delay
```

**Validation**:
- Run keep_alive() and verify no visible effect
- Monitor system to ensure idle doesn't trigger
- Test each fallback method

**Acceptance Criteria**:
- F15 key sent twice with 0.1s delay
- System idle detection prevented
- No visible effect to user
- Multiple fallback methods work

---

### Task 2.5: Enhance send_text() Method
**File**: `src/platform_adapters/macos/adapter.py`
**Effort**: 1 hour
**Dependencies**: Task 2.1

**Changes**:
- [ ] Implement CGEvent character-by-character typing
- [ ] Add keycode mapping helper method
- [ ] Keep existing pyautogui fallback
- [ ] Add rate limiting (10ms delay between characters)

**Implementation Details**:

**Character to Keycode Mapping**:
- A-Z: kVK_ANSI_A (0) to kVK_ANSI_Z (25)
- 0-9: kVK_ANSI_0 (29) to kVK_ANSI_9 (38)
- Space: kVK_Space (49)
- Add support for common punctuation

**Validation**:
- Test with various text inputs
- Verify special characters work
- Test typing speed is reasonable

**Acceptance Criteria**:
- Text typed correctly character-by-character
- Support for alphanumeric and common punctuation
- Reasonable typing speed (~100 chars/sec)

---

## Phase 3: Support Components

### Task 3.1: Enhance Clipboard Adapter
**File**: `src/platform_adapters/macos/adapter.py`
**Effort**: 30 minutes
**Dependencies**: None

**Changes**:
- [ ] Add timeout protection to pbcopy subprocess
- [ ] Use platform detection for pbcopy availability
- [ ] Improve error messages
- [ ] Add debug logging

**Validation**:
- Test copy_text() with various inputs
- Verify clipboard content matches
- Test timeout protection (simulate slow pbcopy)

**Acceptance Criteria**:
- Clipboard copy works reliably
- Timeout protection prevents hangs
- Clear error messages for debugging

---

### Task 3.2: Enhance Notification Adapter
**File**: `src/platform_adapters/macos/adapter.py`
**Effort**: 30 minutes
**Dependencies**: None

**Changes**:
- [ ] Verify sound file path is dynamic (not hardcoded)
- [ ] Improve afplay error handling
- [ ] Add NSSound fallback improvements
- [ ] Add debug logging

**Validation**:
- Test sound playback
- Verify sound file found correctly
- Test fallback methods

**Acceptance Criteria**:
- Notification sound plays reliably
- Dynamic sound file path works
- Multiple fallback methods available

---

## Phase 4: Dependencies and Build

### Task 4.1: Add PyObjC Dependencies
**File**: `pyproject.toml`
**Effort**: 15 minutes
**Dependencies**: None

**Changes**:
- [ ] Add `pyobjc-core>=10.0; platform_system=='Darwin'`
- [ ] Add `pyobjc-framework-Quartz>=10.0; platform_system=='Darwin'`
- [ ] Add `pyobjc-framework-Cocoa>=10.0; platform_system=='Darwin'`
- [ ] Test install on macOS
- [ ] Test install on Linux (verify macOS packages not installed)

**Validation**:
```bash
# On macOS
pip install -e .
python -c "from Quartz.CoreGraphics import *; print('OK')"

# On Linux
pip install -e .
# Verify PyObjC packages not installed
```

**Acceptance Criteria**:
- PyObjC packages install on macOS
- PyObjC packages NOT installed on Linux/Windows
- Conditional dependencies work correctly

---

## Phase 5: Testing and Documentation

### Task 5.1: Create Automated Test Script
**File**: `tests/test_macos_adapter.py` (new file)
**Effort**: 1 hour
**Dependencies**: All implementation tasks

**Changes**:
- [ ] Create test file structure
- [ ] Add platform detection tests
- [ ] Add keyboard adapter tests
- [ ] Add clipboard adapter tests
- [ ] Add notification adapter tests
- [ ] Add integration tests

**Test Coverage**:
- Platform detection: All capabilities detected
- Keyboard: Each method tested individually
- Clipboard: Copy operations tested
- Notification: Sound playback tested
- Fallback chains: Test with methods disabled

**Validation**:
- Run `pytest tests/test_macos_adapter.py`
- Verify all tests pass
- Check test coverage

**Acceptance Criteria**:
- Test suite passes on macOS
- Tests cover all major functionality
- Tests can run in CI/CD

---

### Task 5.2: Create Manual Test Script
**File**: `scripts/test_macos_manual.py` (new file)
**Effort**: 45 minutes
**Dependencies**: All implementation tasks

**Changes**:
- [ ] Create user-friendly test script
- [ ] Add clear instructions for each test
- [ ] Add input prompts for manual verification
- [ ] Add result collection

**Test Flow**:
1. Display platform info
2. Test available methods
3. Guide user to open text editor
4. Test paste command (ask user to verify)
5. Test Ctrl+Enter (ask user to verify)
6. Test keep-alive (no visible effect expected)
7. Test notification sound (ask user to verify)
8. Display summary

**Validation**:
- Run script manually on macOS
- Follow instructions and verify each test
- Check output formatting

**Acceptance Criteria**:
- Clear, easy-to-follow instructions
- All functionality tested
- User can verify results easily
- Summary report helpful

---

### Task 5.3: Create macOS Setup Documentation
**File**: `docs/macos-setup.md` (new file)
**Effort**: 1 hour
**Dependencies**: All implementation tasks

**Content**:
- [ ] Installation instructions
- [ ] Accessibility permission setup guide
- [ ] PyObjC installation notes
- [ ] Troubleshooting section
- [ ] Common issues and solutions
- [ ] Testing verification steps

**Sections**:

**Installation**:
```bash
git clone <repo>
cd AIPut
pip install -e .
```

**Accessibility Permissions**:
1. Open System Settings
2. Privacy & Security → Accessibility
3. Add Terminal/Python
4. Restart application

**Troubleshooting**:
- "Keyboard simulation not working" → Check accessibility permissions
- "Sound not playing" → Verify afplay available
- "Paste not working" → Check clipboard permissions

**Validation**:
- Follow documentation on fresh macOS system
- Verify all steps are accurate
- Check screenshots (if any) are current

**Acceptance Criteria**:
- Complete, accurate setup guide
- Clear troubleshooting section
- User can successfully set up from documentation

---

### Task 5.4: Update Main README
**File**: `README.md`
**Effort**: 30 minutes
**Dependencies**: Task 5.3

**Changes**:
- [ ] Add macOS to supported platforms list
- [ ] Link to macOS setup guide
- [ ] Update platform support table
- [ ] Add macOS-specific notes

**Validation**:
- Verify links work
- Check formatting
- Ensure consistency with existing documentation

**Acceptance Criteria**:
- macOS properly documented
- Links correct and working
- No broken formatting

---

## Phase 6: Verification and Polish

### Task 6.1: Full Integration Testing
**Effort**: 2 hours
**Dependencies**: All previous tasks

**Testing**:
- [ ] Test on fresh macOS installation
- [ ] Test on different macOS versions (11, 12, 13, 14)
- [ ] Test with different Python versions (3.8, 3.9, 3.10, 3.11, 3.12)
- [ ] Test all fallback methods systematically
- [ ] Long-running stability test (1+ hour)
- [ ] Performance testing (measure operation times)

**Test Scenarios**:

**Scenario 1: Fresh Install**
- Install on clean macOS system
- Follow setup documentation
- Verify all features work

**Scenario 2: Upgrade Path**
- Install existing version
- Update to enhanced version
- Verify no breaking changes

**Scenario 3: Limited Dependencies**
- Test with only pyautogui (no PyObjC)
- Verify osascript fallback works

**Scenario 4: No Permissions**
- Test without accessibility permissions
- Verify graceful degradation
- Verify helpful error messages

**Acceptance Criteria**:
- All test scenarios pass
- No regressions on Linux
- No breaking changes
- Performance acceptable

---

### Task 6.2: Code Review and Refinement
**Effort**: 1 hour
**Dependencies**: Task 6.1

**Review Checklist**:
- [ ] Code follows project conventions
- [ ] Error handling is comprehensive
- [ ] Debug logging is helpful
- [ ] Comments are clear
- [ ] No hardcoded values (use constants)
- [ ] No code duplication
- [ ] Type hints where appropriate
- [ ] Docstrings for public methods

**Refinement Tasks**:
- [ ] Extract magic numbers to constants
- [ ] Remove code duplication
- [ ] Improve variable names
- [ ] Add missing docstrings
- [ ] Optimize any slow operations

**Acceptance Criteria**:
- Code passes all style checks
- Code is maintainable and clear
- No obvious bugs or issues

---

### Task 6.3: Performance Benchmarking
**Effort**: 1 hour
**Dependencies**: Task 6.1

**Measurements**:
- [ ] Paste command latency (each method)
- [ ] Ctrl+Enter latency (each method)
- [ ] Keep-alive latency (each method)
- [ ] Clipboard copy latency
- [ ] Notification sound latency

**Benchmarking Tool**:
```python
# benchmark_macos.py
import timeit

def benchmark_paste():
    # Time 100 paste operations
    times = []
    for _ in range(100):
        start = time.time()
        await adapter.keyboard.send_paste_command()
        times.append(time.time() - start)
    return statistics(times)
```

**Acceptance Criteria**:
- All operations complete in acceptable time
- Performance comparable to Linux implementation
- No memory leaks in long-running test

---

## Task Dependencies

```
Phase 1: Foundation
├── Task 1.1: Platform Detection

Phase 2: Core Functionality
├── Task 2.1: Tool Detection (requires 1.1)
├── Task 2.2: send_paste_command (requires 2.1)
├── Task 2.3: send_ctrl_enter (requires 2.1)
├── Task 2.4: keep_alive (requires 2.1)
└── Task 2.5: send_text (requires 2.1)

Phase 3: Support Components
├── Task 3.1: Clipboard (no dependencies)
└── Task 3.2: Notification (no dependencies)

Phase 4: Dependencies
└── Task 4.1: PyObjC (no dependencies)

Phase 5: Testing & Docs
├── Task 5.1: Automated Tests (requires all Phase 1-4)
├── Task 5.2: Manual Tests (requires all Phase 1-4)
├── Task 5.3: Setup Docs (requires all Phase 1-4)
└── Task 5.4: README Update (requires 5.3)

Phase 6: Verification
├── Task 6.1: Integration Tests (requires all Phase 1-5)
├── Task 6.2: Code Review (requires 6.1)
└── Task 6.3: Benchmarking (requires 6.1)
```

## Parallelization Opportunities

**Can be done in parallel**:
- Tasks 2.2, 2.3, 2.4, 2.5 (after 2.1 is complete)
- Tasks 3.1 and 3.2 (no dependencies on each other)
- Tasks 5.1, 5.2, 5.3 (after implementation is complete)

**Must be sequential**:
- Task 1.1 must be before 2.1
- Task 2.1 must be before 2.2-2.5
- Phase 6 requires all previous phases

## Estimated Timeline

| Phase | Tasks | Effort | Can Parallelize |
|-------|-------|--------|-----------------|
| Phase 1 | 1 task | 30 min | No |
| Phase 2 | 5 tasks | 6.5 hours | Partially |
| Phase 3 | 2 tasks | 1 hour | Yes |
| Phase 4 | 1 task | 15 min | No |
| Phase 5 | 4 tasks | 3 hours | Partially |
| Phase 6 | 3 tasks | 4 hours | Partially |
| **Total** | **16 tasks** | **15.25 hours** | **~12 hours with parallelization** |

## Success Criteria

All tasks completed when:
- ✅ Platform detection enhanced and tested
- ✅ All keyboard operations work with fallback chains
- ✅ Keep-alive functionality working
- ✅ Clipboard and notification components enhanced
- ✅ Dependencies added and tested
- ✅ Test suites created and passing
- ✅ Documentation complete
- ✅ Integration testing passes on multiple macOS versions
- ✅ Code reviewed and refined
- ✅ Performance benchmarks acceptable
