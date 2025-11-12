#!/usr/bin/env python3
"""
UI Protection System - Figma Integration

Protects Figma-generated UI components from accidental modification by agents.
Allows agents to modify business logic while preserving visual design.

Usage:
    protector = UIProtector()
    protector.mark_as_protected(Path("components/CalculatorUI.tsx"))
    result = protector.verify_ui_unchanged(Path("components/CalculatorUI.tsx"))
"""

import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional
import json


class UIProtector:
    """
    Detects if agents modified protected UI elements

    Monitors:
    - Tailwind class changes
    - Framer Motion prop changes
    - JSX structure changes
    - Color/spacing changes
    """

    def __init__(self):
        self.protected_files: Dict[Path, str] = {}
        self.cache_file = Path(".ui_protection_cache.json")
        self._load_cache()

    def _load_cache(self):
        """Load protected file hashes from cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.protected_files = {
                        Path(k): v for k, v in data.items()
                    }
            except Exception as e:
                print(f"Warning: Could not load UI protection cache: {e}")

    def _save_cache(self):
        """Save protected file hashes to cache"""
        try:
            data = {str(k): v for k, v in self.protected_files.items()}
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save UI protection cache: {e}")

    def mark_as_protected(self, file_path: Path) -> bool:
        """
        Mark a file as UI-protected

        Stores hash of UI elements to detect changes

        Returns:
            True if successfully protected, False otherwise
        """
        if not file_path.exists():
            print(f"❌ Cannot protect non-existent file: {file_path}")
            return False

        try:
            content = file_path.read_text()

            # Extract UI-sensitive elements
            ui_signature = self._extract_ui_signature(content)

            # Store hash
            file_hash = hashlib.sha256(ui_signature.encode()).hexdigest()
            self.protected_files[file_path] = file_hash

            # Save to cache
            self._save_cache()

            print(f"🔒 UI file protected: {file_path}")
            print(f"   Signature hash: {file_hash[:16]}...")
            return True

        except Exception as e:
            print(f"❌ Error protecting file {file_path}: {e}")
            return False

    def _extract_ui_signature(self, content: str) -> str:
        """
        Extract UI-relevant parts of code

        Captures:
        - className attributes
        - Framer Motion props (initial, animate, whileHover)
        - CSS/Tailwind classes
        - Layout structure (div, motion.div nesting)
        """

        # Extract all className values
        classnames = re.findall(r'className=[\"{`]([^\"{}`]+)[\"{`]', content)

        # Extract Framer Motion props
        motion_props = re.findall(
            r'(initial|animate|whileHover|whileTap|transition)=\{([^}]+)\}',
            content
        )

        # Extract JSX structure (element types)
        elements = re.findall(r'<(motion\.\w+|\w+)', content)

        # Extract inline styles
        inline_styles = re.findall(r'style=\{([^}]+)\}', content)

        # Combine into signature
        signature = {
            'classnames': sorted(classnames),
            'motion_props': sorted(str(p) for p in motion_props),
            'elements': sorted(elements),
            'inline_styles': sorted(inline_styles)
        }

        return str(signature)

    def verify_ui_unchanged(self, file_path: Path) -> Dict:
        """
        Verify that UI elements haven't changed

        Returns:
        {
            'protected': bool,
            'ui_changed': bool,
            'changes_detected': List[str],
            'current_hash': str,
            'original_hash': str
        }
        """

        if file_path not in self.protected_files:
            return {
                'protected': False,
                'ui_changed': False,
                'changes_detected': [],
                'current_hash': None,
                'original_hash': None
            }

        try:
            original_hash = self.protected_files[file_path]
            current_content = file_path.read_text()
            current_signature = self._extract_ui_signature(current_content)
            current_hash = hashlib.sha256(current_signature.encode()).hexdigest()

            ui_changed = original_hash != current_hash
            changes = []

            if ui_changed:
                changes = self._describe_ui_changes(
                    file_path,
                    current_content
                )

            return {
                'protected': True,
                'ui_changed': ui_changed,
                'changes_detected': changes,
                'current_hash': current_hash,
                'original_hash': original_hash
            }

        except Exception as e:
            return {
                'protected': True,
                'ui_changed': True,
                'changes_detected': [f"Error verifying file: {e}"],
                'current_hash': None,
                'original_hash': None
            }

    def _describe_ui_changes(
        self,
        file_path: Path,
        current_content: str
    ) -> List[str]:
        """
        Describe what UI changes were detected

        Returns list of human-readable change descriptions
        """

        changes = []

        # Basic detection - can be enhanced with detailed diff
        if "className" in current_content:
            changes.append("Tailwind classes may have been modified")

        if any(prop in current_content for prop in ["initial", "animate", "whileHover"]):
            changes.append("Framer Motion animations may have been altered")

        changes.append("UI elements were modified (run detailed diff for specifics)")

        return changes

    def unprotect(self, file_path: Path) -> bool:
        """
        Remove UI protection from a file

        Returns:
            True if successfully unprotected, False otherwise
        """
        if file_path in self.protected_files:
            del self.protected_files[file_path]
            self._save_cache()
            print(f"🔓 UI protection removed: {file_path}")
            return True
        else:
            print(f"⚠️  File was not protected: {file_path}")
            return False

    def list_protected_files(self) -> List[Path]:
        """Return list of all protected files"""
        return list(self.protected_files.keys())


class UIProtectionOrchestrator:
    """
    Integrates UI protection into workflow

    Workflow:
    1. User provides Figma design code
    2. Extract UI component, mark as protected
    3. Agents work on logic
    4. Before commit: verify UI unchanged
    5. Reject if UI was modified
    """

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.protector = UIProtector()

    def import_figma_design(
        self,
        figma_code: str,
        output_ui_file: Path,
        output_logic_file: Optional[Path] = None
    ) -> bool:
        """
        Import Figma code and protect UI file

        Process:
        1. Write Figma code to UI file
        2. Mark UI file as protected
        3. Optionally create logic file stub

        Returns:
            True if successful, False otherwise
        """

        try:
            # Ensure parent directory exists
            output_ui_file.parent.mkdir(parents=True, exist_ok=True)

            # Add protection comment to top of file
            protected_header = """// 🔒 UI-PROTECTED
