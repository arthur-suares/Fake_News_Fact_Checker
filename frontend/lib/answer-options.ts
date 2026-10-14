// As alternativas das alegações do dataset vêm como "Veredito: justificativa"
// (VERDICT_LABEL em backend/app/services/news_questions.py). Só o veredito
// certo com o critério correto da skill conta como acerto para o BKT.
export type OptionVerdict = "true" | "fake"

export interface ParsedOption {
  verdict: OptionVerdict | null
  verdictLabel: string | null
  justification: string
}

const VERDICT_PREFIXES: Record<string, OptionVerdict> = {
  Verdadeira: "true",
  "Falsa ou enganosa": "fake",
}

export function parseOption(text: string | null | undefined): ParsedOption {
  const value = text ?? ""
  const separator = value.indexOf(": ")
  const prefix = separator > 0 ? value.slice(0, separator) : ""
  const verdict = VERDICT_PREFIXES[prefix]
  if (!verdict) return { verdict: null, verdictLabel: null, justification: value }
  return { verdict, verdictLabel: prefix, justification: value.slice(separator + 2) }
}

// Verdadeiro quando todas as alternativas seguem o formato veredito + justificativa.
export function hasVerdictOptions(options: Record<string, string>): boolean {
  const values = Object.values(options)
  return values.length > 0 && values.every((value) => parseOption(value).verdict !== null)
}
