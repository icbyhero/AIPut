# Spec: Platform macOS Support

## Overview

This spec defines requirements for macOS platform support in AIPut, bringing it to feature parity with the Linux implementation.

## ADDED Requirements

### Requirement: macOS Platform Detection

The system SHALL detect macOS-specific capabilities and tools.

#### Scenario: Detect macOS CLI Tools

**Given** the system is running on macOS
**When** platform detection runs
**Then** the system SHALL:
- Detect presence of osascript (built-in AppleScript interpreter)
- Detect presence of afplay (built-in audio player)
- Detect presence of pbcopy (built-in clipboard tool)
- Detect presence of pbpaste (built-in clipboard paste tool)
- Store detected tools in `PlatformInfo.additional_info['cli_tools']`

#### Scenario: Detect PyObjC Frameworks

**Given** the system is running on macOS
**When** platform detection runs
**Then** the system SHALL:
- Attempt to import Quartz framework
- Attempt to import AppKit framework
- Store availability in `additional_info['quartz_available']`
- Store availability in `additional_info['appkit_available']`

#### Scenario: Detect Accessibility Permissions

**Given** the system is running on macOS
**When** platform detection runs
**Then** the system SHALL:
- Check if application has accessibility permissions using AXIsProcessTrusted()
- Store permission status in `additional_info['accessibility_enabled']`
- Return True if permissions granted, False otherwise

---

### Requirement: macOS Keyboard Simulation

The system MUST provide robust keyboard simulation on macOS with multiple fallback methods.

#### Scenario: Detect Available Keyboard Methods

**Given** the macOS platform adapter is initialized
**When** method detection runs
**Then** the system SHALL detect methods in priority order:
1. CGEvent/Quartz (if Quartz framework available)
2. pyautogui (if pyautogui available)
3. AppKit/NSEvent (if AppKit available)
4. pynput (if pynput available)
5. osascript (always available as fallback)

#### Scenario: Send Paste Command

**Given** text has been copied to the clipboard
**And** a text editor is open and focused
**When** the system sends a paste command
**Then** the system SHALL:
- Send Cmd+V key combination (not Shift+Insert like Linux)
- Try CGEvent/Quartz method first
- Fall back to pyautogui if CGEvent fails
- Fall back to AppKit if pyautogui fails
- Fall back to pynput if AppKit fails
- Fall back to osascript if all other methods fail
- Return True if paste command sent successfully
- Return False if all methods fail

**Acceptance Criteria**:
- Clipboard content is pasted into the text editor
- Operation completes within 2 seconds
- No subprocess hangs (timeout protection)

#### Scenario: Send Ctrl+Enter

**Given** an application is focused that supports Ctrl+Enter
**When** the system sends Ctrl+Enter key combination
**Then** the system SHALL:
- Send Ctrl+Return key combination
- Try methods in priority order (CGEvent > pyautogui > AppKit > osascript)
- Return True if command sent successfully
- Return False if all methods fail

**Acceptance Criteria**:
- Ctrl+Enter action is triggered in the application
- Operation completes within 2 seconds

#### Scenario: Send Text Directly

**Given** an application is focused with a text input field
**When** the system sends text directly
**Then** the system SHALL:
- Use CGEvent to type character-by-character if available
- Fall back to pyautogui if CGEvent unavailable
- Insert 10ms delay between characters
- Support alphanumeric characters (A-Z, 0-9)
- Support common punctuation (space, comma, period, etc.)
- Return True if text sent successfully
- Return False if all methods fail

**Acceptance Criteria**:
- Text appears in input field character-by-character
- Typing speed is approximately 100 characters/second
- Special characters are typed correctly

---

### Requirement: macOS Keep-Alive Functionality

The system MUST prevent macOS idle detection to maintain system activity.

#### Scenario: Keep-Alive Using F15 Key

**Given** the macOS system is idle
**When** the system sends keep-alive signal
**Then** the system SHALL:
- Send F15 key press and release (virtual key code 160)
- Wait 0.1 seconds
- Send F15 key press and release again
- Use CGEvent/Quartz method if available
- Fall back to pyautogui if CGEvent fails
- Fall back to Caps Lock toggle via osascript as last resort
- Return True if keep-alive sent successfully
- Return False if all methods fail

