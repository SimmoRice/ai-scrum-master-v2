#!/usr/bin/env python3
"""
Helper script to import Figma UI with protection
"""

from pathlib import Path
from ui_protector import UIProtectionOrchestrator

# Your Figma-generated UI code
figma_code = """import { motion } from 'motion/react';

export function Calculator() {
  const buttons = [
    { label: 'AC', type: 'function', span: 1 },
    { label: '±', type: 'function', span: 1 },
    { label: '%', type: 'function', span: 1 },
    { label: '÷', type: 'operator', span: 1 },

    { label: '7', type: 'number', span: 1 },
    { label: '8', type: 'number', span: 1 },
    { label: '9', type: 'number', span: 1 },
    { label: '×', type: 'operator', span: 1 },

    { label: '4', type: 'number', span: 1 },
    { label: '5', type: 'number', span: 1 },
    { label: '6', type: 'number', span: 1 },
    { label: '-', type: 'operator', span: 1 },

    { label: '1', type: 'number', span: 1 },
    { label: '2', type: 'number', span: 1 },
    { label: '3', type: 'number', span: 1 },
    { label: '+', type: 'operator', span: 1 },

    { label: '0', type: 'number', span: 2 },
    { label: '.', type: 'number', span: 1 },
    { label: '=', type: 'operator', span: 1 },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="w-full max-w-sm"
    >
      <div className="bg-gray-800/80 backdrop-blur-xl rounded-3xl p-6 shadow-2xl shadow-white/10 border border-white/30">
        {/* Display */}
        <div className="mb-6 px-4 py-8 text-right">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-white text-6xl tracking-tight overflow-hidden"
          >
            0
          </motion.div>
        </div>

        {/* Buttons Grid */}
        <div className="grid grid-cols-4 gap-3">
          {buttons.map((button, index) => (
            <motion.button
              key={index}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {}}
              className={`
                h-20 rounded-2xl transition-all duration-200 flex items-center justify-center
                ${button.span === 2 ? 'col-span-2' : ''}
                ${
                  button.type === 'operator'
                    ? 'bg-gradient-to-br from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-500 text-white shadow-lg shadow-orange-500/50'
                    : button.type === 'function'
                    ? 'bg-gradient-to-br from-gray-400 to-gray-500 hover:from-gray-300 hover:to-gray-400 text-black shadow-lg shadow-gray-500/30'
                    : 'bg-gradient-to-br from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-white shadow-lg shadow-gray-800/50'
                }
                relative overflow-hidden group
              `}
            >
              <span className="relative z-10 text-3xl">{button.label}</span>

              {/* Glow effect on hover */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className="absolute inset-0 bg-white/20 rounded-2xl blur-xl" />
              </div>
            </motion.button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
"""

# Workspace directory
workspace = Path.home() / "Development/repos/calculator-app-by-ai"

# Create UI protection orchestrator
orchestrator = UIProtectionOrchestrator(workspace)

print("🎨 Importing Figma UI with protection...")
print("=" * 60)

# We'll manually create the protected UI file and logic stub
# since the Figma code has UI and empty onClick handlers mixed together

# Create components directory
components_dir = workspace / "src/components"
components_dir.mkdir(parents=True, exist_ok=True)

# Create lib directory for logic
lib_dir = workspace / "src/lib"
lib_dir.mkdir(parents=True, exist_ok=True)

# Write protected UI file
ui_file = components_dir / "CalculatorUI.tsx"
ui_content = """// 🔒 UI-PROTECTED
// This file contains visual design from Figma
// DO NOT modify className, styles, animations, or layout
// Only data flow (props, handlers) can be changed

import { motion } from 'motion/react';

interface Button {
  label: string;
  type: 'number' | 'operator' | 'function';
  span: number;
}

interface CalculatorUIProps {
  display: string;
  onButtonClick: (button: Button) => void;
}

export function CalculatorUI({ display, onButtonClick }: CalculatorUIProps) {
  const buttons: Button[] = [
    { label: 'AC', type: 'function', span: 1 },
    { label: '±', type: 'function', span: 1 },
    { label: '%', type: 'function', span: 1 },
    { label: '÷', type: 'operator', span: 1 },

    { label: '7', type: 'number', span: 1 },
    { label: '8', type: 'number', span: 1 },
    { label: '9', type: 'number', span: 1 },
    { label: '×', type: 'operator', span: 1 },

    { label: '4', type: 'number', span: 1 },
    { label: '5', type: 'number', span: 1 },
    { label: '6', type: 'number', span: 1 },
    { label: '-', type: 'operator', span: 1 },

    { label: '1', type: 'number', span: 1 },
    { label: '2', type: 'number', span: 1 },
    { label: '3', type: 'number', span: 1 },
    { label: '+', type: 'operator', span: 1 },

    { label: '0', type: 'number', span: 2 },
    { label: '.', type: 'number', span: 1 },
    { label: '=', type: 'operator', span: 1 },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="w-full max-w-sm"
    >
      <div className="bg-gray-800/80 backdrop-blur-xl rounded-3xl p-6 shadow-2xl shadow-white/10 border border-white/30">
        {/* Display */}
        <div className="mb-6 px-4 py-8 text-right">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-white text-6xl tracking-tight overflow-hidden"
          >
            {display}
          </motion.div>
        </div>

        {/* Buttons Grid */}
        <div className="grid grid-cols-4 gap-3">
          {buttons.map((button, index) => (
            <motion.button
              key={index}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onButtonClick(button)}
              className={`
                h-20 rounded-2xl transition-all duration-200 flex items-center justify-center
                ${button.span === 2 ? 'col-span-2' : ''}
                ${
                  button.type === 'operator'
                    ? 'bg-gradient-to-br from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-500 text-white shadow-lg shadow-orange-500/50'
                    : button.type === 'function'
                    ? 'bg-gradient-to-br from-gray-400 to-gray-500 hover:from-gray-300 hover:to-gray-400 text-black shadow-lg shadow-gray-500/30'
                    : 'bg-gradient-to-br from-gray-700 to-gray-800 hover:from-gray-600 hover:to-gray-700 text-white shadow-lg shadow-gray-800/50'
                }
                relative overflow-hidden group
              `}
            >
              <span className="relative z-10 text-3xl">{button.label}</span>

              {/* Glow effect on hover */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div className="absolute inset-0 bg-white/20 rounded-2xl blur-xl" />
              </div>
            </motion.button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

export type { Button, CalculatorUIProps };
"""

