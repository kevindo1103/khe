/**
 * M0 Happy Path E2E (#187)
 *
 * Verifies the core SME user journey end-to-end:
 *   login → upload PDF → poll extraction → confirm extracted →
 *   view obligations → ask chat → receive answer with sources
 *
 * Against: staging (PLAYWRIGHT_BASE_URL=https://staging.khe.iceflow.cloud)
 * Creds:   UAT_TENANT_ID / UAT_USERNAME / UAT_PASSWORD env vars
 */
import * as path from "path";
import * as fs from "fs";
import * as os from "os";
import { test, expect, login } from "../fixtures/auth";

const POLL_INTERVAL = 2_000;
const EXTRACT_TIMEOUT = 30_000;

test.describe("M0 Happy Path", () => {
  test("login → upload → extraction → obligations → chat", async ({ page }) => {
    // ── 1. Login ──────────────────────────────────────────────────────────
    await login(page);
    await expect(page).toHaveURL(/\/admin/);

    // ── 2. Upload PDF ─────────────────────────────────────────────────────
    await page.goto("/admin/upload");
    // Create a minimal valid PDF fixture in a temp dir
    const tmpPdf = path.join(os.tmpdir(), "khe_e2e_test.pdf");
    fs.writeFileSync(
      tmpPdf,
      // Minimal single-page PDF with a contract-like text
      `%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 72 720 Td (Test Contract) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000368 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
441
%%EOF`
    );

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(tmpPdf);

    // Wait for upload confirmation (status "processing")
    await expect(
      page.getByText(/đang xử lý|processing/i)
    ).toBeVisible({ timeout: 10_000 });

    // ── 3. Poll for extraction completion ─────────────────────────────────
    await page.goto("/admin/documents");

    let extracted = false;
    const deadline = Date.now() + EXTRACT_TIMEOUT;
    while (!extracted && Date.now() < deadline) {
      await page.waitForTimeout(POLL_INTERVAL);
      await page.reload();
      const statusText = await page.textContent("body");
      if (statusText?.match(/extracted|đã bóc tách/i)) {
        extracted = true;
      }
    }
    expect(extracted, "Document should reach extracted status within 30s").toBe(true);

    // ── 4. Document detail shows terms ────────────────────────────────────
    // Click the first document in the list
    await page.locator("a, [role=row]").filter({ hasText: /khe_e2e_test|test contract/i }).first().click();
    await expect(page).toHaveURL(/\/admin\/documents\/\d+/);
    // Terms section should be present
    await expect(page.getByText(/thông tin bóc tách|terms|fields/i)).toBeVisible();

    // ── 5. Obligations page renders ───────────────────────────────────────
    await page.goto("/admin/obligations");
    // Page loads without error (may be empty if test PDF has no dates)
    await expect(page).not.toHaveURL(/error/);
    await expect(page.locator("body")).not.toContainText(/500|internal server error/i);

    // ── 6. Chat — answer with sources ────────────────────────────────────
    await page.goto("/admin/chat");
    const chatInput = page.getByRole("textbox");
    await chatInput.fill("hợp đồng hết hạn khi nào?");
    await chatInput.press("Enter");

    // Either found answer OR D-08 fallback — both are correct outcomes
    await expect(
      page.getByText(/không tìm thấy|hết hạn|ngày/i)
    ).toBeVisible({ timeout: 15_000 });

    // Sources chip should appear if found=true
    // (non-blocking check — D-08 case has no sources)
    const sourceChips = page.getByText(/📄 nguồn|source/i);
    // sources visible OR D-08 fallback visible — one must be true
    const d08Msg = page.getByText("Không tìm thấy thông tin này trong hồ sơ của bạn.");
    const hasResult = (await sourceChips.count()) > 0 || (await d08Msg.count()) > 0;
    expect(hasResult, "Chat should show sources or D-08 fallback").toBe(true);

    // Cleanup
    fs.unlinkSync(tmpPdf);
  });
});
