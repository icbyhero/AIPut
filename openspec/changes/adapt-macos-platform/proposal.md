# Proposal: Adapt macOS Platform Adapter

## Metadata

- **Change ID**: `adapt-macos-platform`
- **Title**: Enhance macOS platform adapter to match Linux implementation robustness
- **Status**: Proposed
- **Created**: 2025-01-06
- **Author**: User Request

## Problem Statement

The AIPut application currently has excellent Linux (Fedora) support for voice input keyboard operations with robust fallback mechanisms, multiple automation tool support, and comprehensive error handling. However, the macOS adapter, while present, lacks the same level of sophistication and reliability.

**Specific Issues**:
1. Keep-alive functionality not implemented (returns False)
2. Limited keyboard simulation methods without proper fallback chain
3. No low-level Quartz/CGEvent integration (most reliable on macOS)
4. Missing timeout protection on subprocess calls
5. No accessibility permission detection
6. Inconsistent error handling compared to Linux implementation

## Proposed Solution

Enhance the macOS platform adapter to match the robustness of the Linux implementation by:

1. **Enhanced Platform Detection**: Detect macOS CLI tools, PyObjC/Quartz availability, and accessibility permissions
2. **Robust Keyboard Simulation**: Implement priority-based fallback chain (CGEvent > pyautogui > AppKit > pynput > osascript)
3. **Keep-Alive Implementation**: Use F15 key (macOS equivalent to Scroll Lock) with fallback methods
4. **Timeout Protection**: Add timeout protection to all subprocess calls
5. **Accessibility Integration**: Detect permissions and provide user guidance
6. **Consistent Error Handling**: Match Linux adapter patterns for reliability

## Affected Components

- **src/platform_detection/detector.py**: Enhanced macOS capability detection
- **src/platform_adapters/macos/adapter.py**: Complete MacOSKeyboardAdapter rewrite
- **pyproject.toml**: Add PyObjC dependencies for macOS

## Benefits

- **Parity with Linux**: macOS users get same robust experience as Linux users
- **Multiple Fallback Methods**: If one method fails, others automatically take over
- **Better Reliability**: Low-level Quartz integration provides most reliable keyboard simulation
- **User-Friendly**: Accessibility permission detection guides users through setup
- **Future-Proof**: Multiple automation methods ensure compatibility across macOS versions

## Alternatives Considered

### Alternative 1: Minimal Fix (Keep Existing Code)
- **Pros**: Less code to write
- **Cons**: Unreliable, no fallback mechanisms, poor user experience
- **Decision**: Rejected - doesn't match project quality standards

### Alternative 2: Only pyautogui
- **Pros**: Simple, cross-platform
- **Cons**: Single point of failure, no fallback options
- **Decision**: Rejected - Linux implementation has multiple fallbacks for good reason

### Alternative 3: Full Enhancement (Selected)
- **Pros**: Matches Linux robustness, multiple fallbacks, best reliability
- **Cons**: More code to write and maintain
- **Decision**: Accepted - aligns with project architecture and quality standards

## Compatibility

- **Backward Compatible**: Yes, existing macOS code will be enhanced, not removed
- **Breaking Changes**: None
- **New Dependencies**: PyObjC frameworks (macOS only, conditional install)

## Migration Path

No migration needed - enhancement is transparent to existing code.

## Testing Plan

1. Test all keyboard simulation methods individually
2. Test fallback chain by disabling each method
3. Verify keep-alive prevents sleep
4. Test clipboard operations
5. Test notification sounds
6. Verify accessibility permission detection

## Related Specs

- `platform-abstraction`: Extends platform abstraction to macOS
- `notifications`: Uses notification sound system

## Success Criteria

- ✅ All keyboard operations work with multiple fallback methods
- ✅ Keep-alive functionality successfully prevents idle detection
- ✅ Clipboard operations work reliably
- ✅ Notification sounds play correctly
- ✅ Accessibility permissions properly detected
- ✅ Test suite passes all scenarios
- ✅ Manual testing confirms user expectations met
