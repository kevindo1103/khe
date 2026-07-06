/**
 * Playwright auth fixtures.
 *
 * Wraps the 3-field Khế login form (tenant_id / username / password) and
 * exposes an `authenticatedPage` fixture that starts already logged in.
 */
import { test as base, type Page } from "@playwright/test";

export interface Credentials {
  tenantId: string;
  username: string;
  password: string;
}

// Default UAT creds — override via env for CI / staging.
export const UAT_CREDS: Credentials = {
  tenantId: process.env.UAT_TENANT_ID || "uat-demo",
  username: process.env.UAT_USERNAME || "demo",
  password: process.env.UAT_PASSWORD || "Khe@UAT2026",
};

export async function login(page: Page, creds: Credentials = UAT_CREDS) {
  await page.goto("/admin/login");
  await page.getByTestId("login-tenant-id").fill(creds.tenantId);
  await page.getByTestId("login-username").fill(creds.username);
  await page.getByTestId("login-password").fill(creds.password);
  await page.getByRole("button", { name: /đăng nhập/i }).click();
  // Wait until redirect out of login page
  await page.waitForURL(/\/admin(?!\/login)/, { timeout: 10_000 });
}

// Extended test fixture with pre-authenticated page
export const test = base.extend<{ authenticatedPage: Page }>({
  authenticatedPage: async ({ page }, use) => {
    await login(page);
    await use(page);
  },
});

export { expect } from "@playwright/test";
