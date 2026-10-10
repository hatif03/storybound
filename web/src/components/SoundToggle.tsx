import { Icon } from './Icon';
import { setSettings, useSettings } from '../state/settings';
import { setMusic, sfx, stop, unlock } from '../lib/sound';

/** Always-visible speaker button. Off by default; turning it on is itself a tap, so it also unlocks audio. */
export function SoundToggle() {
  const { sound, music } = useSettings();
  return (
    <button
      type="button"
      className="corner-btn"
      aria-pressed={sound}
      aria-label={sound ? 'Sound is on. Tap to turn sound off' : 'Sound is off. Tap to turn sound on'}
      onClick={() => {
        unlock();
        const next = !sound;
        setSettings({ sound: next, ...(next ? {} : { music: false }) });
        if (!next) { stop(); setMusic(false); } else { sfx('happy-chime'); if (music) setMusic(true); }
      }}
    >
      <Icon name={sound ? 'speaker-high' : 'speaker-slash'} />
    </button>
  );
}