ui_file.write_text(ui_content)
print(f"✅ Created protected UI file: {ui_file}")

# Mark as protected
orchestrator.protector.mark_as_protected(ui_file)

# Create logic stub
logic_file = lib_dir / "calculatorLogic.ts"
logic_content = """// ✅ MODIFIABLE: Agents can change business logic here
// This file contains the calculator engine - AI agents will implement this

export type Operator = '+' | '-' | '×' | '÷' | null;

export interface CalculatorState {
  display: string;
  previousValue: number | null;
  operator: Operator;
  waitingForOperand: boolean;
}

export class CalculatorEngine {
  private state: CalculatorState;

  constructor() {
    this.state = {
      display: '0',
      previousValue: null,
      operator: null,
      waitingForOperand: false
    };
  }

  // TODO: Implement calculator logic
  // Agents will add methods like:
  // - inputDigit(digit: string): void
  // - inputDecimal(): void
  // - performOperation(nextOperator: Operator): void
  // - clearAll(): void
  // - toggleSign(): void
  // - inputPercent(): void

  getState(): CalculatorState {
    return { ...this.state };
  }
}
"""

logic_file.write_text(logic_content)
print(f"📝 Created logic stub: {logic_file}")

# Create container component
container_file = components_dir / "Calculator.tsx"
container_content = """// Container component that connects UI to logic
import { useState, useRef } from 'react';
import { CalculatorUI, type Button } from './CalculatorUI';
import { CalculatorEngine } from '../lib/calculatorLogic';

export function Calculator() {
  const engine = useRef(new CalculatorEngine());
  const [display, setDisplay] = useState('0');

  const handleButtonClick = (button: Button) => {
    // TODO: Implement button handling logic
    // This will call methods on the CalculatorEngine
    // and update the display state
    console.log('Button clicked:', button.label);
  };

  return <CalculatorUI display={display} onButtonClick={handleButtonClick} />;
}
"""

container_file.write_text(container_content)
print(f"🔗 Created container component: {container_file}")

# Create package.json
package_file = workspace / "package.json"
package_content = """{
  "name": "calculator-app",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "motion": "^10.16.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.0.0"
  }
}
"""

package_file.write_text(package_content)
print(f"📦 Created package.json: {package_file}")

# Create README
readme_file = workspace / "README.md"
readme_content = """# Calculator App with UI Protection

This calculator uses Figma-designed UI that is protected from modification.

## File Structure

- `src/components/CalculatorUI.tsx` - 🔒 **PROTECTED** Figma-designed visual component
- `src/lib/calculatorLogic.ts` - ✅ **MODIFIABLE** Business logic (to be implemented)
- `src/components/Calculator.tsx` - Container component

## UI Protection

The `CalculatorUI.tsx` file is marked as UI-PROTECTED. Agents can:
- ✅ Change prop types and interfaces
- ✅ Update event handlers
- ❌ NOT change className, Tailwind classes, or Framer Motion props
- ❌ NOT modify layout, colors, or visual styling

All visual changes must be done in Figma and re-imported.

## Next Steps

Run AI Scrum Master to implement calculator logic:

```bash
cd ~/Development/repos/ai-scrum-master-v2
./run.sh --workspace ~/Development/repos/calculator-app-by-ai "Implement calculator logic..."
```
"""

readme_file.write_text(readme_content)
print(f"📖 Created README: {readme_file}")

print("\n" + "=" * 60)
print("✅ Figma UI Import Complete!")
print("=" * 60)
print(f"\n🔒 Protected file: {ui_file.relative_to(workspace)}")
print(f"✅ Modifiable files:")
print(f"   - {logic_file.relative_to(workspace)}")
print(f"   - {container_file.relative_to(workspace)}")
print(f"\n📊 Protection Status:")

status = orchestrator.get_protection_status()
for file_info in status['files']:
    print(f"   🔒 {Path(file_info['path']).name} - Hash: {file_info['hash'][:16]}...")

print(f"\n⚠️  Agents will NOT be able to modify visual styling in CalculatorUI.tsx")
print(f"✅ Agents CAN implement logic in calculatorLogic.ts")
