"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { LikertScale } from "@/components/likert-scale"
import { PERGUNTAS_PRE, type RespostasPre } from "@/lib/types"
import { ClipboardCheck } from "lucide-react"

interface SurveyFormProps {
  onComplete: (respostas: RespostasPre) => void
}

export function SurveyForm({ onComplete }: SurveyFormProps) {
  const [respostas, setRespostas] = useState<Record<string, number>>({})

  const todasRespondidas = PERGUNTAS_PRE.every((p) => respostas[p.id])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!todasRespondidas) return
    onComplete(respostas as unknown as RespostasPre)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      <header className="flex flex-col items-center gap-3 text-center">
        <span className="flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent text-primary-foreground shadow-lg shadow-accent/30">
          <ClipboardCheck className="size-6" />
        </span>
        <div>
          <h1 className="text-balance bg-gradient-to-r from-primary to-accent bg-clip-text text-2xl font-bold text-transparent sm:text-3xl">
            Antes de começar
          </h1>
          <p className="mt-1 text-pretty text-sm text-muted-foreground">
            Responda a algumas perguntas rápidas sobre a notícia que você vai verificar. Use a escala de 1 a 5.
          </p>
        </div>
      </header>

      <div className="flex flex-col gap-5">
        {PERGUNTAS_PRE.map((pergunta, i) => (
          <fieldset
            key={pergunta.id}
            className={
              i % 2 === 0
                ? "rounded-xl border border-primary/40 border-l-4 border-l-primary bg-primary/10 p-4"
                : "rounded-xl border border-accent/40 border-l-4 border-l-accent bg-accent/10 p-4"
            }
          >
            <legend className="sr-only">{pergunta.texto}</legend>
            <p className="mb-3 flex items-start gap-2 text-sm font-medium text-foreground">
              <span
                className={
                  i % 2 === 0
                    ? "flex size-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground"
                    : "flex size-6 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-bold text-accent-foreground"
                }
              >
                {i + 1}
              </span>
              <span className="pt-0.5">{pergunta.texto}</span>
            </p>
            <LikertScale
              tone={i % 2 === 0 ? "primary" : "accent"}
              name={pergunta.texto}
              value={respostas[pergunta.id] ?? null}
              onChange={(v) => setRespostas((prev) => ({ ...prev, [pergunta.id]: v }))}
              minLabel={pergunta.min}
              maxLabel={pergunta.max}
            />
          </fieldset>
        ))}
      </div>

      <Button
        type="submit"
        disabled={!todasRespondidas}
        className="h-12 w-full bg-gradient-to-r from-primary to-accent text-base font-semibold text-primary-foreground shadow-lg shadow-primary/30 hover:opacity-90"
      >
        Continuar
      </Button>
    </form>
  )
}
