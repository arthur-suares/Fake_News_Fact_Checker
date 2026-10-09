
"use client"

import { useEffect, useRef, useState } from "react"

import { ConfidenceSelector } from "@/components/game/confidence-selector"
import { QuestionCard } from "@/components/game/question-card"
import { createGame, submitAnswer } from "@/lib/game-api"
import type { GameCreateResponse, GameResult } from "@/lib/types"

export function GameScreen() {
  const [gameData, setGameData] = useState<GameCreateResponse | null>(null)
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [confidence, setConfidence] = useState<number | null>(null)
  const [loadingGame, setLoadingGame] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<GameResult | null>(null)

  const startedAt = useRef<number>(Date.now())
  const submitLock = useRef(false)

  useEffect(() => {
    let active = true

    async function loadGame() {
      try {
        setLoadingGame(true)
        setError(null)

        const data = await createGame()

        if (active) {
          setGameData(data)
          startedAt.current = Date.now()
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Não foi possível iniciar a partida."
          )
        }
      } finally {
        if (active) setLoadingGame(false)
      }
    }

    void loadGame()

    return () => {
      active = false
    }
  }, [])

  async function handleSubmit() {
    if (
      !gameData ||
      !selectedOption ||
      confidence === null ||
      submitLock.current ||
      result
    ) {
      return
    }

    submitLock.current = true
    setSubmitting(true)
    setError(null)

    try {
      const response = await submitAnswer(gameData.game_id, {
        question_id: gameData.question.id,
        game_round_id: gameData.round.id,
        selected_option: selectedOption,
        confidence,
        response_time: Math.max(
          0,
          Math.floor((Date.now() - startedAt.current) / 1000)
        ),
      })

      setResult(response)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível enviar sua resposta. Tente novamente."
      )
    } finally {
      submitLock.current = false
      setSubmitting(false)
    }
  }

  if (loadingGame) {
    return (
      <div className="p-8 text-center text-slate-600" role="status">
        Carregando partida...
      </div>
    )
  }

  if (!gameData) {
    return (
      <div className="mx-auto max-w-3xl p-8">
        <p className="text-red-600" role="alert">
          {error ?? "Não foi possível carregar a partida."}
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="mt-4 rounded-lg bg-sky-600 px-4 py-2 text-white"
        >
          Tentar novamente
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-2xl font-bold text-slate-900">
            Nova partida
          </h1>
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm text-emerald-700">
            Rodada {gameData.round.number}
          </span>
        </div>

        <h2 className="mt-4 text-lg font-semibold text-slate-800">
          {gameData.news.title}
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          {gameData.news.content}
        </p>
      </div>

      <QuestionCard
        question={gameData.question}
        onAnswer={(option) => {
          if (!submitting && !result) setSelectedOption(option)
        }}
      />

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <ConfidenceSelector
          value={confidence}
          onChange={(value) => {
            if (!submitting && !result) setConfidence(value)
          }}
        />
      </div>

      {!result && (
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!selectedOption || confidence === null || submitting}
          className="w-full rounded-lg bg-sky-600 px-4 py-3 font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Enviando resposta..." : "Enviar resposta"}
        </button>
      )}

      {error && (
        <p className="rounded-lg bg-red-50 p-4 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      {result && (
        <section
          className="space-y-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          aria-live="polite"
        >
          <h2 className="text-xl font-bold text-slate-900">
            {result.correct ? "Resposta correta!" : "Resposta incorreta"}
          </h2>

          {result.explanation && (
            <p className="text-slate-700">{result.explanation}</p>
          )}

          <p className="text-sm text-slate-600">
            Habilidade: {result.skill_code}
          </p>
          <p className="text-sm text-slate-600">
            Domínio estimado:{" "}
            {(result.mastery_probability * 100).toFixed(1)}%
          </p>
        </section>
      )}
    </div>
  )
}