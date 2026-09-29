// Robot model → product card image. Images are loaded at runtime from the public product site
// (never bundled); <RobotImage> falls back to a drawn illustration when a URL fails or nothing matches.
// Lookup: exact modelTypeCode first, then case-insensitive keywords in displayName / modelTypeCode.
// Codes seen on the test tenant (2026-09-29), all confirmed by the owner: M4 → Mira, M6 → Marvel,
// SW1 / SW3 → Beetle, Scrubber 50H / Scrubber 50 MD → Omnie, Scrubber S1 → Phantas, VC 40 → Vacuum 40.
// "Whiz V" is deliberately unmapped (generic illustration).

export type RobotModel = { key: string; name: string; image: string }

const IMG = 'https://gausium.com/wp-content/uploads'
const MODELS: Record<string, RobotModel> = {
  beetle: { key: 'beetle', name: 'Beetle', image: `${IMG}/2024/11/Beetle-Pro-card-1-560x365.png` },
  phantas: { key: 'phantas', name: 'Phantas', image: `${IMG}/2022/04/phantas-v1.3-card-560x365.png` },
  mira: { key: 'mira', name: 'Mira', image: `${IMG}/2026/04/mira-card-560x365.webp` },
  marvel: { key: 'marvel', name: 'Marvel', image: `${IMG}/2026/04/marvel-2-560x365.webp` },
  omnie: { key: 'omnie', name: 'Omnie', image: `${IMG}/2024/12/omnie-roller-card-560x365.png` },
  scrubber75: { key: 'scrubber75', name: 'Scrubber 75', image: `${IMG}/2022/04/SC75-V4.2-card-1-560x365.png` },
  phanshop: { key: 'phanshop', name: 'PhanShop', image: `${IMG}/2025/11/phanshop-card-2-560x365.png` },
  vacuum40: { key: 'vacuum40', name: 'Vacuum 40', image: `${IMG}/2022/04/40-v1.6-card-1-560x365.png` },
}

/** Exact upstream modelTypeCode (case-insensitive) → model. Only owner-confirmed codes belong here. */
const BY_CODE: Record<string, string> = {
  'm4': 'mira', 'm6': 'marvel',
  'sw1': 'beetle', 'sw3': 'beetle',
  'scrubber 50h': 'omnie', 'scrubber 50 md': 'omnie',
  'scrubber s1': 'phantas',
  'vc 40': 'vacuum40',
}

/** Ordered keyword rules (first hit wins); matched as whole words against lower-cased text. */
const KEYWORDS: [RegExp, string][] = [
  [/\bphanshop\b/, 'phanshop'],
  [/\bphantas\b/, 'phantas'],
  [/\bbeetle\b/, 'beetle'],
  [/\bomnie\b/, 'omnie'],
  [/\bmira\b/, 'mira'],
  [/\bmarvel\b/, 'marvel'],
  [/\b(scrubber|sc) ?75\b/, 'scrubber75'],
  [/\b(vacuum|vc) ?40\b/, 'vacuum40'],
]

export function robotModel(info: { modelTypeCode?: unknown; displayName?: unknown } | null | undefined): RobotModel | null {
  if (!info) return null
  const code = typeof info.modelTypeCode === 'string' ? info.modelTypeCode.trim() : ''
  const exact = BY_CODE[code.toLowerCase()]
  if (exact) return MODELS[exact]
  const text = [info.displayName, code].filter(v => typeof v === 'string').join(' ').toLowerCase()
  for (const [pattern, key] of KEYWORDS) if (pattern.test(text)) return MODELS[key]
  return null
}
