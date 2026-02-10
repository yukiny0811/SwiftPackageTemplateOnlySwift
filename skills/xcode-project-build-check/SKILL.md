---
name: "xcode-project-build-check"
description: "Run mandatory post-edit validation for Swift/Xcode repositories using Xcode MCP first and `xcodebuild` as fallback. Use when working in repositories with `Package.swift`, `.xcworkspace`, or `.xcodeproj`, and the user expects build/test verification with fix-forward behavior. Always run `swift build` for package builds. For Xcode artifacts, prefer Xcode MCP build/test actions; when no workspace/project is open in Xcode, open `.xcworkspace` (or `.xcodeproj`) and retry MCP before falling back to workspace-first `xcodebuild` build/test."
---

# Xcode Project Build Check

## Overview

Enforce a strict post-change verification workflow for Swift/Xcode repositories:
- Build required targets
- Run tests when tests exist
- Fix actionable failures and rerun until pass or hard blocker

## Required Behavior

1. Always run `swift build` when `Package.swift` exists.
2. For Xcode artifacts, prefer Xcode MCP (`BuildProject`, test actions) before shell `xcodebuild`.
3. If tests exist, run tests. Do not skip tests silently.
4. If `XcodeListWindows` returns no workspace windows, open `.xcworkspace` first (or `.xcodeproj` when no workspace exists), then retry MCP.
5. Keep `xcodebuild` workflow as fallback when MCP is unavailable, not connected, or still cannot operate on the target project after opening.
6. If validation fails, apply minimal fixes and rerun the same failing check.
7. Do not report completion until required checks pass or a concrete blocker is identified.

## Discovery

Run from repo root:

```bash
test -f Package.swift && echo "has_package"
find . -type d -name "*.xcworkspace" -not -path "*/.build/*" -not -path "*/DerivedData/*"
find . -type d -name "*.xcodeproj" -not -path "*/.build/*" -not -path "*/DerivedData/*"
```

## Workflow

### Step 1: Swift Package Build

If `Package.swift` exists:

```bash
swift build
```

If it fails, fix and rerun `swift build` until success or hard blocker.

### Step 2: Xcode MCP Path (Primary)

Use this path first whenever Xcode MCP tools are available.

1. Get active Xcode context with `XcodeListWindows`.
2. If no matching workspace/project window exists:
   - Open `.xcworkspace` when present:
     ```bash
     open "<workspace-path>"
     ```
   - Otherwise open `.xcodeproj`:
     ```bash
     open "<project-path>"
     ```
   - Wait briefly, then rerun `XcodeListWindows`.
3. Select the workspace tab that corresponds to the target repo.
4. Run `BuildProject(tabIdentifier: ...)`.
5. If build fails, inspect with:
   - `GetBuildLog`
   - `XcodeListNavigatorIssues`
   - `XcodeRefreshCodeIssuesInFile` (for affected files)
6. Apply fixes, then rerun `BuildProject`.

### Step 3: MCP Test Execution (When Tests Exist)

After build passes on MCP path:

1. Call `GetTestList(tabIdentifier: ...)`.
2. If test list is non-empty, run tests with `RunAllTests`.
3. If there is a reason to scope (for example one broken suite), use `RunSomeTests` with specific test identifiers.
4. If tests fail, fix and rerun the failing test action.
5. If no tests are available in the active scheme/test plan, report that tests were not present.

### Step 4: `xcodebuild` Fallback Path

Use this when MCP cannot be used (tool unavailable, no matching workspace tab even after open attempt, or MCP action failure unrelated to code).

If a workspace exists, prefer workspace commands:

```bash
xcodebuild -list -json -workspace "<workspace-path>"
xcodebuild -workspace "<workspace-path>" -scheme "<scheme>" build
```

If tests exist for the scheme, run tests:

```bash
xcodebuild -workspace "<workspace-path>" -scheme "<scheme>" test
```

If no workspace exists, use project commands:

```bash
xcodebuild -list -json -project "<project-path>"
xcodebuild -project "<project-path>" -scheme "<scheme>" build
xcodebuild -project "<project-path>" -scheme "<scheme>" test
```

If destination selection is required, use `xcodebuild -showdestinations ...` and rerun with an explicit simulator destination.

## Fix-Forward Loop

When a build/test fails:

1. Capture first actionable compiler/test failure.
2. Apply smallest concrete fix.
3. Rerun the exact failed action (`BuildProject`, `RunAllTests`, or fallback `xcodebuild` command).
4. Repeat until pass or hard blocker.

Prioritize true blockers:
- Swift compile errors (`error:`)
- Linker failures (`Undefined symbols`, duplicate symbols)
- Failing tests (assertions/crashes/timeouts)
- Signing/provisioning issues when they block local validation

Treat warnings separately unless user explicitly asks to resolve warnings.

## Completion Report

Always report:

1. Which path was used (`swift build`, Xcode MCP, fallback `xcodebuild`)
2. Build status
3. Test status (ran/passed/failed/not available)
4. If failed, exact blocker and next command/action needed
