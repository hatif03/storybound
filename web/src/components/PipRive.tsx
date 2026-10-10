// Pip as a Rive animation. Loaded lazily (the Rive runtime is the one heavy part) and fully self-hosted: both wasm files
// come from our own bundle, and the runtime's default CDN fallback is switched off, so there are no outside requests.
import { RuntimeLoader, useRive } from '@rive-app/react-canvas';
import wasmUrl from '@rive-app/canvas/rive.wasm?url';
import wasmFallbackUrl from '@rive-app/canvas/rive_fallback.wasm?url';

RuntimeLoader.setWasmUrl(wasmUrl);
RuntimeLoader.setWasmFallbackUrl(wasmFallbackUrl);

// Every Pip .riv has one artboard (500x500) and one looping "State Machine 1" with no inputs (see docs/WEB.md).
// `crop` is where the owl sits inside the 500x500 artboard (measured by scripts/inspect-rive.mjs --bounds), so the animation is
// drawn the same size as the still picture it replaces.
export interface Crop { x: number; y: number; w: number; h: number }

export default function PipRive({ src, crop, onReady, onFail }: { src: string; crop?: Crop; onReady: () => void; onFail: () => void }) {
  const { RiveComponent } = useRive({ src, stateMachines: 'State Machine 1', autoplay: true, onLoad: onReady, onLoadError: onFail });
  const s = crop ? Math.max(crop.w, crop.h) * 1.1 : 0.5;
  const cx = crop ? crop.x + crop.w / 2 : 0.5;
  const cy = crop ? crop.y + crop.h / 2 : 0.5;
  const size = 100 / s;
  return (
    <div className="pip-rive" aria-hidden="true" style={{ width: `${size}%`, height: `${size}%`, left: `${50 - cx * size}%`, top: `${50 - cy * size}%` }}>
      <RiveComponent />
    </div>
  );
}