// This file contains visual design from Figma
// DO NOT modify className, styles, animations, or layout
// Only data flow (props, handlers) can be changed

"""

            # Write UI file with protection header
            full_content = protected_header + figma_code
            output_ui_file.write_text(full_content)

            # Mark as protected
            self.protector.mark_as_protected(output_ui_file)

            # Create logic file stub if specified
            if output_logic_file:
                output_logic_file.parent.mkdir(parents=True, exist_ok=True)

                logic_stub = """// ✅ MODIFIABLE: Agents can change business logic here

export interface AppState {
  // Define your state here
}

export class AppEngine {
  private state: AppState;

  constructor() {
    this.state = {
      // Initialize state
    };
  }

  getState(): AppState {
    return { ...this.state };
  }
}
"""
                output_logic_file.write_text(logic_stub)
                print(f"📝 Logic file created: {output_logic_file}")

            print(f"✅ Figma design imported successfully")
            print(f"🔒 Protected UI file: {output_ui_file}")
            print(f"\n⚠️  Agents can modify logic but NOT {output_ui_file.name}")

            return True

        except Exception as e:
            print(f"❌ Error importing Figma design: {e}")
            return False

    def verify_before_commit(self) -> bool:
        """
        Verify all protected UI files before git commit

        Returns:
        - True if UI unchanged (safe to commit)
        - False if UI was modified (block commit)
        """

        all_safe = True
        protected_files = self.protector.list_protected_files()

        if not protected_files:
            print("ℹ️  No UI-protected files to verify")
            return True

        print(f"\n🔒 Verifying {len(protected_files)} protected UI file(s)...")

        for file_path in protected_files:
            result = self.protector.verify_ui_unchanged(file_path)

            if result['ui_changed']:
                print(f"\n❌ UI MODIFICATION DETECTED: {file_path}")
                print(f"   Changes: {', '.join(result['changes_detected'])}")
                print(f"   BLOCKED: Agents modified protected Figma design")
                all_safe = False
            else:
                print(f"✅ UI intact: {file_path}")

        if all_safe:
            print("\n✅ All protected UI files verified - safe to commit")
        else:
            print("\n❌ UI protection violated - commit blocked")
            print("   Please revert UI changes or update design in Figma first")

        return all_safe

    def get_protection_status(self) -> Dict:
        """
        Get status of all protected files

        Returns:
        {
            'total_protected': int,
            'files': [
                {
                    'path': str,
                    'ui_changed': bool,
                    'hash': str
                },
                ...
            ]
        }
        """

        protected_files = self.protector.list_protected_files()
        files_status = []

        for file_path in protected_files:
            result = self.protector.verify_ui_unchanged(file_path)
            files_status.append({
                'path': str(file_path),
                'ui_changed': result['ui_changed'],
                'hash': result['current_hash']
            })

        return {
            'total_protected': len(protected_files),
            'files': files_status
        }


if __name__ == "__main__":
    # Example usage
    print("UI Protection System - Test Mode")
    print("=" * 60)

    # Create test file
    test_file = Path("test_ui_component.tsx")
    test_content = """
import { motion } from 'framer-motion';

export function TestComponent() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-blue-500 text-white p-4"
    >
      Test Component
    </motion.div>
  );
}
"""
    test_file.write_text(test_content)

    # Test protection
    protector = UIProtector()
    protector.mark_as_protected(test_file)

    # Verify unchanged
    result = protector.verify_ui_unchanged(test_file)
    print(f"\nVerification result: {result}")

    # Modify file
    modified_content = test_content.replace("bg-blue-500", "bg-red-500")
    test_file.write_text(modified_content)

    # Verify again (should detect change)
    result = protector.verify_ui_unchanged(test_file)
    print(f"\nAfter modification: {result}")

    # Cleanup
    test_file.unlink()
    print("\n✅ Test complete")
