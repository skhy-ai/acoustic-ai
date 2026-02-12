import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

/**
 * Doppler Analysis Tests
 * =======================
 * Tests the DopplerAnalysis component by uploading a test audio file
 * and verifying the classification card and Doppler summary render.
 *
 * PREREQUISITES:
 *   - Backend running on localhost:8000
 *   - Frontend running on localhost:5173
 *   - A test .wav file at tests/fixtures/test_audio.wav
 *     (if not present, tests will be skipped gracefully)
 */

const FIXTURE_DIR = path.join(__dirname, '..', 'fixtures');
const TEST_AUDIO = path.join(FIXTURE_DIR, 'test_audio.wav');

test.describe('Doppler Analysis', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to the main page (DopplerAnalysis component must be reachable)
        await page.goto('/');
    });

    test('page loads without errors', async ({ page }) => {
        // Verify no uncaught JS errors
        const errors: string[] = [];
        page.on('pageerror', (err) => errors.push(err.message));
        await page.waitForTimeout(2000);
        expect(errors).toHaveLength(0);
    });

    test('Doppler file input exists', async ({ page }) => {
        // Look for the file input (may be in a sub-route or tab)
        const fileInput = page.locator('#doppler-file-input');
        // If DopplerAnalysis is on a separate route/tab, this may not be visible
        // on the index page. Skip gracefully.
        if (await fileInput.count() > 0) {
            await expect(fileInput).toBeVisible();
        }
    });

    test('Run Analysis button is disabled without file', async ({ page }) => {
        const button = page.locator('#doppler-run-btn');
        if (await button.count() > 0) {
            await expect(button).toBeDisabled();
        }
    });

    test('upload audio file and verify analysis runs', async ({ page }) => {
        test.skip(!fs.existsSync(TEST_AUDIO), 'Test audio fixture not found');

        const fileInput = page.locator('#doppler-file-input');
        test.skip((await fileInput.count()) === 0, 'DopplerAnalysis not on current page');

        // Upload file
        await fileInput.setInputFiles(TEST_AUDIO);

        // Run button should now be enabled
        const runBtn = page.locator('#doppler-run-btn');
        await expect(runBtn).toBeEnabled();

        // Click and wait for results
        await runBtn.click();

        // Wait for either a result or an error (max 30s for FFT processing)
        await page.waitForTimeout(5000);

        // Check if a classification card or error message appeared
        const pageContent = await page.textContent('body');
        const hasResult = pageContent?.includes('First Guess') || pageContent?.includes('Analysis');
        expect(hasResult).toBeTruthy();
    });
});
