# Figma UI Protection System - Implementation Guide

## Overview

The UI Protection System prevents AI agents from accidentally modifying Figma-designed visual elements while allowing them to work on business logic freely.

## Problem Solved

**Before UI Protection:**
- Figma generates beautiful UI + complete working code
- Agents might modify UI when changing logic (breaking design)
- No way to enforce separation between visual design and business logic

**After UI Protection:**
- Figma-generated UI files are marked as protected
- Agents instructed to never modify visual elements
- Automated detection of UI violations before commit
- Workflow blocked if protected files are modified

## Architecture

```
User provides Figma code
        ↓
UI Protection Orchestrator separates:
   - UI Component (🔒 Protected)
   - Logic Module (✅ Modifiable)
        ↓
Agents work on logic only
        ↓
Before Product Owner Review:
   - Verify protected files unchanged
   - Block if UI modifications detected
        ↓
Safe to commit
```

## Components

### 1. UI Protector (`ui_protector.py`)

Core protection logic:

```python
from pathlib import Path
from ui_protector import UIProtector

# Create protector
protector = UIProtector()

# Mark file as protected
protector.mark_as_protected(Path("components/CalculatorUI.tsx"))

# Verify file unchanged
result = protector.verify_ui_unchanged(Path("components/CalculatorUI.tsx"))
# Returns: {'ui_changed': bool, 'changes_detected': List[str]}
```

**What it tracks:**
- `className` attributes (Tailwind CSS)
- Framer Motion props (`initial`, `animate`, `whileHover`, etc.)
- JSX structure (element types, nesting)
- Inline styles

**How it works:**
1. Extracts UI signature (hash of visual elements)
2. Stores hash in `.ui_protection_cache.json`
3. On verification, re-extracts signature and compares hashes
4. Detects any changes to protected visual elements

### 2. UI Protection Orchestrator

High-level workflow integration:

```python
from pathlib import Path
from ui_protector import UIProtectionOrchestrator

# Create orchestrator
orchestrator = UIProtectionOrchestrator(Path("~/my-project"))

# Import Figma code
orchestrator.import_figma_design(
    figma_code=figma_generated_code,
    output_ui_file=Path("components/AppUI.tsx"),
    output_logic_file=Path("lib/appLogic.ts")
)

# Before git commit - verify protection
if not orchestrator.verify_before_commit():
    print("❌ UI protection violated - commit blocked")
else:
    print("✅ All protected files intact")
```

### 3. Orchestrator Integration

The main workflow (`orchestrator.py`) includes UI protection checks:

```python
class Orchestrator:
    def __init__(self, workspace_dir):
        # ... existing code ...
        self.ui_protector = UIProtectionOrchestrator(workspace_dir)

    def process_user_story(self, user_story):
        # ... agents work ...

        # BEFORE Product Owner review
        if not self._verify_ui_protection():
            return WorkflowResult(
                approved=False,
                errors=["UI protection violated"]
            )

        # Continue to PO review...
```

### 4. Agent Prompts

Agents are instructed about UI protection:

**Architect Prompt:**
```markdown
UI PROTECTION RULES:
Files marked with "🔒 UI-PROTECTED" are OFF-LIMITS.

YOU CAN:
- Update prop types/interfaces
- Modify event handlers
- Change data flow

YOU CANNOT:
- Change className or Tailwind classes
- Modify Framer Motion props
- Alter layout structure
- Change colors/spacing/styling
```

**Product Owner Prompt:**
```markdown
UI PROTECTION VERIFICATION:
- Check for "🔒 UI-PROTECTED" files
- Verify NO visual changes were made
- REJECT if UI protection violated
```

## Usage

### Step 1: Import Figma Design

When you have Figma-generated code, import it with protection:

```python
from ui_protector import UIProtectionOrchestrator

orchestrator = UIProtectionOrchestrator(workspace)

# Figma generated this complete component
figma_code = """
import { motion } from 'framer-motion';

export function Calculator() {
  // Complete implementation with UI + logic
}
"""

# Separate and protect
orchestrator.import_figma_design(
    figma_code=figma_code,
    output_ui_file=Path("components/CalculatorUI.tsx"),
    output_logic_file=Path("lib/calculatorLogic.ts")
)
```

This creates:

**components/CalculatorUI.tsx** (Protected):
```typescript
// 🔒 UI-PROTECTED
// This file contains visual design from Figma
// DO NOT modify className, styles, animations, or layout

import { motion } from 'framer-motion';

interface CalculatorUIProps {
  display: string;
  onButtonClick: (button: Button) => void;
}

export function CalculatorUI({ display, onButtonClick }: CalculatorUIProps) {
  // All Figma visual elements here
  return (
    <motion.div className="bg-black/40 backdrop-blur-xl">
      {/* Beautiful Figma UI */}
    </motion.div>
  );
}
```

**lib/calculatorLogic.ts** (Modifiable):
```typescript
// ✅ MODIFIABLE: Agents can change business logic

export class CalculatorEngine {
  inputDigit(digit: string): void { /* ... */ }
  performOperation(op: Operator): void { /* ... */ }
}
```

### Step 2: Run Workflow

Now run AI Scrum Master workflow:

```bash
./run.sh --workspace ~/my-app "Add scientific calculator functions"
```

