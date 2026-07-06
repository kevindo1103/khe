/**
 * Consent Gate E2E (#187)
 *
 * Verifies NĐ 13/2023 + DEC-010 consent gate at UI layer:
 *   no-consent tenant → upload blocked with clear message →
 *   admin grants consent → upload succeeds
 *
 * Requires: `uat-demo-noconsent` tenant seeded (Backend lead #75).
 * Skip if env vars not provided.
 */
import { test, expect, login, type Credentials } from "../fixtures/auth";

const NOCONSENT_CREDS: Credentials = {
  tenantId: process.env.UAT_NOCONSENT_TENANT || "uat-demo-noconsent",
  username: process.env.UAT_NOCONSENT_USER || "demo-noconsent",
  password: process.env.UAT_NOCONSENT_PASS || "Khe@UAT2026",
};

test.describe("Consent Gate (DEC-010 / NĐ 13/2023)", () => {
  test.skip(
    !process.env.UAT_NOCONSENT_TENANT,
    "Skipped: UAT_NOCONSENT_TENANT env var not set — seed uat-demo-noconsent first (see #75)"
  );

  test("no-consent tenant: upload blocked with clear UI message", async ({ page }) => {
    await login(page, NOCONSENT_CREDS);
    await page.goto("/admin/upload");

    // Attempt upload
    const fileInput = page.locator('input[type="file"]');
    // Create a minimal PDF bytes inline
    const pdfContent = Buffer.from(
      "%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\ntrailer<</Size 1>>\nstartxref\n9\n%%EOF"
    );
    await fileInput.setInputFiles({
      name: "test.pdf",
      mimeType: "application/pdf",
      buffer: pdfContent,
    });

    // Expect 403-based error message in UI
    await expect(
      page.getByText(/chưa đồng ý|consent|chưa cấp quyền/i)
    ).toBeVisible({ timeout: 10_000 });

    // Must NOT show "processing" or "success"
    await expect(page.getByText(/đang xử lý|processing|thành công|uploaded/i)).toHaveCount(0);
  });

  test("after consent granted: upload succeeds", async ({ page }) => {
    // This test requires the admin to have granted consent via API or UI.
    // In automated CI, consent is granted via API before this test runs.
    // Here we verify the post-consent state.
    await login(page, NOCONSENT_CREDS);

    // Grant consent via API (simulates admin action)
    const apiBase = process.env.PLAYWRIGHT_BASE_URL
      ? process.env.PLAYWRIGHT_BASE_URL.replace(/\/$/, "")
      : "http://localhost:8000";

    // POST /consent via fetch in page context (cookie already set from login)
    const consentResult = await page.evaluate(async (base) => {
      const r = await fetch(`${base}/api/consent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ purpose: "vision_extraction" }),
      });
      return { status: r.status, body: await r.json() };
    }, apiBase);

    expect([200, 201]).toContain(consentResult.status);

    // Now upload should work
    await page.goto("/admin/upload");
    const fileInput = page.locator('input[type="file"]');
    const pdfContent = Buffer.from(
      "%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\ntrailer<</Size 1>>\nstartxref\n9\n%%EOF"
    );
    await fileInput.setInputFiles({
      name: "consent_test.pdf",
      mimeType: "application/pdf",
      buffer: pdfContent,
    });

    // Should proceed to processing
    await expect(
      page.getByText(/đang xử lý|processing|uploaded|thành công/i)
    ).toBeVisible({ timeout: 10_000 });
  });

  test("revoke consent: upload blocked again", async ({ page }) => {
    await login(page, NOCONSENT_CREDS);

    const apiBase = process.env.PLAYWRIGHT_BASE_URL
      ? process.env.PLAYWRIGHT_BASE_URL.replace(/\/$/, "")
      : "http://localhost:8000";

    // Revoke consent
    const revokeResult = await page.evaluate(async (base) => {
      const r = await fetch(`${base}/api/consent/revoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ purpose: "vision_extraction" }),
      });
      return r.status;
    }, apiBase);
    expect(revokeResult).toBe(200);

    await page.goto("/admin/upload");
    const fileInput = page.locator('input[type="file"]');
    const pdfContent = Buffer.from(
      "%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\ntrailer<</Size 1>>\nstartxref\n9\n%%EOF"
    );
    await fileInput.setInputFiles({
      name: "post_revoke.pdf",
      mimeType: "application/pdf",
      buffer: pdfContent,
    });

    await expect(
      page.getByText(/chưa đồng ý|consent|chưa cấp quyền/i)
    ).toBeVisible({ timeout: 10_000 });
  });
});