**Acceptance Criteria**:
- No visible effect on user interface (F15 doesn't exist on physical keyboards)
- System idle timer is reset
- Operation can be called repeatedly without issues

**Note**: F15 is used instead of Scroll Lock (which doesn't exist on macOS) because it's a virtual function key with no physical equivalent, making it invisible to the user while still resetting idle timers.

#### Scenario: Keep-Alive Fallback Without Permissions

**Given** accessibility permissions are not granted
**And** CGEvent/PyAutoGUI methods fail
**When** the system sends keep-alive signal
**Then** the system SHALL:
- Fall back to caffeinate command
- Run `caffeinate -u -t 1` to prevent sleep for 1 second
- Return True if caffeinate succeeds
- Return False if caffeinate fails

---

### Requirement: macOS Clipboard Operations

The system MUST provide reliable clipboard operations on macOS.

#### Scenario: Copy Text to Clipboard

**Given** text needs to be copied to the clipboard
**When** the system performs clipboard copy
**Then** the system SHALL:
- Try pyperclip library first
- Fall back to pbcopy command (built-in)
- Add 100ms delay after copy to ensure clipboard update
- Use timeout protection (1 second) on pbcopy subprocess
- Return True if copy succeeds
- Return False if all methods fail

**Acceptance Criteria**:
- Text is available in clipboard after operation
- Clipboard content can be pasted manually with Cmd+V
- Operation completes within 1 second

#### Scenario: Detect Clipboard Tool Availability

**Given** the macOS platform adapter is initialized
**When** clipboard capabilities are checked
**Then** the system SHALL:
- Detect if pbcopy is available (from CLI tools detection)
- Detect if pyperclip is available
- Store preferred tool in adapter state
- Default to pbcopy if both available

---

### Requirement: macOS Notification Sounds

The system MUST play notification sounds on macOS.

#### Scenario: Play Custom Notification Sound

**Given** a custom sound file exists at `src/assets/029_Decline_09.wav`
**When** the system triggers notification sound
**Then** the system SHALL:
- Try afplay command first (built-in audio player)
- Fall back to NSSound via AppKit if afplay fails
- Fall back to osascript beep if NSSound fails
- Fall back to terminal bell (`\a`) if all else fails
- Play sound asynchronously (non-blocking)
- Return True if sound playback started
- Return False if all methods fail

**Acceptance Criteria**:
- Sound is audible to user
- Operation doesn't block application
- No error messages if sound file not found (graceful fallback)

#### Scenario: Handle Missing Sound File

**Given** the custom sound file does not exist
**When** the system triggers notification sound
**Then** the system SHALL:
- Log debug message about missing file
- Fall back to system beep immediately
- Not crash or raise exception
- Return True if fallback beep works

---

### Requirement: macOS Dependencies

The system MUST correctly manage macOS-specific dependencies.

#### Scenario: Conditional PyObjC Installation

**Given** a user installs AIPut dependencies
**When** installing on macOS
**Then** the package manager SHALL:
- Install `pyobjc-core>=10.0`
- Install `pyobjc-framework-Quartz>=10.0`
- Install `pyobjc-framework-Cocoa>=10.0`

#### Scenario: No PyObjC on Other Platforms

**Given** a user installs AIPut dependencies
**When** installing on Linux or Windows
**Then** the package manager SHALL:
- NOT install any PyObjC packages
- Skip packages marked with `; platform_system=='Darwin'`
- Only install cross-platform dependencies (pyautogui, etc.)

**Acceptance Criteria**:
- Linux users don't get macOS dependencies
- Windows users don't get macOS dependencies
- Installation completes successfully on all platforms

---

### Requirement: macOS Accessibility Permissions

The system MUST guide users to grant required permissions.

#### Scenario: Warn About Missing Permissions

**Given** the macOS adapter is initialized
**And** accessibility permissions are not granted
**When** the adapter initializes
**Then** the system SHALL:
- Log a warning message about missing permissions
- Explain that keyboard simulation may not work
- Provide instructions to grant permissions
- Not crash or prevent initialization

**Acceptance Criteria**:
- Warning is displayed in console/log
- Instructions are clear and actionable
- Adapter initialization completes even without permissions

#### Scenario: Permission Instructions

**Given** a user needs to grant accessibility permissions
**When** permission instructions are displayed
**Then** the instructions SHALL include:
1. Open System Settings
2. Navigate to Privacy & Security → Accessibility
3. Click lock icon to unlock (authenticate)
4. Add Terminal or Python to allowed applications
5. Restart AIPut application

**Acceptance Criteria**:
- Instructions work on macOS 13 (Ventura) and later
- Instructions also work on macOS 12 (Monterey) and earlier (System Preferences)
- Path is clear and unambiguous

---

## MODIFIED Requirements

### Requirement: Platform Abstraction Layer

The system MUST extend existing platform abstraction spec to include macOS.

#### Scenario: Platform Detection for macOS

**Given** the system starts on macOS
**When** platform detection runs
**Then** `PlatformInfo` SHALL contain:
- `os_name = 'Darwin'`
- `desktop_environment = 'Aqua'`
- `display_protocol = 'Cocoa'`
- `additional_info` with macOS-specific capabilities

#### Scenario: Adapter Factory for macOS

**Given** the system is running on macOS
**When** platform adapter factory creates adapter
**Then** it SHALL return `MacOSAdapter` instance
- With `MacOSKeyboardAdapter`
- With `MacOSClipboardAdapter`
- With `MacOSNotificationAdapter`
- With `MacOSResourceAdapter`
- With `MacOSSystemTrayAdapter`

---

## Requirements Mapping

| Requirement | Related Specs | Files to Modify |
|-------------|---------------|-----------------|
| macOS Platform Detection | platform-abstraction | detector.py |
| macOS Keyboard Simulation | platform-abstraction | macos/adapter.py |
| macOS Keep-Alive | platform-abstraction | macos/adapter.py |
| macOS Clipboard Operations | platform-abstraction | macos/adapter.py |
| macOS Notification Sounds | notifications | macos/adapter.py |
| macOS Dependencies | platform-abstraction | pyproject.toml |
| macOS Accessibility Permissions | platform-abstraction | macos/adapter.py, docs |

---

## Testing Requirements

### Unit Tests

- Test platform detection for all macOS capabilities
- Test each keyboard simulation method independently
- Test clipboard operations with various inputs
- Test notification sound playback
- Test fallback chains for all operations

### Integration Tests

- Test full workflow: copy → paste → Ctrl+Enter
- Test keep-alive prevents system sleep
- Test with accessibility permissions granted
- Test with accessibility permissions denied

### Manual Tests

- Test on fresh macOS installation
- Test on different macOS versions (11, 12, 13, 14)
- Test with different Python versions (3.8-3.12)
- Test all fallback methods systematically

---

## Non-Functional Requirements

### Performance

- Paste command: < 2 seconds
- Ctrl+Enter: < 2 seconds
- Keep-alive: < 1 second
- Clipboard copy: < 1 second
- Notification sound: < 500ms to start playback

### Reliability

- At least 3 fallback methods for keyboard operations
- At least 2 fallback methods for clipboard
- At least 4 fallback methods for notifications
- Graceful degradation if permissions missing

### Compatibility

- Support macOS 10.9+ (Python 3.8 requirement)
- Test on macOS 11 (Big Sur)
- Test on macOS 12 (Monterey)
- Test on macOS 13 (Ventura)
- Test on macOS 14 (Sonoma)

### Security

- Require accessibility permissions for keyboard simulation
- No subprocess injection vulnerabilities
- Proper escaping of all user input
- No sensitive data storage or logging

---

## Success Criteria

The macOS platform support is considered complete when:

✅ All ADDED requirements are implemented and tested
✅ All MODIFIED requirements are updated and tested
✅ Unit tests pass with > 80% code coverage
✅ Integration tests pass for all scenarios
✅ Manual testing confirmed on at least 3 macOS versions
✅ Documentation is complete and accurate
✅ Performance benchmarks meet requirements
✅ No regressions on Linux implementation
✅ User acceptance testing passes

---

## Dependencies

### Internal Dependencies

- `platform-abstraction` spec: Base adapter interfaces
- `notifications` spec: Notification sound system
- Existing Linux adapter implementation: Reference for patterns

### External Dependencies

- Python 3.8+
- PyObjC frameworks (macOS only):
  - pyobjc-core >= 10.0
  - pyobjc-framework-Quartz >= 10.0
  - pyobjc-framework-Cocoa >= 10.0
- pyautogui >= 0.9.54 (already in project)
- pyperclip >= 1.8.2 (already in project)

---

## Open Questions

### Question 1: F15 Key Availability

**Question**: Does F15 key work on all macOS versions for keep-alive?

**Investigation Needed**:
- Test on macOS 10.9-10.14 (earlier versions)
- Test on macOS 11-14 (recent versions)
- Verify no physical keyboards have F15 that would affect users

**Resolution**: Testing during Task 2.4 (keep_alive implementation)

### Question 2: Caps Lock Toggle Visibility

**Question**: Is Caps Lock toggle too intrusive as a fallback keep-alive method?

**Investigation Needed**:
- Test Caps Lock toggle visibility
- Survey user preference
- Consider mouse movement as alternative

**Resolution**: Decision during Task 2.4 based on testing

### Question 3: CGEvent Availability

**Question**: Are there any macOS configurations where CGEvent is unavailable even with PyObjC installed?

**Investigation Needed**:
- Test in sandboxed environments
- Test in restricted user accounts
- Test with various security profiles

**Resolution**: Testing during Task 2.1 (method detection)
