# Saodi H5

Mobile web client for the Saodi agent (chat, robot list and robot details). Requires Node.js 18+. Run from `h5/`:

```sh
npm install
npm run dev          # Vite dev server, proxies /api to http://127.0.0.1:8000
npm run typecheck
npm run i18n:check   # dictionary key/placeholder parity + no hard-coded CJK outside src/i18n
npm run build        # runs i18n:check, then builds
npm run preview
```

`npm run build` empties and writes `../src/gs_openapi/server/static/` inside the Python package, so the HTTP server serves the page and assets from the same origin. The app uses hash routing, so static hosting does not need a history fallback.

Settings stores the API base URL and API key in this browser's localStorage (`saodi.apiBase` / `saodi.apiKey`; legacy `pi.*` keys are migrated and removed on first load). Only use a key on trusted devices over HTTPS.

## Layout and design

- `src/shared/tokens.css` holds every color, radius, shadow and type size (plus Vant `--van-*` overrides); components use these variables only.
- Tool results render as cards through one table, `src/components/cards/registry.ts` (tool name → card). Unmapped or failed results keep the plain tool row; the raw JSON stays expandable.
- Robot photos come from `src/shared/robotModels.ts` and load at runtime from the product site (`referrerpolicy="no-referrer"`); failures fall back to a drawn robot. Images are never copied into the repo or wheel.
- Charts in cards are hand-written SVG (`src/components/ui/BarChart.vue`).
- Markdown: `src/shared/markdown.ts` (`renderSegments`) splits model text into sanitized markdown runs and special fences. ```` ```html ```` renders in a sandboxed iframe (`HtmlPreview.vue`); ```` ```mermaid ```` renders as a diagram (`components/ui/MermaidView.vue`). While a fence is still streaming its source is shown with "Generating…"; once closed it renders. `mermaid` is loaded with a dynamic `import()` into its own chunks only when a closed mermaid fence appears (never in the first-screen bundle, never from a CDN), initialized with `securityLevel: 'strict'` and the design tokens (font, primary, ink); its SVG is sanitized again with DOMPurify (svg profile). Parse errors show the source plus one error line; wide diagrams scroll inside their card so the page never overflows horizontally.

## Internationalization

English is the source language; Chinese is the second locale.

- Dictionaries: `src/i18n/en.ts` (source) and `src/i18n/zh.ts`. Both are flat `key → string` maps; `zh.ts` is typed as `Record<keyof en, string>`, and `npm run i18n:check` (run before every build) also checks that `{placeholders}` match.
- Use `t('key', { name })` for text and `tn('base', n)` for plurals (`base.one` / `base.other`, chosen with `Intl.PluralRules`). Dates, numbers and relative times go through `formatDateTime`, `formatNumber` and `relativeTime` in `src/i18n/index.ts` (all `Intl`).
- Locale: `localStorage['saodi.locale']`, otherwise `navigator.language` (`zh*` → Chinese, anything else → English). Settings has an English / 中文 switch that applies immediately, persists, and updates `<html lang>`, `document.title` and Vant's built-in texts.
- Adding text: add the key to `en.ts` first, then the same key to `zh.ts`. Never hard-code user-visible text in components.
- Agent replies are not translated here; the backend answers in the user's input language.

## 中文说明

H5 以英文为主语言、中文为第二语言。文案字典在 `src/i18n/en.ts`（源）与 `src/i18n/zh.ts`，两者键必须完全一致，`npm run i18n:check`（`npm run build` 前自动执行）会校验键、占位符，并禁止在 `src/i18n` 之外硬编码中文。语言默认读 `localStorage` 的 `saodi.locale`，没有则按浏览器语言判断（`zh*` 为中文，其余为英文）；设置页可在 English / 中文 之间切换，即时生效并持久化。品牌统一为 Saodi AI（中文副标「扫地」），标志见 `src/shared/mark.svg`。
