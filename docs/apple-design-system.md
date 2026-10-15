# Sentiri Apple Design System

> Reusable design tokens, CSS, and patterns for applying the Apple-style aesthetic to any template in the Sentiri project.
> Last updated: 2026-10-15

---

## 1. Core Principles

Apple's design language is defined by **restraint, not decoration**:

1. **Clean whitespace** — let content breathe, generous padding
2. **Typography-first** — SF Pro font, tight tracking, precise weights
3. **Subtle depth** — layered soft shadows, never heavy borders
4. **Single-hue backgrounds** — flat colors, no multi-color gradients
5. **Smooth motion** — Apple's signature easing curve, slow and deliberate

---

## 2. Font Stack

```css
body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
                 "Helvetica Neue", "Inter", sans-serif;
    letter-spacing: -0.01em;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
```

---

## 3. Color Palette

### Neutral / Backgrounds
```css
/* Apple's signature neutral grey */
--bg-neutral: #f5f5f7;      /* page background */
--bg-card: #ffffff;         /* card surface */
--text-primary: #1d1d1f;    /* headings */
--text-secondary: #6e6e73;  /* body text */
--text-tertiary: #86868b;   /* footers, captions */
```

### Brand / Accent
```css
--accent-blue: #0071e3;     /* Apple blue — links, logo, CTAs */
```

### Role-themed deep backgrounds (for hover states / sections)
```css
.bg-role-admin     { background: #1d1d1f; }  /* near-black */
.bg-role-therapist { background: #0b3d2e; }  /* deep forest green */
.bg-role-doctor    { background: #0a3552; }  /* deep navy blue */
.bg-role-client    { background: #4a2311; }  /* deep umber brown */
.bg-role-default   { background: #f5f5f7; }  /* neutral grey */
```

---

## 4. Typography Scale

```css
.page-eyebrow {
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.08em;       /* wide tracking for ALL-CAPS labels */
    text-transform: uppercase;
    color: #6e6e73;
}

.page-title {
    font-weight: 700;
    font-size: 3rem;               /* 48px */
    line-height: 1.1;
    letter-spacing: -0.03em;       /* tight tracking — Apple signature */
    color: #1d1d1f;
}

.page-subtitle {
    font-size: 1.1rem;             /* 17.6px */
    font-weight: 400;
    color: #6e6e73;
}

.role-title {
    font-weight: 600;
    font-size: 1.25rem;
    color: #1d1d1f;
}

.role-desc {
    font-size: 0.9rem;
    color: #6e6e73;
}

.footer-text {
    font-size: 0.8rem;
    color: #86868b;
}
```

---

## 5. Card Component

```css
.apple-card {
    background: #ffffff;
    border-radius: 18px;            /* Apple's signature corner radius */
    overflow: hidden;
    /* Layered soft shadow — Apple depth */
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04),
                0 8px 24px rgba(0, 0, 0, 0.06);
    transition: transform 0.6s cubic-bezier(0.25, 0.1, 0.25, 1),
                box-shadow 0.6s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.apple-card:hover {
    transform: translateY(-10px) scale(1.02);
}
```

---

## 6. Pill / Chip Component

```css
.role-chip {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    padding: 4px 12px;
    border-radius: 980px;           /* fully rounded pill */
    background: #f5f5f7;
    color: #6e6e73;
}
```

---

## 7. The Apple Easing Curve

**This is the single most important value.** Use it for ALL transitions:

```css
transition: all 0.6s cubic-bezier(0.25, 0.1, 0.25, 1);
```

- For **background fades** use `1s`
- For **card hovers** use `0.6s`
- For **entrance animations** use `0.9s`

Never use `ease-in-out` or `ease`. Always this exact bezier curve.

---

## 8. Entrance Animation (fade-up, staggered)

```css
.fade-up {
    animation: fadeUp 0.9s cubic-bezier(0.25, 0.1, 0.25, 1) both;
}
.fade-up:nth-child(2) { animation-delay: 0.1s; }
.fade-up:nth-child(3) { animation-delay: 0.2s; }
.fade-up:nth-child(4) { animation-delay: 0.3s; }

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}
```

---

## 9. Dark Background Text Inversion

When a role background (dark) is active, invert text to light:

```css
body.role-active .page-title    { color: #f5f5f7 !important; }
body.role-active .page-eyebrow  { color: #a1a1a6 !important; }
body.role-active .page-subtitle { color: #a1a1a6 !important; }
body.role-active .footer-text   { color: #86868b !important; }
body.role-active .logo-box      { background: rgba(255, 255, 255, 0.18) !important; }
body.role-active .role-chip     { background: rgba(255, 255, 255, 0.14) !important;
                                  color: #f5f5f7 !important; }
```

---

## 10. Role Background Swap (JavaScript)

```javascript
document.addEventListener('DOMContentLoaded', function () {
    var body = document.getElementById('welcomeBody');
    var cards = document.querySelectorAll('.role-card');
    var roleClasses = ['bg-role-default', 'bg-role-admin',
                       'bg-role-therapist', 'bg-role-doctor', 'bg-role-client'];

    function setBackground(role) {
        roleClasses.forEach(function(c) { body.classList.remove(c); });
        body.classList.remove('role-active');
        if (role && role !== 'default') {
            body.classList.add('bg-role-' + role);
            body.classList.add('role-active');
        } else {
            body.classList.add('bg-role-default');
        }
    }

    cards.forEach(function(card) {
        var role = card.getAttribute('data-role');
        card.addEventListener('mouseenter', function() { setBackground(role); });
        card.addEventListener('mouseleave', function() { setBackground('default'); });
    });
});
```

---

## 11. Quick Application Checklist

To apply this system to any new template:

- [ ] Use the SF Pro font stack + `antialiased` on `body`
- [ ] Set `background: #f5f5f7` as the default page background
- [ ] Use `#1d1d1f` / `#6e6e73` / `#86868b` for text hierarchy
- [ ] Use `#0071e3` for any accent/CTA
- [ ] Cards: `border-radius: 18px` + layered soft shadows
- [ ] Chips/pills: `border-radius: 980px`
- [ ] ALL transitions use `cubic-bezier(0.25, 0.1, 0.25, 1)`
- [ ] Add staggered `fade-up` entrance on load
- [ ] Keep it flat — no multi-color gradients
- [ ] Generous padding (`p-6` minimum on cards)

---

## 12. Files Using This System

| File | Purpose |
|---|---|
| `chat_analyzer/templates/chat_analyzer/welcome.html` | Role selection landing page (reference implementation) |
| `chat_analyzer/templates/chat_analyzer/auth/login.html` | Login page (glassmorphism variant) |
| `chat_analyzer/templates/chat_analyzer/client/base_client.html` | Client portal shell |

> When adding the system to a new template, copy the CSS from `welcome.html`'s `{% block extra_css %}` as the canonical source.
