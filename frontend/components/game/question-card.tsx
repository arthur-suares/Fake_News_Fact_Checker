import { Search } from "lucide-react"

import { hasVerdictOptions, parseOption, type OptionVerdict } from "@/lib/answer-options"
import { SKILL_INFO, toSkillCode } from "@/lib/skills"
import type { Question } from "@/lib/types"
import { cn } from "@/lib/utils"

export function VerdictBadge({ verdict, label }: { verdict: OptionVerdict; label: string }) {
  return (
    <span
      className={cn(
        "w-fit rounded px-1.5 py-0.5 text-xs font-semibold",
        verdict === "true" ? "bg-accent/15 text-accent" : "bg-destructive/10 text-destructive",
      )}
    >
      {label}
    </span>
  )
}

type QuestionCardProps = {
  question: Question | null
  selectedOption?: string | null
  disabled?: boolean
  onAnswer: (option: string) => void
}

export function QuestionCard({ question, selectedOption, disabled = false, onAnswer }: QuestionCardProps) {
  if (!question) {
    return <div className="rounded-xl border border-border bg-muted p-6 text-muted-foreground">Nenhuma pergunta ativa.</div>
  }

  const skillCode = toSkillCode(question.skill_code ?? question.skill_id)
  const verdictOptions = hasVerdictOptions(question.options)

  return (
    <fieldset
      disabled={disabled}
      className="flex flex-col gap-4 rounded-xl border border-border bg-card p-4 shadow-sm disabled:opacity-60 sm:p-5"
    >
      {skillCode && (
        <span className="w-fit rounded-full bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">
          {SKILL_INFO[skillCode].name}
        </span>
      )}

      <legend className="sr-only">{question.text}</legend>
      <h3 aria-hidden className="text-base font-semibold text-pretty text-foreground sm:text-lg">
        {question.text}
      </h3>

      {question.hints && question.hints.length > 0 && (
        <div className="flex flex-col gap-1.5 rounded-lg border border-primary/20 bg-primary/5 p-3">
          <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-primary">
            <Search className="size-3.5" />
            Pontos de atenção
          </span>
          <ul className="flex list-disc flex-col gap-1 pl-5 text-sm leading-snug text-foreground/90">
            {question.hints.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
        </div>
      )}

      {verdictOptions && (
        <p className="text-sm leading-snug text-muted-foreground">
          Cada alternativa traz um veredito e uma justificativa. Só vale o acerto quando os dois estão certos: é o
          critério usado que mostra domínio em {skillCode ? SKILL_INFO[skillCode].name.toLowerCase() : "checagem"}.
        </p>
      )}

      <div className="grid gap-2.5">
        {Object.entries(question.options).map(([key, value]) => {
          const selected = selectedOption === key
          const option = parseOption(value)
          return (
            <button
              key={key}
              type="button"
              onClick={() => onAnswer(key)}
              aria-pressed={selected}
              className={cn(
                "flex items-start gap-3 rounded-lg border px-3 py-3 text-left text-sm transition outline-none focus-visible:ring-3 focus-visible:ring-ring/50 sm:px-4",
                selected
                  ? "border-primary bg-primary/5 text-foreground"
                  : "border-border bg-background text-foreground/90 hover:border-primary/40 hover:bg-muted",
              )}
            >
              <span
                className={cn(
                  "flex size-6 shrink-0 items-center justify-center rounded-full border text-xs font-bold",
                  selected ? "border-primary bg-primary text-primary-foreground" : "border-border text-muted-foreground",
                )}
              >
                {key}
              </span>
              {option.verdict ? (
                <span className="flex flex-col gap-1 pt-0.5">
                  <VerdictBadge verdict={option.verdict} label={option.verdictLabel!} />
                  <span className="leading-snug">{option.justification}</span>
                </span>
              ) : (
                <span className="pt-0.5 leading-snug">{value}</span>
              )}
            </button>
          )
        })}
      </div>
    </fieldset>
  )
}
