import { useEffect, useId, useRef, useState } from 'react';
import { BootstrapError, loadBootstrap, type BootstrapResult } from './api/bootstrap';

const destinations = [
  { id: 'overview', label: 'County overview', eyebrow: 'Public baseline' },
  { id: 'evidence', label: 'Evidence explorer', eyebrow: 'Claims and sources' },
  { id: 'research', label: 'Research desk', eyebrow: 'Private workspace' },
  { id: 'sources', label: 'Sources & changes', eyebrow: 'Release register' },
] as const;
type Destination = (typeof destinations)[number]['id'];
type LoadState = { status: 'loading' } | { status: 'ready'; result: BootstrapResult } | { status: 'error'; error: BootstrapError };

const emptyCopy: Record<Destination, [string, string]> = {
  overview: ['No baseline release is active', 'The county overview will appear after a reviewed baseline is sealed and explicitly activated.'],
  evidence: ['Evidence will appear with a release', 'Claims, source excerpts, uncertainty, and limitations stay unavailable until a baseline is active.'],
  research: ['Research tools are not available yet', 'Private briefs and scenarios will open when the local service reports those capabilities.'],
  sources: ['No source register is available', 'Source history and release changes will appear here when those capabilities are implemented.'],
};

function EmptyState({ destination }: { destination: Destination }) {
  const [title, text] = emptyCopy[destination];
  return <section className="empty-card" aria-labelledby="empty-title">
    <div className="empty-mark" aria-hidden="true">○</div><p className="kicker">Workspace status</p>
    <h2 id="empty-title">{title}</h2><p>{text}</p>
    <div className="empty-note"><span>Unknown remains unknown</span><p>No county values are shown until they have a pinned release and inspectable evidence.</p></div>
  </section>;
}

function Nav({ active, onSelect }: { active: Destination; onSelect: (id: Destination) => void }) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  function keyNav(index: number, event: React.KeyboardEvent<HTMLButtonElement>) {
    let next: number | undefined;
    if (event.key === 'ArrowDown' || event.key === 'ArrowRight') next = (index + 1) % destinations.length;
    if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') next = (index - 1 + destinations.length) % destinations.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = destinations.length - 1;
    if (next !== undefined) { event.preventDefault(); refs.current[next]?.focus(); }
  }
  return <nav aria-label="Primary" className="primary-nav">{destinations.map((item, index) =>
    <button key={item.id} ref={(node) => { refs.current[index] = node; }} className={active === item.id ? 'nav-item active' : 'nav-item'}
      aria-current={active === item.id ? 'page' : undefined} onClick={() => onSelect(item.id)} onKeyDown={(e) => keyNav(index, e)}>
      <span>{item.label}</span><small>{item.eyebrow}</small>
    </button>)}</nav>;
}

export function App({ bootstrapLoader = loadBootstrap }: { bootstrapLoader?: () => Promise<BootstrapResult> }) {
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [active, setActive] = useState<Destination>('overview');
  const titleId = useId();
  useEffect(() => {
    let current = true;
    bootstrapLoader().then(
      (result) => { if (current) setState({ status: 'ready', result }); },
      (reason: unknown) => { if (current) setState({ status: 'error', error: reason instanceof BootstrapError ? reason : new BootstrapError('Could not open the local workspace.', 'connection') }); },
    );
    return () => { current = false; };
  }, [bootstrapLoader]);
  const section = destinations.find((item) => item.id === active)!;
  const release = state.status === 'ready' ? state.result.bootstrap.active_release_id ?? null : null;

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">CT</span><div><strong>CHESTERFIELD</strong><small>County observatory</small></div></div>
      <Nav active={active} onSelect={setActive} />
      <div className="privacy-note"><span aria-hidden="true">◆</span><div><strong>Local workspace</strong><small>Private by design</small></div></div>
    </aside>
    <main className="workspace" aria-labelledby={titleId}>
      <header className="topbar"><div className="connection"><span className={`status-dot ${state.status}`} aria-hidden="true" /><span>{state.status === 'ready' ? 'Local service connected' : state.status === 'loading' ? 'Connecting to local service' : 'Local service unavailable'}</span></div>
        <div className="release-status"><span>PINNED RELEASE</span><strong>{release ?? 'None'}</strong></div></header>
      <div className="page"><div className="page-heading"><div><p className="kicker">{section.eyebrow}</p><h1 id={titleId}>{section.label}</h1></div><span className="availability">Not available yet</span></div>
        {state.status === 'loading' && <section className="state-card" aria-live="polite" aria-busy="true"><div className="spinner" aria-hidden="true" /><h2>Opening the local workspace</h2><p>Checking the session and reading the pinned release state.</p></section>}
        {state.status === 'error' && <section className="state-card error" role="alert"><p className="kicker">Connection required</p><h2>{state.error.message}</h2><p>{state.error.kind === 'expired-session' ? 'Close this page and open the application again from the launcher to start a fresh local session.' : 'Confirm the Chesterfield service is running, then reopen the application from its launcher.'}</p></section>}
        {state.status === 'ready' && <>{state.result.bootstrap.has_baseline && release
          ? <section className="state-card"><p className="kicker">Release pinned for this view</p><h2>Workspace data views are still being prepared</h2><p>Release <code>{release}</code> is fixed for this page. This shell does not request unimplemented county data.</p></section>
          : <EmptyState destination={active} />}
          <section className="capabilities" aria-labelledby="capabilities-title"><div><p className="kicker">Workspace</p><h2 id="capabilities-title">Available tools</h2></div>
            <p>{state.result.bootstrap.capabilities?.length ? 'Additional tools are available, and their views will appear as they are connected.' : 'No data tools are available in this workspace yet.'}</p></section></>}
      </div>
    </main>
  </div>;
}
