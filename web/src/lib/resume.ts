// The story in progress, remembered for this tab only (sessionStorage; gone when the tab closes), so a reload picks it back up.
// Only the story's id and the lesson's title are kept: the story itself stays on the server, and Forget deletes both.
const KEY = 'storybound.active';

export interface Active { storyId: string; lessonTitle?: string }

export function saveActive(a: Active): void { try { sessionStorage.setItem(KEY, JSON.stringify(a)); } catch { /* storage blocked */ } }
export function clearActive(): void { try { sessionStorage.removeItem(KEY); } catch { /* storage blocked */ } }
export function loadActive(): Active | null {
  try {
    const a = JSON.parse(sessionStorage.getItem(KEY) ?? 'null') as Active | null;
    return a && typeof a.storyId === 'string' && /^[A-Za-z0-9_-]{4,64}$/.test(a.storyId) ? { storyId: a.storyId, lessonTitle: typeof a.lessonTitle === 'string' ? a.lessonTitle.slice(0, 80) : undefined } : null;
  } catch { return null; }
}
