---
name: "xcode-project-build-check"
description: "Run mandatory build verification after Swift/Xcode changes. Use when working in Swift repositories that may contain Swift Package Manager (`Package.swift`), Xcode projects (`.xcodeproj`), or workspaces (`.xcworkspace`), and the user expects build validation and fix-forward behavior. Always run `swift build` for package builds, run `xcodebuild` for Xcode builds, prioritize `.xcworkspace` over `.xcodeproj` when a workspace exists, and fix build errors before reporting completion."
---

# Xcode Project Build Check

## Overview

Enforce a strict post-change build check workflow for Swift/Xcode repositories. Execute builds, fix compile or linker failures, and re-run until clean.

## Required Behavior

1. Always run `swift build` when `Package.swift` exists.
2. Always run `xcodebuild` for Xcode artifacts.
3. If any `.xcworkspace` exists, use workspace-based builds and do not fall back to `.xcodeproj` unless explicitly requested.
4. If no workspace exists but `.xcodeproj` exists, use project-based builds.
5. If a build fails, fix the issue, then rerun the failed build command.
6. Do not report completion until the required builds pass or a hard blocker is identified.

## Discovery

Run from repo root:

```bash
test -f Package.swift && echo "has_package"
find . -type d -name "*.xcworkspace" -not -path "*/.build/*" -not -path "*/DerivedData/*"
find . -type d -name "*.xcodeproj" -not -path "*/.build/*" -not -path "*/DerivedData/*"
```

Resolve schemes with JSON output when possible:

```bash
xcodebuild -list -json -workspace "<workspace-path>"
xcodebuild -list -json -project "<project-path>"
```

## Build Workflow

### Step 1: Swift Package Build

If `Package.swift` exists:

```bash
swift build
```

If it fails, fix the errors and rerun `swift build` until it succeeds.

### Step 2: Xcode Workspace Build (Priority Path)

If at least one workspace exists, build workspace schemes.

1. Pick the target workspace.
2. Determine scheme:
   - Use user-specified scheme when provided.
   - Otherwise, choose a shared scheme from `xcodebuild -list -json -workspace`.
3. Build:

```bash
xcodebuild -workspace "<workspace-path>" -scheme "<scheme>" build
```

If destination errors occur, retry with an explicit destination that matches the project platform, for example:

```bash
xcodebuild -workspace "<workspace-path>" -scheme "<scheme>" -destination "generic/platform=iOS Simulator" build
```

### Step 3: Xcode Project Build (Fallback Only)

Use this only when no workspace exists:

```bash
xcodebuild -project "<project-path>" -scheme "<scheme>" build
```

## Fix-Forward Loop

When a build fails:

1. Capture the first actionable error from compiler or linker output.
2. Apply the smallest change that addresses that concrete failure.
3. Rerun the exact failed build command.
4. Repeat until pass or blocker.

Prioritize true build blockers:
- Swift compiler errors (`error:`)
- Linker errors (`Undefined symbols`, duplicate symbols)
- Missing imports/modules
- Signing or provisioning issues when they block local build validation

Treat warnings separately; do not stop once required builds pass unless user asked to clean warnings.

## Completion Report

Always report:

1. Commands executed
2. Which build path was used (`swift build`, workspace `xcodebuild`, or project `xcodebuild`)
3. Final status (pass/fail)
4. If fail, exact blocker and next command needed
