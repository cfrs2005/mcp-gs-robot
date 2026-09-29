// Build-time i18n gate: every locale has exactly en.ts's keys with the same {placeholders},
// and no CJK text is hard-coded in src/ outside src/i18n (comments are ignored).
// Portable to Node 18+: the TypeScript dictionaries are stripped with esbuild (already installed via vite)
// into a temp dir and imported from there, so no Node type-stripping support is required.
import { mkdtempSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, relative } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { transform } from 'esbuild'

const root = fileURLToPath(new URL('..', import.meta.url))
const src = join(root, 'src')

async function loadDictionary(name) {
  const { code } = await transform(readFileSync(join(src, 'i18n', `${name}.ts`), 'utf8'), { loader: 'ts', format: 'esm' })
  const dir = mkdtempSync(join(tmpdir(), 'saodi-i18n-'))
  try {
    const file = join(dir, `${name}.mjs`)
    writeFileSync(file, code)
    return (await import(pathToFileURL(file).href)).default
  } finally { rmSync(dir, { recursive: true, force: true }) }
}

const en = await loadDictionary('en')
const locales = { zh: await loadDictionary('zh') }
const problems = []
const placeholders = text => [...text.matchAll(/\{(\w+)\}/g)].map(m => m[1]).sort().join(',')

for (const [name, dict] of Object.entries(locales)) {
  for (const key of Object.keys(en)) {
    if (!(key in dict)) problems.push(`${name}: missing key ${key}`)
    else if (placeholders(en[key]) !== placeholders(dict[key])) problems.push(`${name}: placeholder mismatch in ${key}`)
  }
  for (const key of Object.keys(dict)) if (!(key in en)) problems.push(`${name}: extra key ${key}`)
  for (const key of Object.keys(en)) {
    const base = key.replace(/\.(one|other)$/, '')
    if (base !== key && !(`${base}.one` in en && `${base}.other` in en)) problems.push(`en: plural ${base} needs both .one and .other`)
  }
}

const walk = dir => readdirSync(dir).flatMap(entry => {
  const path = join(dir, entry)
  return statSync(path).isDirectory() ? (entry === 'i18n' ? [] : walk(path)) : [path]
})
const stripComments = code => code.replace(/<!--[\s\S]*?-->/g, '').replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:'"`])\/\/.*$/gm, '$1')
for (const file of walk(src).filter(f => /\.(ts|vue)$/.test(f))) {
  stripComments(readFileSync(file, 'utf8')).split('\n').forEach((line, i) => {
    if (/[㐀-鿿＀-￯　-〿]/.test(line)) problems.push(`hard-coded CJK: ${relative(root, file)}:${i + 1}: ${line.trim()}`)
  })
}

if (problems.length) {
  console.error(`i18n check failed (${problems.length}):\n  ${problems.join('\n  ')}`)
  process.exit(1)
}
console.log(`i18n check ok: ${Object.keys(en).length} keys, locales en + ${Object.keys(locales).join(', ')}; no hard-coded CJK outside src/i18n`)
