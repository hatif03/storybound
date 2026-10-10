import { Icon } from './Icon';
import type { StoryState } from '../state/storyReducer';

export type StoneState = 'done' | 'current' | 'fixing' | 'waiting';

export function stoneState(s: StoryState, i: number): StoneState {
  const accepted = s.pages.some((p) => p.index === i);
  if (s.step.index === i && s.step.kind === 'fixing') return 'fixing';
  if (accepted) return 'done';
  if (s.step.index === i && (s.step.kind === 'writing' || s.step.kind === 'checking')) return 'current';
  return 'waiting';
}

const WORDS: Record<StoneState, string> = { done: 'ready', current: 'being made', fixing: 'being polished', waiting: 'coming soon' };

/** Eight stepping stones, one per page. They light up only when the page really exists. Never a score. */
export function Stones({ story, active, onPick }: { story: StoryState; active?: number; onPick?: (i: number) => void }) {
  const n = story.totalPages;
  return (
    <ol className="stones" aria-label="Pages of your story">
      {Array.from({ length: n }, (_, k) => k + 1).map((i) => {
        const st = stoneState(story, i);
        const label = `Page ${i}: ${WORDS[st]}`;
        const inner = st === 'done' ? <Icon name="star" /> : st === 'fixing' ? <Icon name="sparkle" /> : <span>{i}</span>;
        return (
          <li key={i}>
            {onPick && st === 'done' ? (
              <button type="button" className={`stone stone-${st}`} data-active={active === i} aria-label={label} aria-current={active === i ? 'page' : undefined} onClick={() => onPick(i)}>{inner}</button>
            ) : (
              <span className={`stone stone-${st}`} data-active={active === i} role="img" aria-label={label}>{inner}</span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
