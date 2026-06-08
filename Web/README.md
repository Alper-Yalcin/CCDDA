<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/f21e0072-ea1f-4bea-98ae-8abbcafef21e

## Run Locally

**Prerequisites:**  Node.js (recommended v18+)

1. Install dependencies

   ```powershell
   npm install
   ```

2. Create a local env file and set your Gemini key

   - Copy the example file (PowerShell):

     ```powershell
     copy .env.example .env.local
     ```

   - Open `Web/.env.local` and set `GEMINI_API_KEY` (and `APP_URL` if needed).

   Note: Do NOT commit `.env.local` to version control. Keep your secret keys private.

3. Run the app locally

   ```powershell
   npm run dev
   ```

Notes

- If you need to clean the build folder on Windows, you can run `rd /s /q dist` in PowerShell or use `npx rimraf dist` for cross-platform removal.
- The development server runs on port `3000` by default (see `package.json` scripts and `vite.config.ts`).
