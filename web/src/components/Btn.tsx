import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Icon } from './Icon';
import { sfx } from '../lib/sound';

type Variant = 'sun' | 'sky' | 'leaf' | 'paper' | 'grape';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant; big?: boolean; icon?: string; iconAfter?: string; round?: boolean; quiet?: boolean; children?: ReactNode;
}

/** The sticker button: thick outline, hard shadow that squashes when pressed, at least 56 px tall (big: 80 px). */
export function Btn({ variant = 'sun', big, icon, iconAfter, round, quiet, children, className = '', onClick, ...rest }: Props) {
  return (
    <button
      type="button"
      className={`btn btn-${variant} ${big ? 'btn-big' : ''} ${round ? 'btn-round' : ''} ${className}`}
      onClick={(e) => { if (!quiet) sfx('tap'); onClick?.(e); }}
      {...rest}
    >
      {icon && <Icon name={icon} />}
      {children !== undefined && <span className="btn-label">{children}</span>}
      {iconAfter && <Icon name={iconAfter} />}
    </button>
  );
}
