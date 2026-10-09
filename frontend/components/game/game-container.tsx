"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import Link from "next/link"
import { AlertCircle, BarChart3, Home, Loader2, RotateCcw, Trophy } from "lucide-react"

import { GameScreen } from "@/components/game/game-screen"
import { Button, buttonVariants } from "@/components/ui/button"
import { createGame, describeApiError, getNextRound, isAuthenticationError } from "@/lib/game-api"
import type { GameRoundPayload } from "@/lib/types"
import { cn } from "@/lib/utils"

type GameState =
  | { phase: "loading"; message: string }
  | { phase: "playing"; round: GameRoundPayload }
  | { phase: "error"; message: string; retry: () => void; requiresLogin: boolean }
  | { phase: "finished"; roundsPlayed: number }

function CenteredCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-1 items-center justify-center px-4 py-12">
      <div className="flex w-full max-w-md flex-col items-center gap-4 rounded-xl border border-border bg-card p-6 text-center shadow-sm">
        {children}
      </div>
    </div>
  )
}

export function GameContainer() {
  const [state, setState] = useState<GameState>({ phase: "loading", message: "Preparando a partida..." })
  // Evita criar duas partidas quando o React (StrictMode) monta o efeito duas vezes em dev
  const started = useRef(false)

  const startGame = useCallback(async () => {
    setState({ phase: "loading", message: "Preparando a partida..." })
    try {
      setState({ phase: "playing", round: await createGame() })
    } catch (error) {
      setState({
        phase: "error",
        message: describeApiError(error),
        retry: startGame,
        requiresLogin: isAuthenticationError(error),
      })
    }
  }, [])

  const loadNextRound = useCallback(async (gameId: string, roundsPlayed: number) => {
    setState({ phase: "loading", message: "Carregando a próxima rodada..." })
    try {
      const next = await getNextRound(gameId)
      setState(next ? { phase: "playing", round: next } : { phase: "finished", roundsPlayed })
    } catch (error) {
      setState({
        phase: "error",
        message: describeApiError(error),
        retry: () => loadNextRound(gameId, roundsPlayed),
        requiresLogin: isAuthenticationError(error),
      })
    }
  }, [])

  useEffect(() => {
    if (started.current) return
    started.current = true
    void startGame()
  }, [startGame])

  if (state.phase === "loading") {
    return (
      <CenteredCard>
        <Loader2 className="size-8 animate-spin text-primary" />
        <p role="status" className="text-sm text-muted-foreground">
          {state.message}
        </p>
      </CenteredCard>
    )
  }

  if (state.phase === "error") {
    return (
      <CenteredCard>
        <AlertCircle className="size-8 text-destructive" />
        <p role="alert" className="text-sm text-foreground">
          {state.message}
        </p>
        {state.requiresLogin ? (
          <Link href="/login" className={cn(buttonVariants(), "h-10 w-full gap-2 text-sm font-semibold")}>
            Entrar
          </Link>
        ) : (
          <Button type="button" onClick={state.retry} className="h-10 w-full gap-2 text-sm font-semibold">
            <RotateCcw className="size-4" />
            Tentar novamente
          </Button>
        )}
      </CenteredCard>
    )
  }

  if (state.phase === "finished") {
    return (
      <CenteredCard>
        <Trophy className="size-10 text-primary" />
        <div className="flex flex-col gap-1">
          <h1 className="text-xl font-bold text-foreground">Partida concluída!</h1>
          <p className="text-sm text-muted-foreground">
            Você jogou {state.roundsPlayed} {state.roundsPlayed === 1 ? "rodada" : "rodadas"}. Veja como estão suas
            habilidades ou comece uma nova partida.
          </p>
        </div>
        <Link href="/profile" className={cn(buttonVariants(), "h-10 w-full gap-2 text-sm font-semibold")}>
          <BarChart3 className="size-4" />
          Ver minhas habilidades
        </Link>
        <Button type="button" variant="outline" onClick={startGame} className="h-10 w-full gap-2 text-sm font-semibold">
          <RotateCcw className="size-4" />
          Nova partida
        </Button>
        <Link href="/" className={cn(buttonVariants({ variant: "ghost" }), "h-10 w-full gap-2 text-sm")}>
          <Home className="size-4" />
          Voltar ao início
        </Link>
      </CenteredCard>
    )
  }

  const { round } = state
  return (
    <GameScreen
      // key reinicia seleção, confiança e feedback a cada rodada
      key={round.round.id}
      gameId={round.game_id}
      gameRoundId={round.round.id}
      news={round.news}
      question={round.question}
      roundNumber={round.round.number}
      onContinue={() => loadNextRound(round.game_id, round.round.number)}
    />
  )
}
