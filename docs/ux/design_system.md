# Design System / Visual Language

## 1. UI Library / Component Approach
- The UI is built with Next.js + React + Tailwind CSS.
- Components are custom and styled with utility classes (navigation, chat panel, profile, forms, modal).
- Notifications use react-hot-toast.
- Headless UI and Heroicons are listed in dependencies, but no active usage is visible in the current UI.
- No full design system library (MUI, shadcn/ui, Bootstrap) is in use.

## 2. Color Palette
Colors are inferred from Tailwind classes:
- Primary: Indigo 600 (#4F46E5) for main CTAs and links.
- Secondary text: Slate 700 (#334155).
- Accent: Emerald 700 (#047857) for the tutor badge.
- Error: Rose 600 (#E11D48).
- Surface: White (#FFFFFF), Slate 50 (#F8FAFC).
- Borders: Slate 200 (#E2E8F0).
- Text: Slate 900 (#0F172A) primary, Slate 600 (#475569) secondary, Slate 500 (#64748B) muted.

## 3. Typography
- Default Tailwind sans-serif stack (no custom font configured).
- Common sizes: text-xs, text-sm, text-lg, text-xl.
- Common weights: font-semibold for headers, labels, and buttons.

## 4. Layout and Spacing
- Spacing follows Tailwind 4px increments.
- Main container: max-w-5xl centered.
- Auth pages: max-w-md centered card layout.
- Home layout: single column on mobile, two columns on large screens.
- Modal: fixed overlay with centered max-w-md panel.

## 5. Iconography
- The UI relies primarily on text labels and native form elements.
- No consistent icon set is used in the current screens.

## 6. Dark Mode
- Dark mode is not implemented.

## 7. Responsive Breakpoints
- Tailwind defaults: sm 640px, md 768px, lg 1024px, xl 1280px, 2xl 1536px.
- Main layout switches at lg to show sidebar + main panel.

## 8. Source of Truth
- The frontend code is the primary design source.
- Screenshots, if added, should live under docs/ux/screenshots.