The workflow will:
1. Architect implements `scientificLogic.ts` (not protected UI)
2. Security reviews logic only
3. Tester tests business logic
4. **UI Protection Check** - Verifies CalculatorUI.tsx unchanged
5. Product Owner reviews

If agents modify `CalculatorUI.tsx`:
```
❌ UI MODIFICATION DETECTED: components/CalculatorUI.tsx
   Changes: Tailwind classes may have been modified
   BLOCKED: Agents modified protected Figma design

❌ UI protection violated - commit blocked
   Please revert UI changes or update design in Figma
```

### Step 3: Update Visual Design

If you need visual changes:

1. **Do NOT ask agents** to modify UI
2. Go back to Figma
3. Update design in Figma
4. Re-export code
5. Re-import with protection:

```python
# Unprotect old file
orchestrator.protector.unprotect(Path("components/CalculatorUI.tsx"))

# Import new Figma design
orchestrator.import_figma_design(
    figma_code=new_figma_code,
    output_ui_file=Path("components/CalculatorUI.tsx")
)
```

## Configuration

**config.py:**
```python
UI_PROTECTION_CONFIG = {
    "enabled": True,
    "verify_before_po_review": True,
    "block_on_violation": True,
    "protected_file_marker": "🔒 UI-PROTECTED",
    "cache_file": ".ui_protection_cache.json"
}
```

## Manual Protection

You can manually protect any file:

```python
from ui_protector import UIProtector

protector = UIProtector()

# Protect an existing file
protector.mark_as_protected(Path("components/MyComponent.tsx"))

# List all protected files
protected = protector.list_protected_files()

# Unprotect a file
protector.unprotect(Path("components/MyComponent.tsx"))
```

## Benefits

✅ **Figma owns visual design** - Single source of truth
✅ **Agents own business logic** - Can iterate freely
✅ **No accidental UI breakage** - Protection enforced automatically
✅ **Clear separation** - UI vs Logic in different files
✅ **Version control** - Track UI changes separately
✅ **Workflow integration** - Automatic verification before commit

## Example Workflow

```bash
# 1. Create app with Figma
# User designs in Figma, exports code

# 2. Import to AI Scrum Master
$ python3
>>> from ui_protector import UIProtectionOrchestrator
>>> from pathlib import Path
>>> orch = UIProtectionOrchestrator(Path("~/my-app"))
>>> orch.import_figma_design(
...     figma_code=open("figma-export.tsx").read(),
...     output_ui_file=Path("components/AppUI.tsx"),
...     output_logic_file=Path("lib/appLogic.ts")
... )

# 3. Run AI Scrum Master for logic changes
$ ./run.sh --workspace ~/my-app "Add user authentication logic"

# Workflow runs:
# ✅ Architect adds auth to appLogic.ts
# ✅ Security reviews
# ✅ Tester tests
# 🔒 UI Protection Check: AppUI.tsx unchanged ✅
# ✅ Product Owner approves

# 4. Later: Update UI in Figma
# User changes button colors in Figma, re-exports

# 5. Re-import new design
$ python3
>>> orch.protector.unprotect(Path("components/AppUI.tsx"))
>>> orch.import_figma_design(...)

# 6. Continue development
$ ./run.sh --workspace ~/my-app "Add password reset feature"
```

## Troubleshooting

### UI Protection Violation Detected

**Problem:**
```
❌ UI MODIFICATION DETECTED: components/AppUI.tsx
```

**Solutions:**
1. **If change was intentional:** Update design in Figma and re-import
2. **If change was accidental:** Revert the file to original state
3. **If agents needed to change props:** That's allowed - check if it was just prop types (acceptable) vs visual styling (not allowed)

### Protected File Not Detected

**Problem:** File modified but no violation detected

**Cause:** File wasn't marked as protected

**Solution:**
```python
from ui_protector import UIProtector
protector = UIProtector()
protector.mark_as_protected(Path("components/YourFile.tsx"))
```

### False Positive Detection

**Problem:** Violation detected but only props changed (acceptable)

**Cause:** Current implementation detects any change - may need refinement

**Workaround:** Manually verify changes are prop-only, then unprotect and re-protect:
```python
protector.unprotect(Path("components/AppUI.tsx"))
# Make prop changes
protector.mark_as_protected(Path("components/AppUI.tsx"))
```

## Future Enhancements

**Planned for v2.6:**
- [ ] Automated code splitting (Figma export → UI + Logic automatically)
- [ ] More granular protection (allow prop changes, block only visual changes)
- [ ] Visual diff viewer (show exactly what changed)
- [ ] Figma API integration (fetch designs directly)
- [ ] Component extraction from screenshots

## Related Documentation

- [FIGMA_UI_PROTECTION.md](FIGMA_UI_PROTECTION.md) - Original design document
- [UI_DESIGNER_AGENT.md](UI_DESIGNER_AGENT.md) - Future Figma integration plans
- [VISUAL_TESTING_SYSTEM.md](VISUAL_TESTING_SYSTEM.md) - Visual verification system

## Version History

- **v2.5** - Initial UI Protection implementation
- Separation of Figma UI from business logic
- Automated protection verification
- Agent prompt updates
- Workflow integration
