/** @vitest-environment jsdom */
import { afterEach, expect, it, vi } from 'vitest';
import { loadBootstrap, resetBootstrapForTests } from '../src/api/bootstrap';

afterEach(() => { vi.unstubAllGlobals(); resetBootstrapForTests(); history.replaceState(null, '', '/'); });
it('removes and exchanges the fragment secret only once', async () => {
  history.replaceState(null, '', '/#session=single-use-secret');
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({ csrf_token: 'csrf-value' }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ api_version: 'v1', active_release_id: null, has_baseline: false, capabilities: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
  vi.stubGlobal('fetch', fetchMock);
  const first = loadBootstrap(); const second = loadBootstrap();
  expect(location.hash).toBe('');
  await expect(first).resolves.toMatchObject({ csrfToken: 'csrf-value' });
  await expect(second).resolves.toMatchObject({ csrfToken: 'csrf-value' });
  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/session');
  expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ secret: 'single-use-secret' }));
});
it('rejects a malformed bootstrap payload', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ api_version: 'v1', active_release_id: null }), { status: 200, headers: { 'Content-Type': 'application/json' } })));
  await expect(loadBootstrap()).rejects.toMatchObject({ kind: 'invalid-response' });
});
