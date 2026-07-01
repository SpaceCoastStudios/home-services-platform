// Small hex color helpers used to derive brand accent shades (tint / ink / hover)
// from a business's single brand_color, per the current light/dark theme.
// No dependency needed — this is just linear RGB interpolation.

export function hexToRgb(hex) {
  const clean = (hex || '').replace('#', '')
  const full = clean.length === 3 ? clean.split('').map((c) => c + c).join('') : clean
  const n = parseInt(full || '2563eb', 16)
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 }
}

export function mixHex(hex, target, amount) {
  const a = hexToRgb(hex)
  const b = hexToRgb(target)
  const r = Math.round(a.r + (b.r - a.r) * amount)
  const g = Math.round(a.g + (b.g - a.g) * amount)
  const bl = Math.round(a.b + (b.b - a.b) * amount)
  return `rgb(${r}, ${g}, ${bl})`
}

export const DEFAULT_BRAND = '#2563eb'

/**
 * Derives the accent shades used throughout the dashboard from one brand hex:
 *  - brand: the color itself (buttons, active nav, focus rings)
 *  - brandHover: a slightly darker variant for hover states
 *  - brandTint: a light/translucent variant for icon-chip and selection backgrounds
 *  - brandInk: a readable dark/light variant for text or icons sitting on brandTint
 * Tint/ink mix targets flip between white and black depending on theme so the
 * chips read correctly on both a light and a dark card surface.
 */
export function computeBrandTokens(hex, theme) {
  const brand = hex || DEFAULT_BRAND
  if (theme === 'dark') {
    return {
      brand,
      brandHover: mixHex(brand, '#ffffff', 0.15),
      brandTint: mixHex(brand, '#000000', 0.72),
      brandInk: mixHex(brand, '#ffffff', 0.3),
    }
  }
  return {
    brand,
    brandHover: mixHex(brand, '#000000', 0.15),
    brandTint: mixHex(brand, '#ffffff', 0.87),
    brandInk: mixHex(brand, '#000000', 0.35),
  }
}
