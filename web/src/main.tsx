import { Component, StrictMode, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { applyToDocument } from './state/settings';
import './styles/tokens.css';
import './styles/fonts.css';
import './styles/base.css';
import './styles/screens.css';
import './styles/grownup.css';

applyToDocument();
window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener?.('change', applyToDocument);

// A last safety net: if something unexpected breaks, the child sees a soft message and a way back, never a blank page or a stack trace.
class Safety extends Component<{ children: ReactNode }, { broke: boolean }> {
  state = { broke: false };
  static getDerivedStateFromError() { return { broke: true }; }
  render() {
    if (!this.state.broke) return this.props.children;
    return (
      <main className="screen softfail">
        <h1>Oops, Pip dropped a page. One moment!</h1>
        <button type="button" className="btn btn-sun btn-big" onClick={() => location.reload()}><span className="btn-label">Start again</span></button>
      </main>
    );
  }
}

createRoot(document.getElementById('root')!).render(<StrictMode><Safety><App /></Safety></StrictMode>);
