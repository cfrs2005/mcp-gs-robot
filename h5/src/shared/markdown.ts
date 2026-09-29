import { marked, type Token, type Tokens } from 'marked'
import DOMPurify from 'dompurify'

// Every link the model writes opens outside the app and cannot reach window.opener.
DOMPurify.addHook('afterSanitizeAttributes', node => {
  if (node.tagName === 'A' && node.getAttribute('href')) {
    node.setAttribute('target', '_blank')
    node.setAttribute('rel', 'noopener noreferrer')
  }
})

marked.setOptions({ gfm: true, breaks: true })

/** Fenced blocks rendered by their own component instead of as code: ```html (sandboxed preview) and ```mermaid (diagram). */
export type FenceKind = 'html' | 'mermaid'
export type Segment =
  | { kind: 'md'; html: string }
  | { kind: FenceKind; source: string; closed: boolean }

const FENCES: Record<string, FenceKind> = { html: 'html', htm: 'html', mermaid: 'mermaid' }
const fenceKind = (token: Token): FenceKind | undefined =>
  token.type === 'code' ? FENCES[((token as Tokens.Code).lang ?? '').trim().toLowerCase()] : undefined

// A fence is finished only when its raw text ends with a closing fence line; while streaming it is still open.
const fenceClosed = (raw: string) => /\n\s*(`{3,}|~{3,})\s*$/.test(raw.trimEnd())

/** Split markdown into sanitized HTML runs and special fences (```html previews, ```mermaid diagrams). */
export function renderSegments(text: string): Segment[] {
  const tokens = marked.lexer(text.replace(/\r\n/g, '\n'))
  const segments: Segment[] = []
  let run: Token[] = []
  const flush = () => {
    if (!run.length) return
    const list = Object.assign(run, { links: tokens.links })
    const html = DOMPurify.sanitize(marked.parser(list) as string)
    segments.push({ kind: 'md', html })
    run = []
  }
  for (const token of tokens) {
    const kind = fenceKind(token)
    if (kind) {
      flush()
      segments.push({ kind, source: (token as Tokens.Code).text, closed: fenceClosed(token.raw) })
    } else run.push(token)
  }
  flush()
  return segments
}
