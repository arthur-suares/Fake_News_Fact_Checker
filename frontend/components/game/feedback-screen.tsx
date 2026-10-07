import { ArrowRight, CheckCircle2, Lightbulb, Target, XCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { SKILL_INFO } from "@/lib/skills"
import type { AnswerFeedback } from "@/lib/types"
import { cn } from "@/lib/utils"

type FeedbackScreenProps = {
  feedback: AnswerFeedback
  roundNumber?: number
  isLastRound?: boolean
  onContinue: () => void
}

function Section({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{titulo}</span>
      <div className="text-sm leading-relaxed text-foreground">{children}</div>
    </div>
  )
}

function MasteryChange({ before, after }: { before: number; after: number }) {
  const pctBefore = Math.round(Math.min(1, Math.max(0, before)) * 100)
  const pctAfter = Math.round(Math.min(1, Math.max(0, after)) * 100)
  const delta = pctAfter - pctBefore

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between text-sm">
        <span className="text-muted-foreground">Domínio estimado</span>
        <span className="font-semibold tabular-nums">
          {pctBefore}% → {pctAfter}%
          <span className={cn("ml-2 text-xs", delta >= 0 ? "text-accent" : "text-destructive")}>
            ({delta >= 0 ? "+" : ""}
            {delta} p.p.)
          </span>
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${pctAfter}%` }} />
      </div>
    </div>
  )
}

export function FeedbackScreen({ feedback, roundNumber, isLastRound = false, onContinue }: FeedbackScreenProps) {
  const skill = SKILL_INFO[feedback.skill_code]
  const nextAction = feedback.next_action ?? (feedback.correct ? skill.nextAction.correct : skill.nextAction.incorrect)
  const hasMastery = feedback.mastery_before != null && feedback.mastery_after != null
  const ResultIcon = feedback.correct ? CheckCircle2 : XCircle

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-8">
      <header className="flex flex-col items-center gap-1 text-center">
        <span className="text-xs font-semibold uppercase tracking-widest text-primary">
          {roundNumber ? `Rodada ${roundNumber} · Feedback` : "Feedback"}
        </span>
      </header>

      <div
        role="status"
        className={cn(
          "flex items-start gap-3 rounded-xl border p-4",
          feedback.correct ? "border-accent/40 bg-secondary" : "border-destructive/30 bg-destructive/10",
        )}
      >
        <ResultIcon className={cn("mt-0.5 size-6 shrink-0", feedback.correct ? "text-accent" : "text-destructive")} />
        <div>
          <p className="text-base font-semibold text-foreground">
            {feedback.correct ? "Resposta correta!" : "Resposta incorreta"}
          </p>
          <p className="text-sm text-muted-foreground">
            {feedback.correct ? "Boa análise. Você identificou o ponto principal." : "Veja abaixo o que passou despercebido."}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-4">
        {!feedback.correct && (
          <Section titulo="Sua resposta">
            <span className="font-semibold">{feedback.selected_option}.</span> {feedback.selected_option_text}
          </Section>
        )}
        {feedback.correct_option && (
          <Section titulo="Resposta correta">
            <span className="font-semibold">{feedback.correct_option}.</span> {feedback.correct_option_text}
          </Section>
        )}
        <Section titulo="Explicação">
          {feedback.explanation ?? <span className="text-muted-foreground">Sem explicação cadastrada para esta pergunta.</span>}
        </Section>
      </div>

      <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <div className="flex items-start gap-3">
          <Target className="mt-0.5 size-5 shrink-0 text-primary" />
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Skill trabalhada</span>
            <p className="text-sm font-semibold text-foreground">
              {skill.name} <span className="font-normal text-muted-foreground">({feedback.skill_code})</span>
            </p>
            <p className="text-sm text-muted-foreground">{skill.description}</p>
          </div>
        </div>
        {hasMastery && <MasteryChange before={feedback.mastery_before!} after={feedback.mastery_after!} />}
      </div>

      <div className="flex items-start gap-3 rounded-xl border border-primary/20 bg-primary/5 p-4">
        <Lightbulb className="mt-0.5 size-5 shrink-0 text-primary" />
        <div className="flex flex-col gap-0.5">
          <span className="text-xs font-semibold uppercase tracking-wide text-primary">Para a próxima rodada</span>
          <p className="text-sm leading-relaxed text-foreground">{nextAction}</p>
        </div>
      </div>

      <Button type="button" onClick={onContinue} className="h-11 w-full gap-2 text-sm font-semibold">
        {isLastRound ? "Ver resultado da partida" : "Próxima rodada"}
        <ArrowRight className="size-4" />
      </Button>
    </div>
  )
}
