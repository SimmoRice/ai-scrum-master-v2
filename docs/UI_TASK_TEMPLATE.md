# UI Task Template

**Use this template when requesting UI/visual changes to get better results from AI Scrum Master.**

---

## Why This Template Matters

AI agents can't see your screen or read your mind. When you request UI changes without specific visual details, agents will guess - and often guess wrong, leading to:

❌ Broken layouts
❌ Wrong colors
❌ Misaligned elements
❌ Multiple revision cycles
❌ Wasted development costs

**Real Example of What Goes Wrong:**

```
Bad Request: "Add dark mode"

Result:
- Agent adds dark mode feature ✅
- But breaks button grid layout ❌
- Colors don't match design ❌
- User has to request 2-3 more fixes ❌
- Total cost: $5+ across multiple workflows
```

```
Good Request: "Add dark mode with these specific requirements..."

Result:
- Agent implements exactly as specified ✅
- Layout stays intact ✅
- Colors match perfectly ✅
- Approved on first try ✅
- Total cost: $1.90
```

---

## Template Structure

```markdown
[TITLE: Brief description of UI change]

## Visual Requirements

[Describe the desired visual appearance in detail]

## Layout & Positioning

[Specify where elements should appear]

## Colors & Styling

[Provide exact color codes and styling details]

## Interactive Behavior

[Describe hover states, transitions, animations]

## Responsive Design

[Specify mobile, tablet, desktop behavior]

## Reference Images

[Attach mockups, wireframes, or example screenshots]

## Acceptance Criteria

[List specific visual checks that define "done"]
```

---

## Complete Example: Dark Mode Toggle

```markdown
# Add Dark Mode Toggle to Calculator App

## Visual Requirements

Add a theme toggle button in the calculator header that switches between light and dark modes.

**Button Appearance:**
- Circular button, 36px diameter
- Position: Top-right corner of calculator header
- Sun icon (☀️) displayed when in light mode
- Moon icon (🌙) displayed when in dark mode
- Smooth icon rotation on hover (20deg)

## Layout & Positioning

```
┌─────────────────────────────┐
│ Calculator Header           │
│                       [☀️]  │ ← Toggle button here
├─────────────────────────────┤
│ Display Area                │
│                          0  │
├─────────────────────────────┤
│ Button Grid                 │
│  C    ÷    ×    ⌫          │
│  7    8    9    −          │
│  ...                        │
└─────────────────────────────┘
```

## Colors & Styling

**Light Mode:**
- Body background: `#f0f0f0`
- Calculator background: `#e8e8e8`
- Display background: `#ffffff`
- Number buttons: `#f5f5f5`
- Operator buttons: `#ff9f0a` (macOS orange)
- Clear button: `#a5a5a5`

**Dark Mode:**
- Body background: `#1c1c1e`
- Calculator background: `#2c2c2e`
- Display background: `#1c1c1e`
- Number buttons: `#505050`
- Operator buttons: `#ff9f0a` (same orange)
- Clear button: `#3a3a3c`

**Toggle Button:**
- Light mode background: `#ffffff`
- Dark mode background: `#3a3a3c`
- Box shadow: `0 2px 8px rgba(0,0,0,0.1)`

## Interactive Behavior

**Hover State:**
- Scale button to 105% (`transform: scale(1.05)`)
- Rotate icon 20deg (`transform: rotate(20deg)`)
- Slightly darker background color

**Click Action:**
- Scale down to 95% (`transform: scale(0.95)`)
- Switch theme immediately
- Swap sun/moon icon
- Save preference to localStorage

**Transitions:**
- All color changes: `0.3s ease`
- Transform animations: `0.3s ease`
- No jarring flashes or jumps

## Responsive Design

**Desktop (>= 768px):**
- Button: 36px diameter
- Icon: 1.2rem font size

**Mobile (< 768px):**
- Button: 32px diameter
- Icon: 1rem font size
- Ensure button doesn't overlap display

## Reference Images

**Visual Reference:** Match the macOS Calculator app aesthetic exactly

**Color Reference:** Use macOS system colors:
- macOS Calculator light gray: #D4D4D2
- macOS Calculator dark gray: #1C1C1C
- macOS orange: #FF9500

## Accessibility

- `aria-label="Toggle dark mode"` on button
- Keyboard accessible (Tab to focus, Enter to toggle)
- Sufficient color contrast in both modes (WCAG AA)
- Focus indicator visible: `3px solid #ff9f0a`

## Technical Requirements

- Persist theme choice in `localStorage` as `"theme"` key
- Apply theme on page load from localStorage
- Default to light mode if no preference stored
- Use CSS custom properties for theme colors
- Smooth transitions between themes

## Acceptance Criteria

Visual checks that MUST pass:

- [ ] Toggle button visible in top-right corner
- [ ] Sun icon shows in light mode
- [ ] Moon icon shows in dark mode
- [ ] Icon rotates smoothly on hover
- [ ] All colors match specification exactly
- [ ] No layout shifts when toggling theme
- [ ] Theme persists across page reloads
- [ ] Transitions are smooth (0.3s)
- [ ] Button is accessible via keyboard
- [ ] Works on mobile, tablet, desktop
- [ ] No broken elements in either theme
- [ ] Matches macOS Calculator aesthetic

---

