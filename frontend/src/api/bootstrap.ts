import type { components } from './schema';

export type Bootstrap = components['schemas']['Bootstrap'];
type SessionResponse = components['schemas']['SessionResponse'];

export class BootstrapError extends Error {
  constructor(message: string, readonly kind: 'expired-session' | 'connection' | 'invalid-response') {
    super(message);
    this.name = 'BootstrapError';
  }
}

export interface BootstrapResult { bootstrap: Bootstrap; csrfToken: string | null }
let startupRequest: Promise<BootstrapResult> | undefined;

function isBootstrap(value: unknown): value is Bootstrap {
  if (!value || typeof value !== 'object') return false;
  const item = value as Record<string, unknown>;
  return item.api_version === 'v1'
    && (item.active_release_id == null || typeof item.active_release_id === 'string')
    && typeof item.has_baseline === 'boolean'
    && (item.capabilities === undefined || (Array.isArray(item.capabilities) && item.capabilities.every((x) => typeof x === 'string')));
}

function takeSessionSecret(): string | null {
  const secret = new URLSearchParams(location.hash.slice(1)).get('session');
  if (secret !== null) history.replaceState(history.state, '', `${location.pathname}${location.search}`);
  return secret;
}

async function readJson(response: Response): Promise<unknown> {
  try { return await response.json(); }
  catch { throw new BootstrapError('The local service returned an unreadable response.', 'invalid-response'); }
}

async function start(): Promise<BootstrapResult> {
  const secret = takeSessionSecret();
  let csrfToken: string | null = null;
  try {
    if (secret !== null) {
      const response = await fetch('/api/v1/session', {
        method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ secret }),
      });
      if (!response.ok) throw new BootstrapError('This launch link has expired or was already used.', 'expired-session');
      const session = await readJson(response) as Partial<SessionResponse>;
      if (typeof session.csrf_token !== 'string' || !session.csrf_token) {
        throw new BootstrapError('The local service returned an invalid session.', 'invalid-response');
      }
      csrfToken = session.csrf_token;
    }

    const response = await fetch('/api/v1/bootstrap', { credentials: 'same-origin' });
    if (response.status === 401 || response.status === 403) {
      throw new BootstrapError('Your local session is no longer available.', 'expired-session');
    }
    if (!response.ok) throw new BootstrapError('The local service could not load the workspace.', 'connection');
    const bootstrap = await readJson(response);
    if (!isBootstrap(bootstrap)) {
      throw new BootstrapError('The local service returned an unsupported bootstrap response.', 'invalid-response');
    }
    return { bootstrap, csrfToken };
  } catch (error) {
    if (error instanceof BootstrapError) throw error;
    throw new BootstrapError('Could not connect to the local Chesterfield service.', 'connection');
  }
}

/** One startup request per page load, including React StrictMode's development remount. */
export function loadBootstrap(): Promise<BootstrapResult> {
  startupRequest ??= start();
  return startupRequest;
}

export function resetBootstrapForTests(): void { startupRequest = undefined; }
