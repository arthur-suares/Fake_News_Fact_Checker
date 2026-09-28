"use client"

import { cn } from "@/lib/utils"

interface LikertScaleProps {
  name: string
  value: number | null
  onChange: (value: number) => void
  minLabel?: string
  maxLabel?: string
  tone?: "primary" | "accent"
}

export function LikertScale({ name, value, onChange, minLabel, maxLabel, tone = "primary" }: LikertScaleProps) {
  const isAccent = tone === "accent"
  return (
    <div className="flex flex-col gap-2">
      <div role="radiogroup" aria-label={name} className="flex items-center justify-between gap-2">
        {[1, 2, 3, 4, 5].map((n) => {
          const selected = value === n
          return (
            <button
              key={n}
              type="button"
              role="radio"
              aria-checked={selected}
              aria-label={`Nota ${n}`}
              onClick={() => onChange(n)}
              className={cn(
                "flex h-11 flex-1 items-center justify-center rounded-lg border text-sm font-semibold transition-all",
                "focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
                selected
                  ? "scale-105 border-transparent bg-gradient-to-br from-primary to-accent text-primary-foreground shadow-md shadow-primary/40"
                  : isAccent
                    ? "border-accent/40 bg-accent/10 text-foreground hover:border-accent hover:bg-accent/25"
                    : "border-primary/40 bg-primary/10 text-foreground hover:border-primary hover:bg-primary/25",
              )}
            >
              {n}
            </button>
          )
        })}
      </div>
      {(minLabel || maxLabel) && (
        <div className="flex items-start justify-between gap-4 text-xs text-muted-foreground">
          <span className="max-w-[45%] text-pretty">{minLabel}</span>
          <span className="max-w-[45%] text-pretty text-right">{maxLabel}</span>
        </div>
      )}
    </div>
  )
}
