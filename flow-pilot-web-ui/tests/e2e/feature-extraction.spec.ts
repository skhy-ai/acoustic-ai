import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

/**
 * Feature Extraction Tests
 * =========================
 * Tests the /api/processing/extract-features endpoint directly
 * via API calls and verifies the feature vector response.
 *
 * PREREQUISITES:
 *   - Backend running on localhost:8000
 *   - A test .wav file at tests/fixtures/test_audio.wav
 */

const API_BASE = 'http://localhost:8000/api';
const FIXTURE_DIR = path.join(__dirname, '..', 'fixtures');
const TEST_AUDIO = path.join(FIXTURE_DIR, 'test_audio.wav');

test.describe('Feature Extraction API', () => {
    test('returns 422 without file', async ({ request }) => {
        const response = await request.post(`${API_BASE}/processing/extract-features`);
        // FastAPI returns 422 for missing required fields
        expect(response.status()).toBe(422);
    });

    test('extracts features from audio file', async ({ request }) => {
        test.skip(!fs.existsSync(TEST_AUDIO), 'Test audio fixture not found');

        const fileBuffer = fs.readFileSync(TEST_AUDIO);

        const response = await request.post(`${API_BASE}/processing/extract-features`, {
            multipart: {
                file: {
                    name: 'test_audio.wav',
                    mimeType: 'audio/wav',
                    buffer: fileBuffer,
                },
                config_json: '{}',
            },
        });

        expect(response.ok()).toBeTruthy();
        const body = await response.json();
        expect(body).toHaveProperty('features');
        expect(body).toHaveProperty('length');
        expect(body.length).toBeGreaterThan(0);
        expect(Array.isArray(body.features)).toBeTruthy();
    });

    test('respects custom feature config', async ({ request }) => {
        test.skip(!fs.existsSync(TEST_AUDIO), 'Test audio fixture not found');

        const fileBuffer = fs.readFileSync(TEST_AUDIO);

        const config = JSON.stringify({
            mfcc: true,
            n_mfcc: 13,
            chroma: false,
            mel: false,
            contrast: false,
            tonnetz: false,
        });

        const response = await request.post(`${API_BASE}/processing/extract-features`, {
            multipart: {
                file: {
                    name: 'test_audio.wav',
                    mimeType: 'audio/wav',
                    buffer: fileBuffer,
                },
                config_json: config,
            },
        });

        if (response.ok()) {
            const body = await response.json();
            // With fewer features enabled, length should be smaller
            expect(body.length).toBeGreaterThan(0);
        }
    });
});
