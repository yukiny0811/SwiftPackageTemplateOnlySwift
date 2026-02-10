---
name: swiftui-ui-builder
description: Create and edit SwiftUI UI screens and components in `.swift` files. Use when the user asks for SwiftUI layout, visual styling, component composition, or screen refactors. Prefer adding `#Preview` whenever practical. After editing any Swift file that contains `#Preview`, render previews with Xcode MCP and save snapshots in the same directory as `SwiftFileName_PreviewName.png`.
---

# SwiftUI UI Builder

## Core Rules

1. Implement UI with SwiftUI-native patterns (`View` composition, modifiers, extracted subviews).
2. Add `#Preview` whenever practical when creating or editing SwiftUI UI.
3. When editing a file that contains `#Preview`, always render preview snapshots with Xcode MCP.
4. Save each rendered snapshot next to the Swift file using `SwiftFileName_PreviewName.png`.
5. If preview rendering fails, fix the error and rerender before reporting completion.

## Workflow

### 1) Edit the SwiftUI file

Apply the requested UI change in the target Swift file.

If `#Preview` is missing but practical to add, add at least one preview macro.  
If adding preview is not practical (for example heavy runtime dependency), state the reason explicitly.

### 2) Prepare Xcode MCP context

1. Call `XcodeListWindows`.
2. If no matching workspace/project is open:
   - Open `.xcworkspace` first when available:
     ```bash
     open "<workspace-path>"
     ```
   - Otherwise open `.xcodeproj`:
     ```bash
     open "<project-path>"
     ```
3. Wait briefly, then call `XcodeListWindows` again.
4. Select the matching `tabIdentifier`.

### 3) Enumerate previews in the edited file

Use:

```bash
python3 skills/swiftui-ui-builder/scripts/preview_snapshot_name.py --source "<source-file>" --list --format json
```

This returns preview indices and output filenames.

### 4) Render and save snapshots

For each preview index in that file:

1. Render:
   - `RenderPreview(tabIdentifier: ..., sourceFilePath: "...", previewDefinitionIndexInFile: <index>)`
2. Read `previewSnapshotPath` from the MCP result.
3. Copy snapshot to the required destination name:

```bash
python3 skills/swiftui-ui-builder/scripts/preview_snapshot_name.py \
  --source "<source-file>" \
  --index <index> \
  --snapshot "<previewSnapshotPath>" \
  --format json
```

The script saves a PNG in the same directory as the Swift file with this naming pattern:
- `SwiftFileName_PreviewName.png`
- Unnamed preview fallback: `Preview<index>`
- Duplicate preview names: append `-<index>` to avoid overwrite

### 5) Report results

Always report:
1. Edited Swift file(s)
2. Whether `#Preview` was added or already present
3. Rendered preview indices
4. Saved snapshot file paths
5. Any preview/build blocker that remains

## Script

### `scripts/preview_snapshot_name.py`

Purpose:
- Parse `#Preview` macros in a Swift file
- Generate deterministic snapshot filenames
- Optionally copy MCP `previewSnapshotPath` to the final destination

Examples:

```bash
python3 skills/swiftui-ui-builder/scripts/preview_snapshot_name.py --source Demo/Demo/ContentView.swift --list
python3 skills/swiftui-ui-builder/scripts/preview_snapshot_name.py --source Demo/Demo/ContentView.swift --index 0
python3 skills/swiftui-ui-builder/scripts/preview_snapshot_name.py --source Demo/Demo/ContentView.swift --index 0 --snapshot /tmp/preview.png
```
