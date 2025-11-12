# UI Designer Agent - Design Proposal (v2.5)

## The Problem

Current Architect agent is **blind** when creating UI:
- No visual design tools
- Can't see what it's building
- Relies on guessing from text descriptions
- Produces functional but basic UI
- No design iteration workflow

## The Solution: Dedicated UI Designer Agent

A specialized agent that focuses ONLY on visual design, with access to:
- Visual design tool integration (Figma, Sketch, etc.)
- Screenshot upload/reference
- Design system libraries
- Modern UI frameworks
- Interactive refinement

## Agent Role Definition

```python
# agents/ui_designer.py

AGENT_ROLES = {
    # ... existing agents ...

    "ui_designer": {
        "name": "UIDesigner",
        "description": "Specializes in creating beautiful, modern UI designs",
        "responsibilities": [
            "Visual design and layout",
            "Color schemes and styling",
            "Responsive design",
            "Animations and transitions",
            "Design system consistency",
        ],
        "tools": [
            "Figma API integration",
            "Screenshot reference upload",
            "Design token generation",
            "Component library access",
            "Visual regression testing"
        ],
        "frameworks": [
            "React + Tailwind CSS",
            "Framer Motion animations",
            "Radix UI primitives",
            "shadcn/ui components"
        ]
    }
}
```

## Workflow Integration

### Option 1: UI Designer Replaces Architect (for UI tasks)

```
User Story: "Build calculator app with macOS look"
       ↓
System detects UI task
       ↓
┌──────────────────────────┐
│ UI Designer Agent        │  ← NEW! Replaces Architect for UI
│ (Visual design focus)    │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Security Agent           │
│ (Review generated code)  │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Tester Agent             │
│ (Write tests)            │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Product Owner            │
│ (Visual approval)        │
└──────────────────────────┘
```

### Option 2: UI Designer + Architect (Collaboration)

```
User Story: "Add dark mode to existing calculator"
       ↓
┌──────────────────────────┐
│ UI Designer Agent        │  ← Creates visual design
│ Generates mockup + specs │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Architect Agent          │  ← Implements backend logic
│ Uses UI specs from above │
└──────────┬───────────────┘
           │
           ▼
Security → Tester → Product Owner
```

## UI Designer Agent Capabilities

### 1. Design Tool Integration

#### Figma Integration

```python
class UIDesigner:
    """UI Designer agent with Figma integration"""

    def __init__(self):
        self.figma_api = FigmaAPI()
        self.design_system = DesignSystemLibrary()

    def create_design_from_description(
        self,
        user_story: str,
        reference_images: List[Path] = None
    ) -> Dict:
        """
        Create UI design using Figma API

        Process:
        1. Analyze user story for UI requirements
        2. Generate design prompt for Figma AI
        3. Create initial design
        4. Export design specs + code
        5. Return for user review
        """

        # Extract UI requirements
        ui_requirements = self.parse_ui_requirements(user_story)

        # Generate Figma design
        design_prompt = self.create_design_prompt(
            requirements=ui_requirements,
            reference_images=reference_images
        )

        # Use Figma AI to generate design
        figma_design = self.figma_api.generate_design(design_prompt)

        # Export code
        code = self.figma_api.export_code(
            design_id=figma_design.id,
            framework="react",  # or "vue", "html", etc.
            style_system="tailwind"
        )

        # Export screenshots
        screenshots = self.figma_api.export_screenshots(
            design_id=figma_design.id,
            formats=["desktop", "tablet", "mobile"]
        )

        return {
            "design_url": figma_design.url,
            "code": code,
            "screenshots": screenshots,
            "design_tokens": figma_design.tokens
        }
```

#### Screenshot Reference Upload

```python
def use_reference_images(self, reference_paths: List[Path]) -> str:
    """
    Analyze reference images and extract design patterns

    User can provide:
    - Screenshots of desired look
    - Mockups from design tools
    - Examples from other apps
    """

    design_analysis = []

    for ref_path in reference_paths:
        # Use Claude's vision capabilities to analyze
        analysis = claude.analyze_image(
            image_path=ref_path,
            prompt="""
            Analyze this UI design and extract:
            1. Color palette (exact hex codes)
            2. Layout structure (grid, flex, etc.)
            3. Typography (fonts, sizes, weights)
            4. Spacing and padding patterns
            5. Border radius and shadows
            6. Button styles and states
            7. Overall aesthetic (modern, minimal, glassmorphic, etc.)
            """
        )

        design_analysis.append(analysis)

    # Synthesize into design specifications
    design_specs = self.synthesize_design_specs(design_analysis)

    return design_specs
```

### 2. User Interaction Workflow

