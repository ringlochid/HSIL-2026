## 2. Colors & Surface Logic
The palette is a study in restrained sophistication. It leverages a deep charcoal foundation to reduce eye strain during long genomic review sessions.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of light-absorbing materials.
*   **Level 0 (Base):** `background` (#0c0e10) - The infinite void.
*   **Level 1 (Sections):** `surface-container-low` (#111416) - Large workspace areas.
*   **Level 2 (Cards):** `surface-container` (#161a1e) - Primary data containers.
*   **Level 3 (Floating/Active):** `surface-container-high` (#1b2025) - Modals or active tooltips.

---

## 3. Typography: The Editorial Edge
The type system pairs the geometric precision of **Manrope** for high-level data storytelling with the utilitarian clarity of **Inter** for dense clinical readings.

*   **Display & Headline (Manrope):** These are your "Anchors." Use `display-sm` for genomic headers to provide a sense of monumental importance. The generous tracking and low-drama weight convey a "calm under pressure" aesthetic.
*   **Body & Title (Inter):** Engineered for legibility. Use `body-md` (0.875rem) as the workhorse for gene sequences and variant descriptions.
*   **The "Data-First" Hierarchy:** By keeping headers `on-surface` and secondary metadata in `on-surface-variant`, we create a natural scanning path that highlights critical findings without using "alarmist" red colors.

---

## 4. Elevation & Depth
In this system, light does not "hit" the surface; the surface "glows" from within.

*   **Tonal Layering:** Avoid shadows on standard cards. Instead, place a `surface-container-lowest` card on a `surface-container-low` section. This "inverted lift" creates a sophisticated, recessed look.
*   **Ambient Shadows:** For floating elements (Modals/Popovers), use an extra-diffused shadow: `box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4)`. The shadow must be nearly invisible, felt rather than seen.
*   **The "Ghost Border" Fallback:** If accessibility requirements demand a boundary, use `outline-variant` (#42494e) at **15% opacity**. This creates a "whisper" of a line that suggests a boundary without breaking the tonal flow.
*   **Glassmorphism:** Use `surface-bright` at 60% opacity with a `blur(12px)` for navigation rails. This allows the complex genomic data to subtly "ghost" behind the UI, maintaining context.

---

## 5. Components

### Cards & Lists
*   **Card Styling:** Use `rounded-lg` (0.5rem) for a compact, professional feel. 
*   **Anti-Divider Policy:** Forbid the use of horizontal rules (`<hr>`). Separate list items using `8px` of vertical whitespace or a subtle toggle between `surface-container` and `surface-container-low` backgrounds.

### Buttons
*   **Primary:** A gradient-fill from `primary` to `primary-container`. Typography set in `label-md` bold, all-caps for an "Active Command" feel.
*   **Secondary:** Ghost style. No background, no border. Only a `primary` colored label. On hover, a subtle `surface-variant` background appears.

### Input Fields
*   **Architecture:** Use `surface-container-highest` for the input track. No border. A 2px bottom-accent in `primary` appears only on `:focus`. This minimizes visual noise in complex forms.

---
