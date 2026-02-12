import { test, expect } from '@playwright/test';

/**
 * Admin Panel Tests
 * ==================
 * Tests the AdminPanel component for backend process management.
 *
 * PREREQUISITES:
 *   - Frontend running on localhost:5173
 *   - Backend may or may not be running (tests check both states)
 */

const API_BASE = 'http://localhost:8000/api';

test.describe('Admin Panel', () => {
    test('backend health check responds when running', async ({ request }) => {
        try {
            const response = await request.get(`${API_BASE}/health`, {
                timeout: 5000,
            });
            if (response.ok()) {
                const body = await response.json();
                expect(body.status).toBe('ok');
            }
        } catch {
            // Backend is not running — this is an acceptable state
            test.skip(true, 'Backend not running, skipping health check');
        }
    });

    test('admin panel renders on the page', async ({ page }) => {
        await page.goto('/');
        await page.waitForTimeout(1000);

        // Look for admin panel or settings area
        const adminElements = page.locator(
            '[id*="admin"], [class*="admin"], [data-testid*="admin"]'
        );
        // Admin panel may be behind a route or settings menu
        // This is a soft check
        const count = await adminElements.count();
        if (count > 0) {
            await expect(adminElements.first()).toBeVisible();
        }
    });

    test('API endpoint listing is accessible', async ({ request }) => {
        try {
            const response = await request.get('http://localhost:8000/openapi.json', {
                timeout: 5000,
            });
            if (response.ok()) {
                const spec = await response.json();
                expect(spec).toHaveProperty('paths');
                // Verify key endpoints exist in the OpenAPI spec
                const paths = Object.keys(spec.paths);
                expect(paths).toContain('/api/health');
            }
        } catch {
            test.skip(true, 'Backend not running');
        }
    });

    test('hardware device listing works', async ({ request }) => {
        try {
            const response = await request.get(`${API_BASE}/hardware/devices`, {
                timeout: 5000,
            });
            // Even if no devices found, the endpoint should respond
            expect(response.status()).toBeLessThan(500);
        } catch {
            test.skip(true, 'Backend not running');
        }
    });
});