```
$ ./run.sh --workspace ~/calculator "Build calculator with macOS look"

🎨 UI task detected - using UI Designer agent

============================================================
🎨 UI Designer Agent Starting
============================================================

📋 Analyzing UI requirements from user story...
✅ Detected requirements:
   - Calculator functionality
   - macOS aesthetic
   - Modern, polished look

Do you have reference images? (y/n): y

📁 Please provide reference image paths (one per line, Ctrl+D when done):
> ~/Desktop/macos-calculator-screenshot.png
> ~/Downloads/cool-calculator-mockup.png
^D

✅ Reference images uploaded

🎨 Analyzing reference images...
✅ Design analysis complete:
   - Color palette: #1C1C1E, #D4D4D2, #FF9500
   - Layout: 4-column grid
   - Typography: SF Pro Display
   - Style: Glassmorphic, gradients, shadows

Would you like to use Figma for design generation? (y/n): y

🎨 Generating Figma design...
✅ Design created: https://figma.com/file/abc123

📸 Exporting screenshots...
✅ Screenshots: desktop, tablet, mobile

💻 Exporting production code...
✅ Code generated: React + Tailwind + Framer Motion

============================================================
🎨 VISUAL CHECKPOINT: UI Designer
============================================================

📸 Screenshots saved to: logs/screenshots/...

Review options:
  1) View Figma design (opens browser)
  2) View screenshots
  3) View generated code
  4) Approve design
  5) Request design revision

Your choice (1-5): 1

✅ Opening Figma design in browser...

[User reviews design in Figma]

Your choice (1-5): 5

What would you like changed?
> Center the text in each button
> Make the zero button span 2 columns
^D

✅ Updating Figma design with feedback...
✅ Design updated: https://figma.com/file/abc123?v=2

[Shows new screenshots]

Your choice (1-5): 4

✅ Design approved! Exporting final code...

Writing code to workspace:
  - src/components/Calculator.tsx
  - src/styles/calculator.css
  - src/lib/calculator-logic.ts

============================================================
🔒 Security Agent Starting
============================================================
...
```

### 3. Design System Integration

```python
class DesignSystemLibrary:
    """
    Pre-built design systems and component libraries

    Reduces iteration time by using proven patterns
    """

    SYSTEMS = {
        "shadcn": {
            "framework": "react",
            "styling": "tailwind",
            "components": "radix-ui",
            "features": ["dark-mode", "accessible", "customizable"]
        },
        "chakra": {
            "framework": "react",
            "styling": "emotion",
            "features": ["dark-mode", "accessible", "themed"]
        },
        "material": {
            "framework": "react",
            "styling": "mui",
            "features": ["material-design", "themed"]
        },
        "daisyui": {
            "framework": "any",
            "styling": "tailwind",
            "features": ["pre-styled", "themed", "minimal"]
        }
    }

    def suggest_design_system(self, requirements: Dict) -> str:
        """
        Suggest appropriate design system based on requirements

        Example:
        - "Modern, accessible" → shadcn/ui
        - "Material Design" → MUI
        - "Quick prototype" → DaisyUI
        """
        pass
```

### 4. Framework Selection

```python
# UI Designer can choose best framework for the task

FRAMEWORK_PROFILES = {
    "simple_static": {
        "html": "Vanilla HTML/CSS/JS",
        "best_for": "Simple, no-build sites",
        "example": "Calculator, landing page"
    },

    "modern_spa": {
        "react": "React + Vite + Tailwind",
        "best_for": "Interactive web apps",
        "example": "Dashboard, admin panel"
    },

    "animated": {
        "react_motion": "React + Framer Motion + Tailwind",
        "best_for": "Polished, animated UIs",
        "example": "Your calculator example"
    },

    "full_stack": {
        "next": "Next.js + Tailwind + shadcn",
        "best_for": "Production web apps",
        "example": "SaaS product, e-commerce"
    }
}
```

## Agent Prompt Design

```markdown
# UI Designer Agent Prompt

You are the UI Designer agent in the AI Scrum Master workflow.

## Your Role

You specialize in creating beautiful, modern user interfaces. Unlike the Architect
agent (who focuses on functionality), you focus on VISUAL DESIGN.

## Capabilities

1. **Figma Integration**
   - Generate designs using Figma AI
   - Export production-ready code
   - Create responsive mockups

2. **Visual Analysis**
   - Analyze reference screenshots
   - Extract color palettes
   - Identify design patterns

3. **Modern Frameworks**
   - React + Tailwind CSS
   - Framer Motion animations
   - shadcn/ui components
   - Radix UI primitives

4. **Design Systems**
   - Apply consistent design patterns
   - Use proven component libraries
   - Follow accessibility guidelines

## Your Workflow

1. **Analyze Requirements**
   - Read user story for UI needs
   - Review any reference images
   - Identify design patterns to use

2. **Create Design**
   - Use Figma to generate visual design
   - OR code directly if simple
   - Export screenshots for review

3. **Get Feedback**
   - Show design to user
   - Iterate based on feedback
   - Refine until approved

4. **Export Code**
   - Generate production-ready code
   - Use modern best practices
   - Include animations and polish

## Code Quality Standards

Your code must be:
- ✅ TypeScript (type-safe)
- ✅ Accessible (ARIA labels, semantic HTML)
- ✅ Responsive (mobile, tablet, desktop)
- ✅ Animated (smooth transitions)
- ✅ Performant (optimized rendering)
- ✅ Maintainable (clean, documented)

## Example Output

```typescript
// Calculator.tsx - Professional quality

