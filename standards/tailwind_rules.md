# Tailwind CSS Usage Rules

These rules govern how Tailwind CSS must be used across all frontend components. The code review agent enforces all rules listed here against every staged diff that touches `.html`, `.jsx`, `.tsx`, `.vue`, or `.svelte` files.

---

## 1. Utility-First Approach

### Rule 1.1 — Use Utility Classes Instead of Custom CSS

All styling must be applied via Tailwind utility classes. Writing custom CSS (in `.css`, `.scss`, or `<style>` blocks) is only permitted when a required style cannot be expressed with Tailwind utilities.

**Violation example:**
```css
/* custom.css */
.card {
  padding: 16px;
  border-radius: 8px;
  background-color: #ffffff;
}
```

**Compliant example:**
```html
<div class="p-4 rounded-lg bg-white">
```

### Rule 1.2 — No Inline `style` Attributes for Values Covered by Tailwind

Inline `style` attributes must not be used for properties that have a direct Tailwind equivalent (spacing, color, typography, borders, shadows, etc.).

**Violation example:**
```html
<p style="font-size: 14px; color: #6b7280;">
```

**Compliant example:**
```html
<p class="text-sm text-gray-500">
```

### Rule 1.3 — Avoid `@apply` Except for Reusable Component Abstractions

`@apply` may only be used inside a dedicated component stylesheet when the same combination of utilities is repeated across three or more unrelated locations. It must not be used as a shortcut to avoid writing utility classes inline.

---

## 2. Responsive Design

### Rule 2.1 — Mobile-First Breakpoints

All responsive styles must be written mobile-first. Base classes apply to the smallest viewport; larger breakpoints are added with prefixes.

Breakpoint order: `(base)` → `sm:` → `md:` → `lg:` → `xl:` → `2xl:`

**Violation example (desktop-first):**
```html
<div class="grid-cols-3 sm:grid-cols-1">
```

**Compliant example (mobile-first):**
```html
<div class="grid-cols-1 md:grid-cols-3">
```

### Rule 2.2 — No Magic Numbers for Breakpoints

Custom breakpoint values (e.g., `min-width: 900px`) must not be added inline. Use the project's configured Tailwind breakpoints only. If a new breakpoint is needed, it must be added to `tailwind.config.js`.

### Rule 2.3 — All Layouts Must Be Responsive

Every layout component must include responsive variants for at least `md` and `lg` breakpoints. A component that only specifies base classes and has no responsive variants requires explicit justification in a comment.

---

## 3. Color Palette

### Rule 3.1 — Use Design-System Colors Only

Colors must be referenced from the project's Tailwind color palette (defined in `tailwind.config.js` under `theme.colors` or `theme.extend.colors`). Arbitrary color values using the bracket syntax (e.g., `text-[#ff0000]`) are forbidden unless the color is a one-off dynamic value passed from a data source.

**Violation example:**
```html
<button class="bg-[#1a73e8] text-[#ffffff]">
```

**Compliant example:**
```html
<button class="bg-primary-600 text-white">
```

### Rule 3.2 — Semantic Color Tokens for UI States

UI state colors must use semantic tokens, not raw palette values:

| State | Required token |
|---|---|
| Primary action | `bg-primary-*` |
| Destructive / error | `bg-red-*` or `bg-danger-*` |
| Success | `bg-green-*` or `bg-success-*` |
| Warning | `bg-yellow-*` or `bg-warning-*` |
| Disabled | `bg-gray-300 text-gray-400` |

### Rule 3.3 — Dark Mode via `dark:` Prefix

Dark mode styles must use Tailwind's `dark:` variant. Separate dark-mode stylesheets or JavaScript-toggled class swaps are not permitted.

**Compliant example:**
```html
<div class="bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
```

---

## 4. Typography

### Rule 4.1 — Use Tailwind Typography Scale

Font sizes must use Tailwind's type scale (`text-xs`, `text-sm`, `text-base`, `text-lg`, `text-xl`, `text-2xl`, etc.). Arbitrary sizes (e.g., `text-[13px]`) are forbidden.

