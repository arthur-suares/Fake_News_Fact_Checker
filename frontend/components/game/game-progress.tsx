type GameProgressProps = {
  current: number
  total: number
}

export function GameProgress({ current, total }: GameProgressProps) {
  const value = Math.min(100, Math.max(0, (current / total) * 100))

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-semibold text-foreground">
          Rodada {current} de {total}
        </span>
        <span className="tabular-nums text-muted-foreground">{Math.round(value)}%</span>
      </div>
      <div
        role="progressbar"
        aria-label="Progresso da partida"
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={current}
        className="h-2 overflow-hidden rounded-full bg-muted"
      >
        <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}
