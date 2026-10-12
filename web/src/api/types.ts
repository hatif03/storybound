// Shapes of the HTTP + server-sent-events contract (docs/API.md) as the backend (src/storybound/api.py, pipeline.py) really sends them.
// Where API.md and the backend differ, the backend wins; differences are marked "backend:".

export interface Lesson { id: string; title: string; blurb: string; icon: string }

// kind: backend sends benign | edge | synthetic | demo-unsafe | demo-text
export interface Fixture { id: string; label: string; url: string; kind: string }

export interface CharacterCard { name: string; species: string; traits: string[]; palette: string[]; one_line: string }

export type CommitScope = 'run' | 'story' | 'scene' | 'image' | 'audio';
export interface Commitment {
  id: string; scope: CommitScope; title: string; plain: string; core: boolean;
  verifier: 'deterministic' | 'judge' | 'both';
}

export interface Choice { id: string; text: string; feedback: string; is_correct: boolean }
export interface Page {
  index: number; scenario: string; question: string; choices: Choice[]; image_prompt: string; narration_text: string;
}

export type VerdictStatus = 'pass' | 'warning' | 'violation' | 'critical' | 'skipped' | 'verification_error';
export interface Verdict {
  commitment: string; scope: string; // "run" | "story" | "scene 5" | "image 5" | "audio 5"
  status: VerdictStatus; attempt: number; expected?: string; actual?: string; verdict_by?: string; cover?: string;
}

export interface Degradation { what: 'image' | 'audio' | 'judge' | 'check' | string; index?: number; why: string; fallback: string }

export interface Receipt {
  story_id: string; oath_hash: string; arm: string; plain: string;
  // backend: counts has `checked` as well as the API.md fields
  counts: { commitments: number; checked?: number; checks: number; violations_found: number; repairs: number; kept: number; shipped_violations: number; judge_enabled?: boolean };
  broken?: string[]; // backend: ids of promises that were not fully kept
  pages: { index: number; attempts: number; final: 'pass' | 'noted' | string }[];
  coverage: { pct: number; uncovered: string[] };
  degradations: Degradation[];
  ignored_drawing_text: string[];
  // backend: usd_estimate (+ estimate: true) rather than API.md's `usd`; more fields than API.md lists
  budget: { usd?: number; usd_estimate?: number; estimate?: boolean; seconds: number; tokens_in: number; tokens_out: number; images?: number; calls?: number; by_model?: Record<string, unknown> };
  prompt_version?: string; models?: Record<string, string>;
  trace_id: string; generated_at: string;
}

export interface QuizOption { id: string; text: string; is_correct: boolean }
export interface QuizItem {
  index: number; kind: 'recall' | 'detail' | 'feeling' | 'lesson'; question: string; options: QuizOption[];
  evidence_page: number; evidence_quote: string; explain: string;
}
export interface Quiz { items: QuizItem[]; talk_about: string }

export type SafetyAction = 'proceed' | 'sanitise' | 'refuse' | 'ask_redraw';

// Every event on the wire: { id, type, t, data }  (backend: `id` is the Last-Event-ID; API.md does not list it)
export type StoryEvent =
  | { id?: number; t: number; type: 'run.started'; data: { story_id: string; arm: string; lesson_id: string; age: number; seed: string; input_hash: string } }
  | { id?: number; t: number; type: 'safety.result'; data: { tier: 'none' | 'A' | 'B'; action: SafetyAction; ignored_text: string[]; reason_code: string } }
  | { id?: number; t: number; type: 'character.ready'; data: { card: CharacterCard } }
  | { id?: number; t: number; type: 'oath.ready'; data: { oath_hash: string; commitments: Commitment[]; added?: string[]; rejected?: string[] } }
  | { id?: number; t: number; type: 'plan.ready'; data: { beats: string[] } }
  | { id?: number; t: number; type: 'scene.started'; data: { index: number; attempt: number } }
  | { id?: number; t: number; type: 'verdict'; data: Verdict }
  // backend: index 0 means a run-level or whole-story repair, not a page
  | { id?: number; t: number; type: 'scene.repair'; data: { index: number; attempt: number; failed: string[]; because: string } }
  | { id?: number; t: number; type: 'scene.accepted'; data: { index: number; attempts_used: number; page: Page } }
  // every page is final (the whole-story check is done): from here on the app may release pages whose picture and voice are ready
  | { id?: number; t: number; type: 'story.verified'; data: Record<string, never> }
  | { id?: number; t: number; type: 'image.ready'; data: { index: number; url: string; verdict: string } }
  | { id?: number; t: number; type: 'audio.ready'; data: { index: number; url: string; seconds: number } }
  | { id?: number; t: number; type: 'quiz.ready'; data: Quiz }
  | { id?: number; t: number; type: 'paint.plan'; data: { painted: number[]; importance: Record<string, number>; budget_usd: number } }
  | { id?: number; t: number; type: 'degraded'; data: Degradation }
  | { id?: number; t: number; type: 'receipt'; data: Receipt }
  | { id?: number; t: number; type: 'run.finished'; data: { outcome: 'shipped' | 'shipped_with_notes'; story_id: string } }
  | { id?: number; t: number; type: 'run.refused'; data: { reason_code: string; message: string; trace_id: string } }
  | { id?: number; t: number; type: 'error'; data: { code: string; message: string } };

export type EventType = StoryEvent['type'];
export const EVENT_TYPES: EventType[] = [
  'run.started', 'safety.result', 'character.ready', 'oath.ready', 'plan.ready', 'scene.started', 'verdict', 'scene.repair',
  'scene.accepted', 'story.verified', 'image.ready', 'audio.ready', 'quiz.ready', 'paint.plan', 'degraded', 'receipt', 'run.finished', 'run.refused', 'error',
];

export interface StartRequest {
  lessonId: string; age: number; heroName?: string; promises?: string[]; pictures?: 'full' | 'half' | 'none' | 'auto';
  drawing: { kind: 'file'; blob: Blob; name: string } | { kind: 'fixture'; id: string };
}
