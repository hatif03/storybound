// What Pip says (and which pose Pip wears) for each step of the run. Pure, so the wording is easy to check.
import type { Pose } from '../components/Pip';
import type { StoryState } from '../state/storyReducer';

export function stepLine(s: StoryState): string {
  const { kind, index } = s.step;
  const name = s.card?.name;
  switch (kind) {
    case 'start':
    case 'looking': return 'Pip is looking at your drawing.';
    case 'meeting': return name ? `Pip is meeting ${name}!` : 'Pip is meeting your hero!';
    case 'promise': return 'Pip is writing a promise.';
    case 'planning': return 'Pip is planning the story.';
    case 'writing': return index ? `Pip is writing page ${index}.` : 'Pip is writing your story.';
    case 'checking': return index ? `Pip is checking page ${index}!` : 'Pip is checking your story!';
    // index 0 is a repair of the hero or the whole story, not of one page
    case 'fixing': return index ? `Pip is fixing page ${index}.` : 'Pip is polishing the whole story.';
    case 'painting': return 'Pip is painting your pictures.';
    case 'voice': return 'Pip is finding a voice.';
    case 'wrapping': return 'Almost done! Pip is tidying up.';
    case 'done': return 'Your story is ready!';
  }
}

/** Pip's voice line for the step, when one was recorded. */
export function stepVoice(s: StoryState): string | null {
  const { kind, index } = s.step;
  if (kind === 'looking') return 'making-look';
  if (kind === 'promise') return 'making-promise';
  if (kind === 'painting') return 'making-paint';
  if (kind === 'voice') return 'making-voice';
  if (kind === 'checking' && index && index <= 8) return `checking-page-${index}`;
  return null;
}

export function stepPose(s: StoryState): Pose {
  switch (s.step.kind) {
    case 'start':
    case 'looking': return 'wink';
    case 'meeting': return 'happy';
    case 'promise':
    case 'planning':
    case 'writing': return 'daydream';
    case 'checking': return 'check';
    case 'fixing': return 'cool';
    case 'painting': return 'paint';
    case 'voice': return 'bubble';
    case 'wrapping': return 'balloon';
    case 'done': return 'party';
  }
}
