import { MOCK, MOCK_SPEED } from '../mock/mockApi';

/** Small, unobtrusive label shown only in demo mode. */
export function DemoBadge() {
  if (!MOCK) return null;
  return <div className="demo-badge" role="note">Demo mode{MOCK_SPEED !== 1 ? ` · ${MOCK_SPEED}× speed` : ''}</div>;
}
