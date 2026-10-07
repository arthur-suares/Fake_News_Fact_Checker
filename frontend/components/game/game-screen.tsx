"use client"

import { useMemo, useState } from "react"

import { ConfidenceSelector } from "@/components/game/confidence-selector"
import { QuestionCard } from "@/components/game/question-card"
import type { Game, Question } from "@/lib/types"

type GameScreenProps = {
  game?: Partial<Game>
  question?: Question | null
}

export function GameScreen({ game, question }: GameScreenProps) {
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [confidence, setConfidence] = useState<number | null>(null)

  const roundNumber = useMemo(() => game?.rounds?.length ?? 1, [game])

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-2xl font-bold text-slate-900">Nova partida</h1>
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-700">
            Rodada {roundNumber}
          </span>
        </div>
        <p className="mt-2 text-sm text-slate-600">
          Fluxo mínimo preparado para o MVP de avaliação de informação com rastreamento de habilidade.
        </p>
      </div>

      <QuestionCard question={question ?? null} onAnswer={(option) => setSelectedOption(option)} />

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <ConfidenceSelector value={confidence} onChange={setConfidence} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">
        <p>Resposta selecionada: {selectedOption ?? "Nenhuma"}</p>
        <p>Confiança: {confidence ?? "Nenhuma"}</p>
      </div>
    </div>
  )
}
