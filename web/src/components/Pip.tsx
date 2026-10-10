// Pip the owl. Shows a still picture at once, then fades in the Rive animation when it has loaded. If Rive fails to load
// (or motion is reduced) the still stays: a missing animation is never an error.
import { lazy, Suspense, useState, type ReactNode } from 'react';
import { prefersCalm } from '../state/settings';
import crops from './pipCrops.json';

export type Pose =
  | 'happy' | 'wink' | 'cool' | 'love' | 'dizzy' | 'shocked' | 'daydream' | 'cupcake' | 'shy' | 'balloon' | 'bubble' | 'party' | 'cake'
  | 'check' | 'comfort' | 'paint' | 'read';

// Rive poses (the crying and angry owls, 03 and 08, are never shipped: not for a child's screen). The last four are still composites.
const RIVE: Record<string, string> = {
  happy: '01-happy-flap', wink: '02-wink', cool: '04-cool-sunglasses', love: '05-heart-eyes', dizzy: '06-dizzy-confused', shocked: '07-shocked',
  daydream: '09-hungry-daydream', cupcake: '10-party-cupcake', shy: '11-shy-giggle', balloon: '12-heart-balloon', bubble: '13-bubble-wand',
  party: '14-balloons-party', cake: '15-birthday-cake',
};

const Animated = lazy(() => import('./PipRive'));

export function Pip({ pose, className = '' }: { pose: Pose; className?: string }) {
  const [readyPose, setReady] = useState<string | null>(null); // per pose: a new pose shows its still until its own animation has loaded
  const [failedPose, setFailed] = useState<string | null>(null);
  const ready = readyPose === pose;
  const failed = failedPose === pose;
  const file: string | undefined = RIVE[pose];
  const still = file ? `/assets/pip/pip-${file}.webp` : `/assets/pip/pip-${pose}.webp`;
  const animate = !!file && !failed && !prefersCalm();
  return (
    <div className={`pip ${className}`} data-pose={pose} data-animated={ready ? 'true' : 'false'} aria-hidden="true">
      <img className="pip-still" src={still} alt="" draggable={false} />
      {animate && (
        <Suspense fallback={null}>
          <Animated key={pose} src={`/assets/pip/pip-${file}.riv`} crop={(crops as Record<string, { x: number; y: number; w: number; h: number }>)[`pip-${file}`]} onReady={() => setReady(pose)} onFail={() => setFailed(pose)} />
        </Suspense>
      )}
    </div>
  );
}

/** Pip with a speech bubble. The bubble text is real text, so screen readers get it. */
export function PipSays({ pose, children, className = '' }: { pose: Pose; children: ReactNode; className?: string }) {
  return (
    <div className={`pip-says ${className}`}>
      <div className="bubble">{children}</div>
      <Pip pose={pose} />
    </div>
  );
}
