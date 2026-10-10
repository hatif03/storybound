// HTTP client. Relative URLs only (the app is served by the same FastAPI process; in dev Vite proxies /api).
// Every call retries gently on network trouble, because a child's tablet on wifi will drop now and then.
import type { Fixture, Lesson, StartRequest } from './types';
import { MOCK, mockFixtures, mockLessons, mockStart } from '../mock/mockApi';

export class ApiError extends Error {
  constructor(public code: string, message: string, public status = 0) { super(message); }
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Retries network failures and 5xx/429 (never 4xx) with a gentle back-off: 0.7 s, 1.8 s, 3.5 s. */
export async function withRetry<T>(fn: () => Promise<T>, tries = 3): Promise<T> {
  const waits = [700, 1800, 3500];
  for (let i = 0; ; i++) {
    try {
      return await fn();
    } catch (e) {
      const retryable = !(e instanceof ApiError) || e.status === 0 || e.status === 429 || e.status >= 500;
      if (!retryable || i >= tries) throw e;
      await sleep(waits[Math.min(i, waits.length - 1)]);
    }
  }
}

async function request(url: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(url, init);
  } catch {
    throw new ApiError('offline', 'No internet', 0);
  }
  if (!res.ok) {
    let code = 'internal';
    let message = 'Something went wrong';
    try {
      const body = await res.json();
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? message;
    } catch { /* body was not JSON */ }
    throw new ApiError(code, message, res.status);
  }
  return res;
}

/** Forget a story: the server deletes its pictures, narration, drawing and video. */
export async function forgetStory(storyId: string): Promise<void> {
  if (MOCK) return;
  await request(`/api/stories/${storyId}`, { method: 'DELETE' });
}

export type VideoStatus = { status: 'none' | 'making' | 'done' | 'failed'; seconds?: number };

export async function startVideo(storyId: string): Promise<VideoStatus> {
  if (MOCK) return { status: 'failed' };
  return (await request(`/api/stories/${storyId}/video`, { method: 'POST' })).json();
}

export async function getVideoStatus(storyId: string): Promise<VideoStatus> {
  if (MOCK) return { status: 'none' };
  return (await request(`/api/stories/${storyId}/video/status`)).json();
}

export const videoUrl = (storyId: string) => `/api/stories/${storyId}/video`;

export const getLessons = (): Promise<Lesson[]> =>
  MOCK ? Promise.resolve(mockLessons()) : withRetry(async () => (await request('/api/lessons')).json());

export const getFixtures = (): Promise<Fixture[]> =>
  MOCK ? Promise.resolve(mockFixtures()) : withRetry(async () => (await request('/api/fixtures')).json());

/** Start a story. Not retried on its own: a second POST would be a second (paid) story. */
export async function startStory(req: StartRequest): Promise<{ storyId: string }> {
  if (MOCK) return mockStart(req);
  const form = new FormData();
  form.set('lesson_id', req.lessonId);
  form.set('age', String(req.age));
  if (req.heroName) form.set('hero_name', req.heroName);
  for (const p of req.promises ?? []) form.append('promise', p);
  if (req.drawing.kind === 'fixture') form.set('fixture_id', req.drawing.id);
  else form.set('drawing', req.drawing.blob, req.drawing.name);
  const res = await request('/api/stories', { method: 'POST', body: form });
  const body = await res.json();
  return { storyId: body.story_id };
}
