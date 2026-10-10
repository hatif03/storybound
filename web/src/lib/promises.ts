// The oath has ~21 promises with parent-readable wording. A child gets seven sticker families instead (the six promise
// stickers made for the project, plus "polished"). Kid wording lives here; unknown promises fall back to their `title`.
import type { PromiseState } from '../state/storyReducer';

export type FamilyId = 'safe' | 'hero-name' | 'one-answer' | 'lesson' | 'pictures' | 'voice' | 'polished';

export interface Family { id: FamilyId; sticker: string; kid: string; grown: string }

export const FAMILIES: Family[] = [
  { id: 'safe', sticker: 'safe', kid: 'Safe and kind', grown: 'Safety' },
  { id: 'hero-name', sticker: 'hero-name', kid: 'Your hero on every page', grown: 'The hero' },
  { id: 'one-answer', sticker: 'one-answer', kid: 'One right answer', grown: 'The questions' },
  { id: 'lesson', sticker: 'lesson', kid: 'The lesson', grown: 'The lesson' },
  { id: 'polished', sticker: 'polished', kid: 'Easy words', grown: 'Reading level and variety' },
  { id: 'pictures', sticker: 'pictures', kid: 'Pictures of your hero', grown: 'The pictures' },
  { id: 'voice', sticker: 'voice', kid: 'Read aloud', grown: 'The voice' },
];

const FAMILY_OF: Record<string, FamilyId> = {
  input_safe_visual: 'safe', no_drawing_text_obedience: 'safe', story_safe_text: 'safe', original_character_only: 'safe',
  character_named_in_scene: 'hero-name', visual_trait_referenced: 'hero-name', card_traits_checkable: 'hero-name',
  schema_valid: 'one-answer', one_correct_choice: 'one-answer', correct_choice_position_balanced: 'one-answer', correct_choice_teaches_lesson: 'one-answer',
  lesson_concept_in_scene: 'lesson', lesson_alignment: 'lesson',
  age_reading_level: 'polished', no_repeated_scenario: 'polished',
  trait_in_image_prompt: 'pictures', illustration_present: 'pictures', image_matches_card: 'pictures',
  narration_present: 'voice',
};

export const familyOf = (id: string): FamilyId => FAMILY_OF[id] ?? (id.startsWith('lesson_specific') ? 'lesson' : 'polished');

/** Short child-friendly line for the promise that was just kept ("Pip checked: ..."). */
const KID: Record<string, string> = {
  input_safe_visual: 'Your drawing is safe to use', no_drawing_text_obedience: 'Words on a drawing are never obeyed',
  story_safe_text: 'Every page is safe and kind', original_character_only: 'Your hero is your own',
  character_named_in_scene: 'Your hero is on every page', visual_trait_referenced: 'Your hero looks like your drawing',
  card_traits_checkable: 'Pip noticed what your hero looks like', schema_valid: 'The story has eight pages',
  one_correct_choice: 'Each question has one right answer', correct_choice_position_balanced: 'The right answer moves around',
  correct_choice_teaches_lesson: 'The right answer shows the lesson', lesson_concept_in_scene: 'The lesson is on every page',
  lesson_alignment: 'The whole story teaches the lesson', age_reading_level: 'The words are easy to read',
  no_repeated_scenario: 'No page repeats another', trait_in_image_prompt: 'Pictures are asked to show your hero',
  illustration_present: 'Every page has a picture', image_matches_card: 'Pictures look like your hero', narration_present: 'Every page can be read aloud',
};
export const kidLine = (p: Pick<PromiseState, 'id' | 'title'>): string => KID[p.id] ?? p.title;

export interface FamilyView extends Family {
  promises: PromiseState[];
  kept: number;
  earned: boolean; // every promise that was checked is kept, and at least one was
  fixing: boolean;
  checking: boolean;
}

/** Group the oath into sticker families. Honest by construction: `earned` is false if anything in the family is not kept. */
export function familyViews(promises: PromiseState[], lessonTitle?: string): FamilyView[] {
  return FAMILIES.map((f) => {
    const ps = promises.filter((p) => familyOf(p.id) === f.id);
    const kept = ps.filter((p) => p.state === 'kept' || p.state === 'kept_after_fix').length;
    const settled = ps.filter((p) => p.state !== 'unchecked');
    const earned = settled.length > 0 && settled.every((p) => p.state === 'kept' || p.state === 'kept_after_fix') && kept > 0;
    return {
      ...f, kid: f.id === 'lesson' && lessonTitle ? lessonTitle : f.kid, promises: ps, kept, earned,
      fixing: ps.some((p) => p.state === 'fixing'), checking: ps.some((p) => p.state === 'checking'),
    };
  }).filter((f) => f.promises.length > 0);
}

/** Parent-facing label for a promise's final state. Text and icon, never colour alone. */
export const STATE_LABEL: Record<PromiseState['state'], string> = {
  kept: 'Kept', kept_after_fix: 'Kept after a rewrite', not_kept: 'Not kept', unchecked: 'Not checked this time',
  waiting: 'Waiting', checking: 'Being checked', fixing: 'Being fixed',
};
