# BangOps — UI Design Brief (for the redesign)

*Written 26 Sep 2026. This is the brief for redesigning everything in [`prototypes/`](../../prototypes). The goal: a clean, calm product that looks like four senior designers argued over every pixel, not an AI-generated dashboard.*

---

## 1. What's wrong today (measured, not guessed)

| Problem | Evidence |
|---|---|
| **No spacing system** | `ops-hub.html` uses **28 different padding values**, `ops-hub-wireframe.html` uses 21, `onboarding-flow.html` uses 14. Spacing is ad hoc, which is why nothing lines up and the layout feels cramped. |
| **Too much information per screen** | Every block tries to show everything at once: status, counts, chips, and descriptions together. There's no hierarchy of primary → secondary → on-demand. |
| **"AI-generated" look** | Emoji used as icons, a card around everything, badge soup, explanatory copy on every element, gradients and decorative containers. |
| **Generic type** | A system font stack with no deliberate scale, and weight/size used inconsistently for hierarchy. |

## 2. Research first, then design

Before drawing, study how excellent operational products handle *the same jobs*. For each reference, capture screenshots and note **what they leave out**.

| Job in BangOps | Study these | What to learn |
|---|---|---|
| Today / home | **Linear** (My Issues, Inbox), **Height**, **Things 3** | One list, one primary action, a generous empty state |
| Review and approve drafts (email, timesheet rows) | **Superhuman**, **Linear Inbox**, **GitHub PR review**, **Granola** | Split view (list ↔ detail), keyboard-first, approve in one keystroke |
| Chat with the agent | **Claude.ai**, **ChatGPT**, **Perplexity**, **Raycast AI** | A calm composer; results rendered as structured cards, not walls of text |
| Projects table | **Attio**, **Linear Projects**, **Notion databases**, **Airtable interface designer** | Dense but readable tables, 1 px dividers, no zebra stripes, sticky headers |
| Timesheet / hours | **Harvest**, **Toggl Track**, **Timely** (AutoSheet), **Productive** | Week grid, draft vs. approved state, totals that don't shout |
| Vendors (later) | **Airtable**, **Mobbin/Layers-style filter bars**, **Stripe Dashboard** tables | Filter chips + table, with detail in a side sheet |
| Onboarding | **Linear onboarding**, **Arc**, **Cron/Notion Calendar** | One question per screen, big type, instant payoff |
| Overall polish | **Vercel dashboard**, **Stripe**, **Resend**, **Cal.com** | Restraint: neutral greys, one accent, crisp borders |

**Deliverable of the research step:** a `docs/design/references.md` with 15–25 annotated screenshots grouped by the jobs above, plus 5–8 **principles** extracted from them (each principle cites a reference).

## 3. Design principles (starting point, refine after research)

1. **One job per screen.** If a screen answers two questions, split it or move one into a side sheet.
2. **Progressive disclosure.** Show 3 facts per item; everything else appears on hover, expand, or in the detail pane.
3. **Draft → Approve is the core interaction.** Every agent output (email, log row) has the same visual pattern and the same keys (`A` approve, `E` edit, `⌘↵` send).
4. **Calm by default.** Colour only means state (red = needs you, amber = waiting, green is almost never needed). Everything else stays neutral.
5. **Words are UI.** Short labels, sentence case, no emoji, no exclamation marks, no "✨ AI". The agent writes like a senior colleague.
6. **Empty is the goal.** "Nothing needs you" is a designed, satisfying state.

## 4. Foundations (tokens, set once, used everywhere)

| Token | Rule |
|---|---|
| **Spacing** | 4 px base. Scale: `4 · 8 · 12 · 16 · 24 · 32 · 48 · 64`. **Nothing else is allowed.** Page gutter 24 (16 on mobile); section gap 32–48; row height 40–44. |
| **Type** | One family (e.g. *Inter*, *Geist*, or *Söhne*-like). Scale: `12 / 13 / 14 (body) / 16 / 20 / 24 / 32`. Weights: 400 and 500 (600 only for page titles). Line height 1.5 body, 1.25 headings. Tabular numbers for hours. |
| **Colour** | Neutral greys (≈10 steps) + **one accent** + 3 state colours. Full light and dark themes defined as tokens. |
| **Radius** | 6 (inputs, chips), 10 (panels). No pill-everything. |
| **Borders / elevation** | 1 px hairlines instead of shadows. Shadow only on floating layers (menus, dialogs). |
| **Icons** | One line-icon set (Lucide / Phosphor), 16 px, 1.5 stroke. **No emoji.** |
| **Motion** | 120–180 ms ease-out; no bounces. |

## 5. Screens for v1 (matches [`architecture-v2`](../architecture/architecture-v2-workspace-native.md))

1. **Home: "Needs you"**. One list mixing client emails awaiting reply and today's unapproved log rows. The empty state is the goal.
2. **Compose**: a chat composer → project detected → options → draft with SOP checks → Copy / Gmail draft / Send.
3. **Today's log**: drafted resource rows in a week grid, approve per row or all at once.
4. **Inbox detail**: client thread summary, asks, reply options (split view).
5. **Onboarding**: 3 steps (Allow → paste resource sheet → paste Chat webhook) with an instant payoff.
6. *(Later)* Projects table, Vendors, founder credits view.

## 6. Process (how "four senior designers" actually happens)

1. **Research board** (§2), then agree on principles.
2. **Wireframes in greyscale** for all 5 screens. Review against the principles; cut 30% of the content.
3. **Tokens and components** (button, input, list row, draft card, chip, side sheet, empty state).
4. **High-fidelity, light and dark**, at 1440 and 390 widths.
5. **Critique pass with four lenses**, each one a separate review (list issues, then fix):
   - *Product designer*: does each screen do one job? Is anything unnecessary?
   - *Visual designer*: does every spacing/type value come from the scale? Is the alignment perfect?
   - *Content designer*: are the labels short, is the tone consistent, is there zero filler copy?
   - *Interaction / a11y designer*: keyboard paths, focus states, contrast ≥ 4.5:1, touch targets ≥ 40 px.
6. Only then rebuild the HTML prototypes.

## 7. Definition of done

- Every padding, margin, and gap value comes from the spacing scale (enforce with a lint or search).
- ≤ 1 accent colour, ≤ 2 font weights on any screen, zero emoji.
- Each screen passes the "5-second test": a new person can say what it's for and what to do next.
- Screenshots of each screen sit next to their closest reference in `references.md`, and the redesign holds up in that comparison.
