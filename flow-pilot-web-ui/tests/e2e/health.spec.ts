import { test, expect } from '@playwright/test';

/**
 * Health Check Tests
 * ===================
 * Verifies the FastAPI backend is reachable and responding.
 *
 * PREREQUISITES:
 *   - Backend running on localhost:8000
 */

const API_BASE = 'http://localhost:8000/api';

test.describe('Backend Health', () => {
    test('GET /api/health returns ok', async ({ request }) => {
        const response = await request.get(`${API_BASE}/health`);
        expect(response.ok()).toBeTruthy();
        const body = await response.json();
        expect(body.status).toBe('ok');
    });

    test('Root endpoint returns running message', async ({ request }) => {
        const response = await request.get('http://localhost:8000/');
        expect(response.ok()).toBeTruthy();
        const body = await response.json();
        expect(body.message).toContain('running');
    });

    test('OpenAPI docs are accessible', async ({ request }) => {
        const response = await request.get('http://localhost:8000/docs');
        expect(response.ok()).toBeTruthy();
    });
});