**Priority:** High
**Estimated Complexity:** Medium
**Visual Verification Required:** YES - Screenshots mandatory
```

---

## More Examples

### Example 2: Responsive Navigation Bar

```markdown
# Create Responsive Navigation Bar

## Visual Requirements

Horizontal navigation bar at top of page with logo and menu items.

**Desktop Appearance:**
```
┌─────────────────────────────────────────┐
│ [Logo]  Home  About  Services  Contact │
└─────────────────────────────────────────┘
```

**Mobile Appearance:**
```
┌─────────────────┐
│ [Logo]    [☰]  │  ← Hamburger menu
└─────────────────┘

When menu open:
┌─────────────────┐
│ [Logo]    [×]  │
├─────────────────┤
│ Home            │
│ About           │
│ Services        │
│ Contact         │
└─────────────────┘
```

## Colors & Styling

- Background: `#2c3e50`
- Text color: `#ecf0f1`
- Hover background: `#34495e`
- Active link: `#3498db`
- Logo height: 40px

## Responsive Breakpoint

- Desktop: >= 768px (horizontal layout)
- Mobile: < 768px (hamburger menu)

## Animations

- Menu slide-in from right: `0.3s ease-out`
- Link hover: `background-color 0.2s ease`

## Acceptance Criteria

- [ ] Logo aligned left
- [ ] Menu items aligned right (desktop)
- [ ] Hamburger icon on mobile
- [ ] Menu slides in smoothly
- [ ] Links change color on hover
- [ ] Active link highlighted
```

### Example 3: Simple Button Style Change

```markdown
# Update Primary Button Styling

## Visual Requirements

Change all primary buttons to match new brand colors.

## Current vs New

**Current:**
- Background: Blue (#007bff)
- Text: White
- Border radius: 4px

**New:**
- Background: Brand purple (#6f42c1)
- Text: White
- Border radius: 8px (more rounded)
- Box shadow: `0 4px 6px rgba(111, 66, 193, 0.25)`

## Hover State

- Background: Darker purple (#5a32a3)
- Shadow: `0 6px 8px rgba(111, 66, 193, 0.35)`
- Transform: `translateY(-2px)` (slight lift)

## Transition

- All properties: `0.2s ease`

## Acceptance Criteria

- [ ] All primary buttons use new purple color
- [ ] Border radius is 8px
- [ ] Hover effect works correctly
- [ ] Shadow appears on all buttons
- [ ] No other button styles affected
```

---

## Quick Checklist

Before submitting a UI task, ask yourself:

- [ ] Did I specify exact colors (hex codes)?
- [ ] Did I describe the layout/positioning?
- [ ] Did I mention hover/active states?
- [ ] Did I include responsive behavior?
- [ ] Did I provide reference images or examples?
- [ ] Did I list specific acceptance criteria?
- [ ] Did I specify animations/transitions?

**If you answered NO to 3 or more questions, add more details!**

---

## What NOT to Do

### ❌ Too Vague

```
"Make the buttons look better"
"Add some colors"
"Make it responsive"
"Improve the layout"
```

**Problem:** Agents will guess what "better" means and likely get it wrong.

### ❌ No Colors Specified

```
"Add dark mode"
```

**Problem:** Agent will choose random dark colors that don't match your design.

### ❌ No Layout Details

```
"Add a header"
```

**Problem:** Agent doesn't know where to put it or what it should contain.

### ❌ Missing Acceptance Criteria

```
"Fix the button grid"
```

**Problem:** Agent doesn't know what "fixed" looks like and may claim success incorrectly.

---

## When to Use This Template

**Always use for:**
- Layout changes (grid, flex, positioning)
- Color scheme updates (themes, palettes)
- New UI components (buttons, forms, cards)
- Responsive design changes
- Animation/transition additions

**Optional for:**
- Simple text content changes (no visual change)
- Bug fixes that don't affect appearance
- Backend/API changes (no UI)

---

## Tips for Success

1. **Screenshot Everything**
   - Take screenshots of current state
   - Create mockups of desired state
   - Attach both to your user story

2. **Use Color Pickers**
   - Don't guess color codes
   - Use macOS Color Picker or online tools
   - Provide exact hex/RGB values

3. **Test Your Requirements**
   - Read your user story aloud
   - Could someone implement it without asking questions?
   - If not, add more details

4. **Reference Real Examples**
   - "Match the GitHub dark mode"
   - "Similar to macOS Calculator"
   - "Use Material Design button style"

5. **Be Specific About Spacing**
   - "16px padding" not "some padding"
   - "24px margin-bottom" not "space between elements"
   - "8px gap" not "small gap"

---

## Template Files

Copy these templates for different UI tasks:

### [Button Component Template](button_template.md)
### [Layout Change Template](layout_template.md)
### [Theme/Color Template](theme_template.md)
### [Responsive Design Template](responsive_template.md)
### [Animation Template](animation_template.md)

---

## Getting Help

If you're not sure how to describe a visual requirement:

1. **Take screenshots** - A picture is worth 1000 words
2. **Find similar examples** - Link to websites with similar UI
3. **Use design tools** - Figma, Sketch, or even PowerPoint
4. **Ask for feedback** - Share your user story in #design channel

---

**Remember:** The more specific you are, the better the results. Spending 5 minutes writing a detailed UI story saves hours of back-and-forth revisions.

**Next:** See [RELEASE_NOTES_v2.3.md](../RELEASE_NOTES_v2.3.md) for the visual testing system that helps catch UI issues automatically.
