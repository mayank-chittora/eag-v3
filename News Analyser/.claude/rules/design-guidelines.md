# News Analyser — Design Guidelines

## 1. Brand Identity

### Platform Tone
The News Analyser serves two audiences: students preparing for competitive exams and investors/traders
making financial decisions. The tone must be:
- **Motivating**: Use active language, progress indicators, and encouraging micro-copy (e.g., "You've read
  42 articles this week — keep going!").
- **Subtle**: Avoid aggressive colours, heavy gradients, or sensationalist framing. News content
  speaks for itself; the UI should stay calm and professional.
- **Trustworthy**: Clean layout, consistent hierarchy, no dark patterns.

---

## 2. Colour Palette

### Primary Colours
| Token                      | Hex       | Usage                                              |
|----------------------------|-----------|----------------------------------------------------|
| `--color-primary`          | `#1A56DB` | Primary CTAs, active nav links, focus rings        |
| `--color-primary-dark`     | `#1140A8` | Primary button hover, active state                 |
| `--color-primary-light`    | `#EBF1FF` | Primary button ghost bg, selected filter chips     |

### Secondary Colours
| Token                       | Hex       | Usage                                           |
|-----------------------------|-----------|-------------------------------------------------|
| `--color-secondary`         | `#0E9F6E` | Secondary actions, success states               |
| `--color-secondary-dark`    | `#057A55` | Secondary button hover                          |
| `--color-secondary-light`   | `#DEF7EC` | Secondary badge background                      |

### Neutral / Surface Colours
| Token                     | Hex       | Usage                                          |
|---------------------------|-----------|------------------------------------------------|
| `--color-surface`         | `#FFFFFF` | Card backgrounds, modal backgrounds            |
| `--color-bg`              | `#F3F4F6` | Page background                                |
| `--color-bg-dark`         | `#111827` | Dark mode page background                      |
| `--color-border`          | `#E5E7EB` | Dividers, card borders                         |
| `--color-border-dark`     | `#374151` | Dark mode borders                              |
| `--color-text-primary`    | `#111827` | Body text, headings                            |
| `--color-text-secondary`  | `#6B7280` | Meta info, labels, timestamps                  |
| `--color-text-muted`      | `#9CA3AF` | Disabled text, placeholder                     |
| `--color-text-on-primary` | `#FFFFFF` | Text on primary colour backgrounds             |

### Sentiment Colours
These colours carry meaning. **Never repurpose them for non-sentiment UI.**

| Token                           | Hex       | Usage                                      |
|---------------------------------|-----------|--------------------------------------------|
| `--color-sentiment-positive`    | `#0E9F6E` | Positive news badge fill                   |
| `--color-sentiment-positive-bg` | `#DEF7EC` | Positive badge background                  |
| `--color-sentiment-negative`    | `#E02424` | Negative news badge fill                   |
| `--color-sentiment-negative-bg` | `#FDE8E8` | Negative badge background                  |
| `--color-sentiment-neutral`     | `#6B7280` | Neutral news badge fill                    |
| `--color-sentiment-neutral-bg`  | `#F3F4F6` | Neutral badge background                   |

### Category Accent Colours
One accent per category. Used on category filter chips and category page headers.

| Category             | Accent Hex  | Light BG Hex |
|----------------------|-------------|--------------|
| Share Market         | `#F59E0B`   | `#FFFBEB`    |
| Agriculture Sector   | `#16A34A`   | `#DCFCE7`    |
| Manufacturing Sector | `#D97706`   | `#FEF3C7`    |
| IT Sector            | `#6366F1`   | `#EEF2FF`    |
| Healthcare Sector    | `#EC4899`   | `#FDF2F8`    |
| Hospitality Sector   | `#F97316`   | `#FFF7ED`    |
| Education Sector     | `#D97706`   | `#FFFBEB`    |
| Indian Politics      | `#DC2626`   | `#FEF2F2`    |
| Global Politics      | `#0E7490`   | `#ECFEFF`    |
| Entertainment        | `#A855F7`   | `#F5F3FF`    |
| Fashion              | `#EC4899`   | `#FDF2F8`    |
| Sports               | `#EA580C`   | `#FFF7ED`    |
| Environment          | `#059669`   | `#ECFDF5`    |
| Economics            | `#0284C7`   | `#E0F2FE`    |

### Danger / Warning / Info
| Token               | Hex       | Usage                          |
|---------------------|-----------|--------------------------------|
| `--color-danger`    | `#E02424` | Destructive actions, errors    |
| `--color-danger-bg` | `#FDE8E8` | Error alert background         |
| `--color-warning`   | `#D97706` | Warnings, loading delays       |
| `--color-warning-bg`| `#FFFBEB` | Warning alert background       |
| `--color-info`      | `#1A56DB` | Informational alerts           |
| `--color-info-bg`   | `#EBF1FF` | Info alert background          |

---

## 3. Typography

### Font Families
- **Body / UI**: `Inter` (Google Fonts) — used for all UI text, labels, navigation, buttons, metadata
- **Article Titles**: `Merriweather` (Google Fonts) — used only for news article headlines to signal editorial credibility

```css
/* Load in index.html or globals.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Merriweather:wght@400;700&display=swap');
```

### Type Scale (Tailwind classes)
| Scale       | Class         | Size   | Weight   | Line Height | Use                              |
|-------------|---------------|--------|----------|-------------|----------------------------------|
| Display     | `text-5xl`    | 48px   | 700      | 1.1         | Hero headings only               |
| H1          | `text-4xl`    | 36px   | 700      | 1.2         | Page titles                      |
| H2          | `text-3xl`    | 30px   | 600      | 1.25        | Section headings                 |
| H3          | `text-2xl`    | 24px   | 600      | 1.3         | Card titles, article headlines   |
| H4          | `text-xl`     | 20px   | 600      | 1.4         | Sub-section headings             |
| H5          | `text-lg`     | 18px   | 500      | 1.5         | Labels, filter section headings  |
| Body        | `text-base`   | 16px   | 400      | 1.6         | Default body text                |
| Body Small  | `text-sm`     | 14px   | 400      | 1.5         | Metadata, source names, dates    |
| Caption     | `text-xs`     | 12px   | 400      | 1.4         | Timestamps, helper text          |

### Rules
- Article headlines use `font-merriweather`. All other text uses `font-inter` (set as Tailwind default).
- Body text maximum line length: 72 characters (`max-w-prose`).
- Never use font weight below 400 or above 700.
- Truncate long article titles with `line-clamp-2` in card view.

---

## 4. Spacing Scale

Use the Tailwind default spacing scale. Key values:
| Token  | px   | Common use                              |
|--------|------|-----------------------------------------|
| `p-1`  | 4px  | Tight internal padding (badge, chip)    |
| `p-2`  | 8px  | Icon button padding                     |
| `p-3`  | 12px | Small card internal padding             |
| `p-4`  | 16px | Standard card padding                   |
| `p-6`  | 24px | Page section padding                    |
| `p-8`  | 32px | Large section padding, page header      |
| `gap-4`| 16px | Grid gap between cards (mobile)         |
| `gap-6`| 24px | Grid gap between cards (desktop)        |

---

## 5. Border Radius & Shadows

### Border Radius
| Token        | Value  | Usage                                 |
|--------------|--------|---------------------------------------|
| `rounded`    | 4px    | Input fields, small chips             |
| `rounded-md` | 6px    | Buttons                               |
| `rounded-lg` | 8px    | Cards, dropdowns                      |
| `rounded-xl` | 12px   | Modals, large panels                  |
| `rounded-full`| 9999px | Avatar, circular icon buttons, tags  |

### Shadows
| Token         | Usage                                     |
|---------------|-------------------------------------------|
| `shadow-sm`   | Default card state                        |
| `shadow-md`   | Card hover state                          |
| `shadow-lg`   | Dropdowns, date pickers, modals           |
| `shadow-xl`   | Full-screen overlays                      |

---

## 6. Component Patterns

### NewsCard
```
┌──────────────────────────────────────┐
│  [Source logo]  Source · Timestamp   │
│                                      │
│  Article Headline (Merriweather H3)  │
│  line-clamp-2                        │
│                                      │
│  Summary text (2-3 lines, body-sm)   │
│                                      │
│  [Category chip]  [Sentiment badge]  │
└──────────────────────────────────────┘
```
- Card bg: `bg-white`, border: `border border-gray-200`, hover: `shadow-md`
- Headline font: Merriweather, `text-xl font-bold`
- On click: opens article in new tab (never navigate away from the app)
- Skeleton loading state required (use `animate-pulse` grey blocks)

### SentimentBadge
```
[● Positive]  [● Negative]  [● Neutral]
```
- Pill shape: `rounded-full px-2.5 py-0.5 text-xs font-semibold`
- Colours: use exact sentiment colour tokens — never custom colours
- Include a filled circle `●` prefix for accessibility (colour-blind support)
- ARIA: `role="status" aria-label="Sentiment: Positive"`

### CategoryChip (filter)
```
[Agriculture]  [IT Sector]  [Sports]  ...
```
- Unselected: `bg-gray-100 text-gray-700 border border-gray-200`
- Selected: use category accent colour with light bg variant
- `rounded-full px-3 py-1 text-sm font-medium cursor-pointer`
- Keyboard accessible: `role="checkbox" aria-checked={selected}`

### DatePicker (Historical page)
- Use a calendar UI component showing a month view
- Disable future dates
- Disable dates older than 1 year from today
- Selected date: primary colour highlight
- Today marker: secondary colour underline

### QuizCard
```
┌───────────────────────────────────────┐
│  Q7 of 10                [Timer: 2:34]│
│                                       │
│  Question text (body, font-medium)    │
│                                       │
│  ○ Option A                           │
│  ○ Option B                           │
│  ○ Option C                           │
│  ○ Option D                           │
│                                       │
│                    [Next →]           │
└───────────────────────────────────────┘
```
- Options: unselected `bg-white border-gray-200`, selected `bg-primary-light border-primary`
- Correct answer (post-submit): `bg-green-50 border-green-500`
- Wrong selected answer (post-submit): `bg-red-50 border-red-500`

### NavBar
- Logo + app name (left)
- Navigation links: News Feed, Historical, Quiz (centre on desktop, hamburger on mobile)
- Theme toggle (right, optional v2 feature)
- Sticky: `sticky top-0 z-50 bg-white/90 backdrop-blur-sm border-b border-gray-200`

---

## 7. Responsive Breakpoints (Mobile-First)

| Breakpoint | Min Width | Tailwind Prefix | Layout change                            |
|------------|-----------|-----------------|------------------------------------------|
| Mobile     | 0px       | (default)       | 1-column, full-width filters, hamburger  |
| sm         | 640px     | `sm:`           | 1-2 column cards, filter chips wrap      |
| md         | 768px     | `md:`           | 2-column cards, side filter panel        |
| lg         | 1024px    | `lg:`           | 3-column cards, persistent filter panel  |
| xl         | 1280px    | `xl:`           | 3-4 column cards, wider content area     |

Card grid: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6`

---

## 8. Accessibility (WCAG AA Minimum)

- All interactive elements must have a visible focus ring: `focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none`
- Colour contrast: text on background must meet 4.5:1 ratio. Check with the defined tokens — they are pre-verified.
- All images require `alt` text. Decorative images: `alt=""`.
- All form inputs require associated `<label>` (visible or visually hidden).
- Modal/dialog: trap focus within the modal, restore focus on close.
- Sentiment badges must include text label, not just colour (colour-blind support).
- Keyboard navigation: every interactive element must be reachable and operable via Tab/Enter/Space.
- ARIA landmarks: `<main>`, `<nav>`, `<aside>` (filter panel), `<header>`, `<footer>`.

---

## 9. Animation & Transitions

- **Standard transition**: `transition-all duration-150 ease-in-out`
- **Card hover**: `hover:shadow-md hover:-translate-y-0.5 transition-all duration-150`
- **Page transitions**: fade-in on route change (150ms opacity 0→1)
- **Skeleton loading**: `animate-pulse` on grey placeholder blocks
- **Toast/notification**: slide-in from bottom-right (200ms)
- **Modal**: fade-in backdrop + scale-up card (150ms)
- Respect `prefers-reduced-motion`: wrap animations in `@media (prefers-reduced-motion: no-preference)`

---

## 10. Iconography

- Icon library: **Lucide React** exclusively. Do not mix icon libraries.
- Icon sizes:
  - `size-4` (16px): inline with text, badges
  - `size-5` (20px): buttons, nav items
  - `size-6` (24px): standalone action icons
  - `size-8` (32px): empty-state illustrations
- Icons must always have `aria-hidden="true"` when decorative, or `aria-label` when standalone.
- Do not use emoji as UI icons.

---

## 11. Motivating Micro-copy Examples

Use encouraging, active language throughout the UI:

| Context                     | Copy                                                       |
|-----------------------------|------------------------------------------------------------|
| Interest selection CTA      | "Show me today's news →"                                  |
| Empty state (no results)    | "Nothing here yet — try broadening your filters."         |
| Quiz start                  | "Test what you know from the last 30 days."               |
| Quiz result (good score)    | "Great work! You scored 8/10. Keep reading daily."        |
| Quiz result (low score)     | "4/10 — Review today's highlights and try again!"         |
| Historical empty             | "No articles stored for this date yet."                   |
| Loading feed                | "Fetching the latest news for you…"                       |