### Rule 4.2 — Line Height and Letter Spacing via Utilities

`leading-*` and `tracking-*` utilities must be used instead of custom `line-height` or `letter-spacing` CSS values.

### Rule 4.3 — Prose Content Uses `@tailwindcss/typography`

Long-form text content (articles, documentation, markdown renders) must be wrapped in a `prose` class from the `@tailwindcss/typography` plugin rather than individually styled.

---

## 5. Spacing and Sizing

### Rule 5.1 — Use the Spacing Scale

All margin, padding, gap, and size values must use Tailwind's spacing scale (`p-1`, `m-4`, `gap-6`, etc.). Arbitrary values (e.g., `p-[18px]`) are forbidden unless the value is dynamic.

### Rule 5.2 — Consistent Component Padding

Interactive components (buttons, inputs, cards) must use consistent internal padding:

| Component | Minimum padding |
|---|---|
| Button | `px-4 py-2` |
| Input | `px-3 py-2` |
| Card | `p-4` or `p-6` |

### Rule 5.3 — No Negative Margins for Layout

Negative margin utilities (`-m-*`, `-mt-*`, etc.) must not be used to fix layout issues. Use flexbox or grid utilities instead.

---

## 6. Flexbox and Grid

### Rule 6.1 — Prefer Flexbox and Grid Over Absolute Positioning

Layout must be achieved with `flex` or `grid` utilities. `absolute` and `fixed` positioning is reserved for overlays, tooltips, and elements that genuinely need to escape document flow.

### Rule 6.2 — Explicit Flex Direction

When using `flex`, always specify `flex-row` or `flex-col` explicitly. Do not rely on the default `flex-row` being implied.

### Rule 6.3 — Grid Column Counts Must Be Responsive

Any `grid-cols-*` class must have at least one responsive variant (e.g., `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`).

---

## 7. Interactivity and State Variants

### Rule 7.1 — Use State Variants for Interactive Styles

Hover, focus, active, and disabled styles must use Tailwind's state variants (`hover:`, `focus:`, `active:`, `disabled:`). JavaScript-toggled class strings for these states are not permitted.

**Compliant example:**
```html
<button class="bg-primary-600 hover:bg-primary-700 focus:ring-2 focus:ring-primary-400 disabled:opacity-50">
```

### Rule 7.2 — Focus Styles Must Be Visible

Every interactive element (`button`, `a`, `input`, `select`, `textarea`) must have a visible focus style. Removing the default focus ring (`focus:outline-none`) without replacing it with a custom ring (`focus:ring-*`) is a violation.

---

## 8. Class Ordering

### Rule 8.1 — Follow Prettier Tailwind Plugin Order

Class names must be sorted in the order enforced by `prettier-plugin-tailwindcss`. The canonical order is:

1. Layout (`display`, `position`, `overflow`)
2. Flexbox / Grid
3. Spacing (`margin`, `padding`)
4. Sizing (`width`, `height`)
5. Typography
6. Backgrounds and borders
7. Effects (shadows, opacity, transforms)
8. State variants (`hover:`, `focus:`, etc.)
9. Responsive variants (`sm:`, `md:`, etc.)

Unsorted class lists are a violation and must be corrected before commit.

---

## 9. Avoiding Anti-Patterns

### Rule 9.1 — No Duplicate Utility Classes

The same utility class must not appear more than once on a single element.

### Rule 9.2 — No Conflicting Utilities

Conflicting utilities (e.g., `text-left text-center`, `p-4 px-2`) must not appear on the same element. The last class wins in CSS, but the intent is ambiguous and the redundant class must be removed.

### Rule 9.3 — Conditional Classes via `clsx` or `classnames`

Dynamic class construction must use `clsx` or `classnames` helpers. String concatenation or template literals for class names are forbidden.

**Violation example:**
```jsx
<div className={"p-4 " + (isActive ? "bg-primary-600" : "bg-gray-200")}>
```

**Compliant example:**
```jsx
<div className={clsx("p-4", isActive ? "bg-primary-600" : "bg-gray-200")}>
```
