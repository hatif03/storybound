// Ten crayons + an eraser. Hex values match the recoloured crayon pictures made by scripts/copy-assets.py.
// Crayons are told apart by position and by the lifted, ringed one, never by colour alone.
export const CRAYONS = [
  { id: 'black', name: 'Black', hex: '#2B2B2B' },
  { id: 'brown', name: 'Brown', hex: '#8A5A2B' },
  { id: 'red', name: 'Red', hex: '#E53935' },
  { id: 'orange', name: 'Orange', hex: '#F58A07' },
  { id: 'yellow', name: 'Yellow', hex: '#FFD21F' },
  { id: 'green', name: 'Green', hex: '#4CC35A' },
  { id: 'sky', name: 'Sky blue', hex: '#29A8E8' },
  { id: 'blue', name: 'Blue', hex: '#2F55D4' },
  { id: 'purple', name: 'Purple', hex: '#8E4FD8' },
  { id: 'pink', name: 'Pink', hex: '#FF6FA5' },
] as const;

export const ERASER = { id: 'eraser', name: 'Eraser', hex: '#FFFFFF' } as const;

// Brush widths in canvas pixels (the canvas is 1024 wide), shown as three dots.
export const BRUSHES = [
  { id: 's', name: 'Thin', px: 8, dot: 10 },
  { id: 'm', name: 'Medium', px: 18, dot: 20 },
  { id: 'l', name: 'Thick', px: 36, dot: 34 },
] as const;