import { useState } from 'react';
import { motion } from 'framer-motion';

type Operator = '+' | '-' | '×' | '÷' | null;

export function Calculator() {
  // State management
  const [display, setDisplay] = useState('0');

  // ... (full implementation)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full max-w-sm"
    >
      {/* Beautiful, animated UI */}
    </motion.div>
  );
}
```

## When to Use You

Use UI Designer instead of Architect when:
- User story is primarily UI/visual
- Design quality is critical
- Modern, polished look required
- Animations/transitions needed

## Visual Verification

ALWAYS:
- ✅ Generate screenshots of your design
- ✅ Show them to user for approval
- ✅ Iterate based on feedback
- ✅ Never claim "looks good" without proof
```

## Configuration

```python
# config.py

AGENT_ROLES = {
    # ... existing agents ...

    "ui_designer": {
        "enabled": True,
        "use_for_ui_tasks": True,  # Auto-use for UI-focused stories
        "figma_integration": True,
        "default_framework": "react-tailwind",
        "require_visual_approval": True,
        "max_design_iterations": 5
    }
}

UI_DESIGNER_CONFIG = {
    "figma_api_key": os.getenv("FIGMA_API_KEY"),
    "default_design_system": "shadcn",

    "frameworks": {
        "react": {
            "bundler": "vite",
            "styling": "tailwind",
            "animation": "framer-motion"
        },
        "vanilla": {
            "no_build": True,
            "styling": "css",
            "animation": "css-transitions"
        }
    },

    "visual_approval": {
        "required": True,
        "show_figma_design": True,
        "show_screenshots": True,
        "show_code_preview": True
    }
}
```

## Benefits Over Current Architect

| Feature | Architect Agent | UI Designer Agent |
|---------|----------------|-------------------|
| **Visual Design** | Blind coding | Figma integration |
| **Reference Images** | Text description only | Can analyze screenshots |
| **Iteration** | Re-code from scratch | Refine in Figma |
| **Code Quality** | Functional | Professional + polished |
| **Animations** | Basic or none | Framer Motion |
| **Styling** | Inline or basic CSS | Tailwind + design tokens |
| **Responsiveness** | Media queries | Mobile-first design |
| **User Approval** | After complete | During design phase |

## Migration Path

### Phase 1: Add UI Designer Agent (v2.5)
- [ ] Create UIDesigner agent class
- [ ] Add Figma API integration
- [ ] Add reference image upload
- [ ] Integrate into orchestrator workflow
- [ ] Add visual checkpoint system

**Estimated Time:** 8-12 hours

### Phase 2: Design System Library (v2.5.1)
- [ ] Add shadcn/ui integration
- [ ] Add component library catalog
- [ ] Add design token generation
- [ ] Template system for common patterns

**Estimated Time:** 6-8 hours

### Phase 3: Advanced Features (v2.6)
- [ ] Multi-framework support (Vue, Svelte, etc.)
- [ ] AI design generation without Figma
- [ ] Design-to-code diffing
- [ ] Component extraction from screenshots

**Estimated Time:** 12-16 hours

## Your Example Workflow

```bash
# What you did manually with Figma:
1. Describe: "macOS calculator but cooler"
2. Figma generates design
3. Review and iterate: "center text in buttons"
4. Export code

# What UI Designer agent would do:
$ ./run.sh --workspace ~/calc "Build calculator with macOS look but cooler"

🎨 UI Designer agent starting...
📋 Creating Figma design from description...
✅ Design created: https://figma.com/file/...

[Shows you the design]

Your feedback: "Center text in buttons"

🎨 Updating design...
✅ Design updated

[Shows you updated design]

Approve? (y/n): y

💻 Exporting React + Tailwind code...
✅ Code written to: src/Calculator.tsx

[Continues to Security/Tester/PO agents]
```

## Summary

You've discovered the **right way to do UI design**:

**Current Problem:**
- Architect agent codes blindly
- No visual design tools
- No iteration workflow
- Basic, functional output

**Your Solution:**
- Use Figma for visual design
- Interactive refinement
- Export polished code
- Professional results

**Proposed Integration:**
- New UI Designer agent
- Figma API integration
- Reference image upload
- Visual approval workflow
- Modern frameworks (React + Tailwind + Framer Motion)

This would give AI Scrum Master the same quality you got from Figma, but integrated into the workflow.

**Recommendation:** Implement UI Designer agent in v2.5 after visual testing (v2.3) and human approval (v2.4).
