/** @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/App';
import { BootstrapError } from '../src/api/bootstrap';

afterEach(cleanup);
const emptyResult = { bootstrap: { api_version: 'v1' as const, active_release_id: null, has_baseline: false, capabilities: [] }, csrfToken: null };

describe('application shell', () => {
  it('renders the truthful empty baseline state', async () => {
    render(<App bootstrapLoader={async () => emptyResult} />);
    expect(await screen.findByRole('heading', { name: 'No baseline release is active' })).toBeInTheDocument();
    expect(screen.getByText('No data tools are available in this workspace yet.')).toBeInTheDocument();
    expect(screen.getByText('None')).toBeInTheDocument();
  });
  it('explains how to recover an expired session', async () => {
    render(<App bootstrapLoader={async () => { throw new BootstrapError('Your local session is no longer available.', 'expired-session'); }} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('open the application again from the launcher');
  });
  it('supports arrow-key navigation and changes destinations on activation', async () => {
    const user = userEvent.setup(); render(<App bootstrapLoader={async () => emptyResult} />);
    await screen.findByRole('heading', { name: 'No baseline release is active' });
    const overview = screen.getByRole('button', { name: /County overview/ });
    const evidence = screen.getByRole('button', { name: /Evidence explorer/ });
    overview.focus(); await user.keyboard('{ArrowDown}{Enter}');
    expect(evidence).toHaveFocus();
    expect(screen.getByRole('heading', { name: 'Evidence explorer' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Evidence will appear with a release' })).toBeInTheDocument();
  });
  it('pins the initial release without loading again during navigation', async () => {
    const loader = vi.fn(async () => ({ bootstrap: { api_version: 'v1' as const, active_release_id: 'release_2026_09', has_baseline: true, capabilities: [] }, csrfToken: null }));
    const user = userEvent.setup(); render(<App bootstrapLoader={loader} />);
    expect((await screen.findAllByText('release_2026_09')).length).toBeGreaterThan(0);
    await user.click(screen.getByRole('button', { name: /Sources & changes/ }));
    await waitFor(() => expect(loader).toHaveBeenCalledTimes(1));
  });
});
