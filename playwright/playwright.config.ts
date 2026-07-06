import { defineConfig, devices } from "@playwright/test";

const BASE_URL =
  process.env.PLAYWRIGHT_BASE_URL || "http://localhost:5173";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 30_000,
  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: BASE_URL,
    // Use pre-installed Chromium in CCR / GitHub Actions env.
    // Falls back to default discovery if env var not set (local dev).
    ...(process.env.PLAYWRIGHT_BROWSERS_PATH
      ? {
          launchOptions: {
            executablePath:
              process.env.PLAYWRIGHT_BROWSERS_PATH + "/chromium",
          },
        }
      : {}),
    headless: true,
    trace: "on-first-retry",
    // Credentials for HttpOnly-cookie auth (D-03 / khe_session cookie)
    ignoreHTTPSErrors: true,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Local dev: spin up Vite + uvicorn before tests.
  // In CI / staging mode (PLAYWRIGHT_BASE_URL set), skip webServer entirely.
  ...(process.env.PLAYWRIGHT_BASE_URL
    ? {}
    : {
        webServer: [
          {
            command: "cd ../backend && uvicorn main:app --port 8000",
            port: 8000,
            reuseExistingServer: true,
            timeout: 30_000,
          },
          {
            command: "cd ../frontend && npm run dev",
            port: 5173,
            reuseExistingServer: true,
            timeout: 30_000,
          },
        ],
      }),
});
