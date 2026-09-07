/**
 * Requirement:
 *   "The application should allow users to reset their password using their registered
 *    email address. The reset link expires after 30 minutes."
 *
 * Acceptance Criterion [Confirmed - Requirement]:
 *   "A registered user can submit a password-reset request."
 *
 * Test Case:
 *   "Verify that a user can submit a password-reset request using a registered email address."
 *
 * Automation Type: UI (Playwright + TypeScript)
 *
 * Traceability:
 *   Requirement -> Acceptance Criterion ("A registered user can submit a password-reset
 *   request.") -> Test Case (above) -> Automation Type: UI -> this script
 *   (tests/ui/password-reset.spec.ts).
 *
 * Provenance note:
 *   The page name, selectors, and expected confirmation text used below are supplied
 *   directly as [Confirmed - Supplied] test input (not discovered by ui-agent, and not
 *   verified against a live application). No selectors, assertions, or steps beyond what
 *   was supplied have been added.
 */

import { test, expect } from '@playwright/test';

// [Not supplied by test input] Navigation target for the Password Reset page.
// Required to load the page under test; no route/URL was included in the supplied
// findings, so this is externalized rather than guessed at and hard-coded.
const PASSWORD_RESET_PATH = process.env.PASSWORD_RESET_PATH ?? '/password-reset';

// [Not supplied by test input] Registered account email for the target test environment.
// Must correspond to a real registered account for this scenario to be meaningful; not
// invented here, sourced from environment configuration instead of a hard-coded value.
const REGISTERED_EMAIL = process.env.TEST_REGISTERED_EMAIL;

test.describe('Password Reset', () => {
  test('user can submit a password-reset request using a registered email address', async ({ page }) => {
    test.skip(
      !REGISTERED_EMAIL,
      'TEST_REGISTERED_EMAIL environment variable must be set to a registered account email for this environment.'
    );

    // Navigate to the Password Reset page.
    await page.goto(PASSWORD_RESET_PATH);

    // Supplied selector: email input.
    await page.locator('[data-testid="email"]').fill(REGISTERED_EMAIL!);

    // Supplied selector: submit button.
    await page.locator('[data-testid="reset-submit"]').click();

    // Supplied selector + expected text: confirmation message.
    await expect(page.locator('[data-testid="reset-confirmation"]')).toHaveText(
      'If an account exists, instructions have been sent.'
    );
  });
});
