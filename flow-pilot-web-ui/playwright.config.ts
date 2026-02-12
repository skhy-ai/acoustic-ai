import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for Acoustic AI E2E Tests
 * ===================================================
 *
 * PREREQUISITES:
 *   1. Backend running: `source ../activate.sh && acoustic-ai-start`
 *   2. Frontend running: `npm run dev`
 *   3. Playwright installed: `npx playwright install --with-deps`
 *
 * RUN:
 *   npx playwright test            # headless
 *   npx playwright test --headed   # visible browser
 *   npx playwright test --ui       # interactive UI
 */
export default defineConfig({
    testDir: './tests/e2e',
    fullyParallel: false,            // tests may depend on backend state
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: 1,
    reporter: 'html',

    use: {
        baseURL: 'http://localhost:5173',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],

    /* Start frontend dev server before tests if not already running */
    webServer: [
        {
            command: 'npm run dev',
            url: 'http://localhost:5173',
            reuseExistingServer: true,
            timeout: 30_000,
        },
    ],
});
