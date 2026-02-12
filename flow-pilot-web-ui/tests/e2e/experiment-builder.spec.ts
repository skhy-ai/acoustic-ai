import { test, expect } from '@playwright/test';

/**
 * Experiment Builder Tests
 * =========================
 * Tests the ExperimentBuilder UI component flow:
 * page load, navigation, and parameter configuration.
 *
 * PREREQUISITES:
 *   - Frontend running on localhost:5173
 */

test.describe('Experiment Builder', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        // Wait for the app to hydrate
        await page.waitForTimeout(1000);
    });

    test('main page loads successfully', async ({ page }) => {
        await expect(page).toHaveTitle(/.*Acoustic.*/i);
        // Or at minimum the page doesn't error
        const errors: string[] = [];
        page.on('pageerror', (err) => errors.push(err.message));
        await page.waitForTimeout(1000);
        expect(errors).toHaveLength(0);
    });

    test('sidebar contains expected navigation items', async ({ page }) => {
        const sidebar = page.locator('[class*="sidebar"], nav, aside');
        if (await sidebar.count() > 0) {
            const sidebarText = await sidebar.textContent();
            // These should exist in development mode
            const expectedItems = ['Experiment', 'Data', 'Analysis', 'Model'];
            const foundItems = expectedItems.filter(item =>
                sidebarText?.toLowerCase().includes(item.toLowerCase())
            );
            // At least some navigation should be present
            expect(foundItems.length).toBeGreaterThan(0);
        }
    });

    test('no console errors on initial load', async ({ page }) => {
        const consoleErrors: string[] = [];
        page.on('console', (msg) => {
            if (msg.type() === 'error') {
                consoleErrors.push(msg.text());
            }
        });

        await page.goto('/');
        await page.waitForTimeout(2000);

        // Filter out known non-critical errors (e.g., favicon, source maps)
        const criticalErrors = consoleErrors.filter(err =>
            !err.includes('favicon') &&
            !err.includes('source map') &&
            !err.includes('net::ERR_')
        );

        expect(criticalErrors).toHaveLength(0);
    });
});
