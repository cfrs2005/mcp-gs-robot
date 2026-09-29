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

export type Segment =
  | { kind: 'md'; html: string }
  | { kind: 'html'; source: string; closed: boolean }

const isHtmlFence = (token: Token): token is Tokens.Code =>
  token.type === 'code' && /^(html|htm)$/i.test((token as Tokens.Code).lang?.trim() ?? '')

// A fence is finished only when its raw text ends with a closing fence line; while streaming it is still open.
const fenceClosed = (raw: string) => /\n\s*(`{3,}|~{3,})\s*$/.test(raw.trimEnd())

/** Split markdown into sanitized HTML runs and ```html blocks (rendered separately as sandboxed previews). */
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
    if (isHtmlFence(token)) {
      flush()
      segments.push({ kind: 'html', source: token.text, closed: fenceClosed(token.raw) })
    } else run.push(token)
  }
  flush()
  return segments
}
