import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';

const sessionUrl = process.env.CDT_SMOKE_URL;
if (!sessionUrl) throw new Error('CDT_SMOKE_URL must be supplied by scripts/smoke.py');
const origin = new URL(sessionUrl).origin;
const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 960 } });
  const requests = [];
  const errors = [];
  await context.route('**/*', route => {
    requests.push(route.request().url());
    if (new URL(route.request().url()).origin !== origin) return route.abort();
    return route.continue();
  });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(sessionUrl);
  await page.getByRole('heading', { name: 'No baseline release is active' }).waitFor();
  assert.equal(new URL(page.url()).hash, '');
  assert.equal(requests.filter(url => url.endsWith('/api/v1/session')).length, 1);
  assert(requests.every(url => new URL(url).origin === origin));
  assert.equal((await context.cookies()).find(c => c.name.startsWith('cdt_session_')).httpOnly, true);
  await page.screenshot({ path: process.env.CDT_SMOKE_SCREENSHOT, fullPage: true });
  await page.getByRole('button', { name: /County overview/ }).focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await page.getByRole('heading', { name: 'Evidence explorer', exact: true }).waitFor();
  await page.getByRole('heading', { name: 'Evidence will appear with a release' }).waitFor();
  await page.reload();
  await page.getByRole('heading', { name: 'No baseline release is active' }).waitFor();
  assert.equal(requests.filter(url => url.endsWith('/api/v1/session')).length, 1);
  await context.setOffline(true);
  await page.getByRole('button', { name: /Research desk/ }).click();
  await page.getByRole('heading', { name: 'Research tools are not available yet' }).waitFor();
  await page.setViewportSize({ width: 390, height: 844 });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  await context.close();
  const unauthenticated = await browser.newPage();
  await unauthenticated.goto(origin);
  await unauthenticated.getByRole('alert').waitFor();
  assert.equal((await unauthenticated.request.get(origin + '/api/v1/bootstrap')).status(), 401);
  assert.equal(errors.length, 0, errors.join('\n'));
  console.log('Browser smoke passed: session, reload, empty states, keyboard, narrow viewport, offline navigation, local-only requests, unauthenticated denial.');
} finally {
  await browser.close();
}
