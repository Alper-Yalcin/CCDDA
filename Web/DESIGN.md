# UI/UX Design Concept: Child Art Emotion Analyzer

## 1. Design Philosophy & Style
- **Core Theme:** "Scientific Empathy"
- **Visual Language:** Clean, minimal, and professional, but approachable. It avoids being overly "childish" (no comic sans or primary colors) to maintain credibility with professionals, yet remains soft enough to feel safe.
- **Color Palette:**
  - **Primary (Trust/Calm):** Soft Teal / Sage Green (`#38B2AC` / `#319795`) - Evokes balance and growth.
  - **Secondary (Warmth):** Soft Sand / Cream (`#F7FAFC` / `#EDF2F7`) - Backgrounds, paper-like feel.
  - **Accent (Action):** Muted Coral (`#ED8936`) - For primary CTAs, warm and inviting.
  - **Text:** Dark Slate (`#2D3748`) - High contrast but softer than pure black.
  - **Status Colors:**
    - *Happy/Positive:* Soft Emerald (`#68D391`)
    - *Sad/Concern:* Muted Indigo (`#63B3ED`)
- **Typography:**
  - **Headings:** `Outfit` or `Space Grotesk` - Modern, geometric sans-serif with character.
  - **Body:** `Inter` or `DM Sans` - Highly legible, neutral, and professional.
- **Shapes & Depth:**
  - **Corners:** `rounded-2xl` (16px) or `rounded-3xl` (24px) for a friendly, organic feel.
  - **Shadows:** `shadow-sm` for cards, `shadow-lg` for floating actions. Soft, diffuse shadows.

## 2. User Flow
1.  **Landing Page:** Introduction -> "Start Analysis" CTA.
2.  **Upload:** Drag & Drop -> Preview -> "Analyze".
3.  **Processing:** Loading state with comforting animation (e.g., pulsing circle or drawing animation).
4.  **Results:** Immediate visual feedback (Emotion Label) -> Detailed Heatmap -> Interpretation.
5.  **Action:** Save to Dashboard / Download Report.

## 3. Page Breakdowns

### A. Landing Page
- **Hero Section:**
  - **Headline:** "Understanding Emotions Through Art."
  - **Subheadline:** "Advanced AI analysis to support psychologists and educators in interpreting children's drawings."
  - **Visual:** Split layout. Left: Text & CTA. Right: Abstract illustration of a drawing being scanned/analyzed.
  - **CTA:** "Start Analysis" (Primary Button).

### B. Upload & Analysis Page
- **Central Card:** A large, dashed-border drop zone.
- **Interaction:**
  - *Idle:* "Drag and drop a drawing here, or click to browse."
  - *Hover:* Border turns Primary Color.
  - *File Selected:* Thumbnail preview with a "Remove" icon.
  - *Privacy Notice:* Small text below: "Images are processed securely and not stored permanently without consent."

### C. Results Page
- **Layout:** Two-column grid (Desktop).
  - **Left (Visual):** The uploaded image with a toggle to show/hide the "Heatmap Overlay" (explaining *why* the AI made the prediction).
  - **Right (Analysis):**
    - **Primary Emotion:** Large text (e.g., "Happy") with an icon.
    - **Confidence:** "92% Confidence".
    - **Interpretation Box:** A text area for the professional to add their own notes.
    - **Actions:** "Download Report (PDF)", "Save to Dashboard".

### D. Dashboard
- **View:** Grid of cards.
- **Card Content:** Thumbnail (blurred for privacy until hovered), Date, Predicted Emotion tag.
- **Filters:** By Date, By Emotion.

## 4. Component Library (Tailwind CSS)

### Buttons
- **Primary:** `bg-teal-500 text-white hover:bg-teal-600 rounded-xl px-6 py-3 font-medium transition-all shadow-md hover:shadow-lg`
- **Secondary:** `bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 rounded-xl px-6 py-3 font-medium transition-all`

### Cards
- **Standard:** `bg-white rounded-2xl shadow-sm border border-slate-100 p-6`
- **Interactive:** `hover:shadow-md transition-shadow cursor-pointer`

### Typography
- **H1:** `font-display text-4xl md:text-5xl font-bold text-slate-800 tracking-tight`
- **H2:** `font-display text-2xl md:text-3xl font-semibold text-slate-800`
- **Body:** `font-sans text-slate-600 leading-relaxed`

## 5. UX Considerations
- **Privacy First:** Explicitly state privacy policies near upload areas.
- **Non-Diagnostic Language:** Use phrases like "Indicates signs of..." rather than "Diagnosed with...".
- **Loading States:** Use skeleton screens or calming animations instead of generic spinners.
