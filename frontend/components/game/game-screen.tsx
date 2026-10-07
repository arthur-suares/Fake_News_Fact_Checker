"use client"

import { useEffect, useRef, useState } from "react"
import { AlertCircle, Loader2, Send } from "lucide-react"

import { ConfidenceSelector } from "@/components/game/confidence-selector"
import { FeedbackScreen } from "@/components/game/feedback-screen"
import { GameProgress } from "@/components/game/game-progress"
import { NewsCard } from "@/components/game/news-card"
import { QuestionCard } from "@/components/game/question-card"
import { Button } from "@/components/ui/button"
import { describeApiError, submitAnswer } from "@/lib/game-api"
import { toSkillCode } from "@/lib/skills"
import type { AnswerFeedback, AnswerResponse, AnswerSubmission, News, Question } from "@/lib/types"

// MVP: a partida termina após 10 rodadas (backend/app/services/game.py)
const DEFAULT_TOTAL_ROUNDS = 10

type GameScreenProps = {
  gameId: string
  gameRoundId: string
  news?: News | null
  question?: Question | null
  roundNumber?: number
  totalRounds?: number
  onContinue: () => void
}

type SubmitStatus = "idle" | "submitting" | "error"

// Junta a resposta do backend com os textos da pergunta já carregada.
// A dica para a próxima rodada vem do conteúdo pré-autorado em lib/skills.ts.
function buildFeedback(question: Question, selectedOption: string, result: AnswerResponse): AnswerFeedback | null {
  const skillCode = toSkillCode(result.skill_code) ?? toSkillCode(question.skill_code ?? question.skill_id)
  if (!skillCode) return null
  const correctOption = result.correct_option ?? question.correct_option ?? null

  return {
    correct: result.correct,
    skill_code: skillCode,
    selected_option: selectedOption,
    selected_option_text: question.options[selectedOption],
    correct_option: correctOption,
    correct_option_text: correctOption ? question.options[correctOption] : null,
    explanation: result.explanation ?? question.explanation,
    mastery_before: result.previous_mastery_probability,
    mastery_after: result.mastery_probability,
  }
}

export function GameScreen({
  gameId,
  gameRoundId,
  news,
  question,
  roundNumber = 1,
  totalRounds = DEFAULT_TOTAL_ROUNDS,
  onContinue,
}: GameScreenProps) {
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [confidence, setConfidence] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null)
  const [status, setStatus] = useState<SubmitStatus>("idle")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const startedAt = useRef<number>(0)
  // Trava síncrona: o estado do React só atualiza no próximo render,
  // então dois cliques rápidos passariam pela checagem de `status`.
  const inFlight = useRef(false)

  // Marca o início da rodada para calcular response_time
  useEffect(() => {
    if (!feedback) startedAt.current = Date.now()
  }, [question?.id, feedback])

  const submitting = status === "submitting"
  const canSubmit = Boolean(question && selectedOption && confidence) && !submitting

  async function handleSubmit() {
    if (!question || !selectedOption || !confidence || inFlight.current) return
    inFlight.current = true
    setStatus("submitting")
    setErrorMessage(null)

    const payload: AnswerSubmission = {
      question_id: question.id,
      game_round_id: gameRoundId,
      selected_option: selectedOption,
      confidence,
      response_time: Math.max(0, Date.now() - startedAt.current),
    }

    try {
      const result = await submitAnswer(gameId, payload)
      const built = buildFeedback(question, selectedOption, result)
      if (!built) throw new Error("Resposta sem skill reconhecida")
      setFeedback(built)
      setStatus("idle")
    } catch (error) {
      setErrorMessage(describeApiError(error))
      setStatus("error")
    } finally {
      inFlight.current = false
    }
  }

  function clearError() {
    if (status === "error") {
      setStatus("idle")
      setErrorMessage(null)
    }
  }

  if (feedback) {
    return (
      <FeedbackScreen
        feedback={feedback}
        roundNumber={roundNumber}
        isLastRound={roundNumber >= totalRounds}
        onContinue={onContinue}
      />
    )
  }

  return (
    <div>
      <header className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto max-w-3xl px-4 py-3">
          <GameProgress current={roundNumber} total={totalRounds} />
        </div>
      </header>

      <main
        aria-busy={submitting}
        className="mx-auto flex max-w-3xl flex-col gap-4 px-4 pt-4 pb-36 sm:gap-5 sm:pt-6 sm:pb-8"
      >
        {news && <NewsCard news={news} />}

        <QuestionCard
          question={question ?? null}
          selectedOption={selectedOption}
          disabled={submitting}
          onAnswer={(option) => {
            setSelectedOption(option)
            clearError()
          }}
        />

        <div className="rounded-xl border border-border bg-card p-4 shadow-sm sm:p-5">
          <ConfidenceSelector
            value={confidence}
            disabled={submitting}
            onChange={(value) => {
              setConfidence(value)
              clearError()
            }}
          />
        </div>

        {/* No mobile o botão fica fixo no rodapé; no desktop volta ao fluxo da página */}
        <div className="fixed inset-x-0 bottom-0 border-t border-border bg-background/95 p-4 backdrop-blur sm:static sm:border-0 sm:bg-transparent sm:p-0">
          <div className="mx-auto flex max-w-3xl flex-col gap-2">
            {errorMessage && (
              <div
                role="alert"
                className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
              >
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="h-11 w-full gap-2 text-sm font-semibold"
            >
              {submitting ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
              {submitting ? "Enviando resposta..." : status === "error" ? "Tentar novamente" : "Responder"}
            </Button>
            {!selectedOption || !confidence ? (
              <p className="text-center text-xs text-muted-foreground">
                {!selectedOption ? "Escolha uma alternativa" : "Indique sua confiança"} para responder.
              </p>
            ) : null}
          </div>
        </div>
      </main>
    </div>
  )
}
