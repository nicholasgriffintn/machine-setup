---
name: frontend-design
description: >-
  Implement responsive layouts, style components with CSS custom properties, build
  interactive forms, and structure semantic HTML for production-grade frontend interfaces.
  Use when building web components, landing pages, dashboards, UI layouts, or web applications.
  Trigger on: "build a page", "design a component", "create a UI", "frontend",
  "landing page", "web interface", "dashboard layout", "styled component", "hero section".
  Not for backend APIs, data fetching logic, or framework-specific state management.
allowed-tools: "Read, Grep, Glob, Bash, Write, Edit"
---

# Frontend Design Skill

Build frontend interfaces that reject generic aesthetics. Output complete, runnable code with intentional typography, color, layout, and motion.

## Step 1 -- Gather Context

Collect before writing any code:

1. **Purpose** -- Problem being solved and target user.
2. **Aesthetic direction** -- Commit to one: brutalist, editorial, retro-futuristic, luxury, playful, or utilitarian. If unspecified, propose one with rationale.
3. **Constraints** -- Framework, browser support, WCAG level, brand rules.
4. **Differentiator** -- The single visual idea that makes this memorable.

## Step 2 -- Define Design Tokens

Set up tokens before component code. Starter template:

```css
:root {
  /* Typography */
  --font-display: 'Space Grotesk', sans-serif;
  --font-body: 'IBM Plex Sans', sans-serif;

  /* Color */
  --color-primary: #1a1a2e;
  --color-accent: #e94560;
  --color-surface: #f5f5f0;
  --color-text: #16213e;

  /* Spacing (4px base) */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 2rem;
  --space-xl: 4rem;

  /* Motion */
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}
```

Replace values to match the chosen aesthetic. Every color, font, and spacing value must reference tokens.

## Step 3 -- Build

Implementation rules:

- **Layout** -- Break the grid intentionally. Use asymmetry, overlap, or unexpected composition. Never default to centered cards on white.
- **Motion** -- Two to three high-impact moments: page-load entrance, staggered reveals, hover micro-interactions. Prefer CSS `@keyframes` and `transition` over JS.
- **Backgrounds** -- Add depth with gradients, textures, or geometric shapes.
- **Responsiveness** -- Mobile-first. Verify at 375px, 768px, 1280px.
- **Accessibility** -- WCAG AA contrast ratios. Keyboard-navigable interactive elements. Semantic HTML throughout.

## Step 4 -- Deliver

Every response includes:

1. Complete, runnable code -- no pseudocode or placeholders.
2. One to two sentences on aesthetic direction and key decisions.
3. Font CDN links or asset references required to render.

## Checklist

Verify before finalizing:

- [ ] Aesthetic direction declared and consistently applied
- [ ] All visual values use CSS custom properties
- [ ] Layout avoids generic patterns (centered cards, purple gradients)
- [ ] Two or more CSS motion moments implemented
- [ ] Responsive across 375px, 768px, 1280px breakpoints
- [ ] WCAG AA met
- [ ] Decisions briefly explained
