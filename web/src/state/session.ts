// Which screen the child is on, and what they have chosen so far. All of it lives in memory only: a drawing is never stored.
import { useEffect, useRef } from 'react';

export type Screen = 'welcome' | 'draw' | 'name' | 'lesson' | 'making' | 'reader' | 'quiz' | 'order' | 'end' | 'refusal' | 'grownups';

export type Source =
  | { kind: 'canvas'; blob: Blob; url: string }
  | { kind: 'photo'; blob: Blob; url: string }
  | { kind: 'sample'; id: string; url: string; label: string; fkind: string };

export interface Choices { source: Source | null; heroName: string; lessonId: string | null }

/** Move focus to the screen's heading when it appears, so screen-reader and keyboard users land in the right place. */
export function useFocusHeading<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useEffect(() => { ref.current?.focus({ preventScroll: true }); }, []);
  return ref;
}

export function releaseSource(s: Source | null) {
  if (s && s.kind !== 'sample') URL.revokeObjectURL(s.url);
}
