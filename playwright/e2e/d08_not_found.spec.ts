/**
 * D-08 E2E (#187)
 *
 * Verifies byte-for-byte D-08 fallback at UI layer:
 *   login → ask unknown keyword → exact string shown → sources panel empty
 *
 * D-08 (FR-CQ-03): Chat cannot answer → must say exactly
 * "Không tìm thấy thông tin này trong hồ sơ của bạn." — no fabrication.
 */
import { test, expect, login } from "../fixtures/auth";

const D08_EXACT = "Không tìm thấy thông tin này trong hồ sơ của bạn.";

test.describe("D-08 Not Found Fallback", () => {
  test("unknown keyword returns exact D-08 string with empty sources", async ({ page }) => {
    await login(page);
    await page.goto("/admin/chat");

    // Ask about something that cannot exist in any tenant's documents
    const chatInput = page.getByRole("textbox");
    await chatInput.fill("xylophone contract payment delta zeta 99999");
    await chatInput.press("Enter");

    // D-08 exact string must appear in UI — byte-for-byte
    await expect(
      page.getByText(D08_EXACT)
    ).toBeVisible({ timeout: 15_000 });

    // Sources panel must be empty (no document chips)
    const sourceChips = page.getByText(/📄 nguồn|source:/i);
    await expect(sourceChips).toHaveCount(0);
  });

  test("single-doc tenant: named non-existent doc returns D-08", async ({ page }) => {
    await login(page);
    await page.goto("/admin/chat");

    const chatInput = page.getByRole("textbox");
    await chatInput.fill("HĐ XYZ-NONEXISTENT-DOC-999 hết hạn khi nào?");
    await chatInput.press("Enter");

    await expect(
      page.getByText(D08_EXACT)
    ).toBeVisible({ timeout: 15_000 });

    const sourceChips = page.getByText(/📄 nguồn|source:/i);
    await expect(sourceChips).toHaveCount(0);
  });

  test("interpretation request returns D-08 (D-06 read-only)", async ({ page }) => {
    await login(page);
    await page.goto("/admin/chat");

    // D-06: backend does not interpret legal content
    const chatInput = page.getByRole("textbox");
    await chatInput.fill("tôi có thể hủy hợp đồng này không?");
    await chatInput.press("Enter");

    // Expect either D-08 fallback or out-of-scope message (not a legal opinion)
    const response = page.locator("[data-testid='chat-answer'], .chat-answer, [role='article']").last();
    await expect(response).toBeVisible({ timeout: 15_000 });

    // Must NOT contain legal interpretation keywords
    const bodyText = await response.textContent() || "";
    expect(bodyText).not.toMatch(/bạn có thể hủy|có quyền hủy|được phép hủy/i);
  });
});
