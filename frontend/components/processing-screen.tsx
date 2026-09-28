"use client"

import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"
import { Check, Loader2 } from "lucide-react"

interface ProcessingScreenProps {
  hasImage: boolean
}

export function ProcessingScreen({ hasImage }: ProcessingScreenProps) {
  const steps = [
    ...(hasImage ? ["Enviando imagem"] : []),
    "Consultando agências de checagem",
    "Comparando avaliações",
    "Preparando resultado",
  ]
  const [active, setActive] = useState(0)

  useEffect(() => {
    if (active >= steps.length - 1) return
    const t = setTimeout(() => setActive((a) => a + 1), 1100)
    return () => clearTimeout(t)
  }, [active, steps.length])

  return (
    <div className="flex flex-col items-center gap-8 py-6">
      <div className="flex flex-col items-center gap-4 text-center">
        <span className="flex size-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <Loader2 className="size-7 animate-spin" />
        </span>
        <h1 className="text-xl font-bold text-foreground">Analisando notícia...</h1>
      </div>

      <ul className="flex w-full flex-col gap-3">
        {steps.map((step, i) => {
          const done = i < active
          const current = i === active
          return (
            <li
              key={step}
              className={cn(
                "flex items-center gap-3 rounded-xl border p-3 transition-all",
                done && "border-accent/40 bg-secondary/50",
                current && "border-primary/40 bg-primary/5",
                !done && !current && "border-border bg-card opacity-60",
              )}
            >
              <span
                className={cn(
                  "flex size-6 shrink-0 items-center justify-center rounded-full",
                  done && "bg-accent text-accent-foreground",
                  current && "bg-primary text-primary-foreground",
                  !done && !current && "border border-border text-transparent",
                )}
              >
                {done ? (
                  <Check className="size-4" />
                ) : current ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <span className="size-2 rounded-full bg-muted-foreground/40" />
                )}
              </span>
              <span
                className={cn(
                  "text-sm font-medium",
                  done && "text-foreground",
                  current && "text-foreground",
                  !done && !current && "text-muted-foreground",
                )}
              >
                {step}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
