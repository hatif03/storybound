// Phosphor icons (MIT) drawn with a CSS mask so they take the text colour. Always decorative: the control carries the label.
import type { CSSProperties } from 'react';

export type IconName = string;

export function Icon({ name, weight = 'fill', className = '' }: { name: IconName; weight?: 'fill' | 'bold'; className?: string }) {
  const url = `url(/assets/icons/${weight}/${name}.svg)`;
  return <span className={`icon ${className}`} aria-hidden="true" style={{ '--icon': url } as CSSProperties} />;
}
