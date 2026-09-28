"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { LikertScale } from "@/components/likert-scale"
import type { ResultadoVerificacao, Veredito } from "@/lib/types"
import { cn } from "@/lib/utils"
import { AlertTriangle, CheckCircle2, ExternalLink, HelpCircle, RotateCcw, Send, XCircle } from "lucide-react"

interface ResultScreenProps {
  resultado: ResultadoVerificacao
  onRestart: () => void
  onEnviarOpiniao: (valor: number) => Promise<void>
}

const veredictoConfig: Record<
  Veredito,
  { label: string; Icon: typeof CheckCircle2; wrap: string; icon: string }
> = {
  verdadeiro: {
    label: "A afirmação provavelmente é verdadeira.",
    Icon: CheckCircle2,
    wrap: "border-accent/40 bg-secondary",
    icon: "text-accent",
  },
  falso: {
    label: "A afirmação provavelmente é falsa.",
    Icon: XCircle,
    wrap: "border-destructive/30 bg-destructive/10",
    icon: "text-destructive",
  },
  enganoso: {
    label: "A afirmação é enganosa ou fora de contexto.",
    Icon: AlertTriangle,
    wrap: "border-primary/30 bg-primary/5",
    icon: "text-primary",
  },
  nao_verificado: {
    label: "Não foi possível verificar a afirmação.",
    Icon: HelpCircle,
    wrap: "border-border bg-muted",
    icon: "text-muted-foreground",
  },
}

function Field({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{titulo}</span>
      <div className="text-sm text-foreground">{children}</div>
    </div>
  )
}

export function ResultScreen({ resultado, onRestart, onEnviarOpiniao }: ResultScreenProps) {
  const [opiniao, setOpiniao] = useState<number | null>(null)
  const [envio, setEnvio] = useState<"idle" | "enviando" | "enviado" | "erro">("idle")
  const cfg = veredictoConfig[resultado.veredito]
  const { Icon } = cfg

  async function handleEnviar() {
    if (opiniao === null) return
    setEnvio("enviando")
    try {
      await onEnviarOpiniao(opiniao)
      setEnvio("enviado")
    } catch {
      setEnvio("erro")
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col items-center gap-1 text-center">
        <span className="text-xs font-semibold uppercase tracking-widest text-primary">Resultado</span>
      </header>

      <div className={cn("flex items-start gap-3 rounded-xl border p-4", cfg.wrap)}>
        <Icon className={cn("mt-0.5 size-6 shrink-0", cfg.icon)} />
        <p className="text-base font-semibold text-foreground">{cfg.label}</p>
      </div>

      <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-4">
        {resultado.classificacao && <Field titulo="Classificação">{resultado.classificacao}</Field>}
        <Field titulo={`Checagens encontradas (${resultado.evidencias.length})`}>
          {resultado.evidencias.length === 0 ? (
            <p className="text-pretty leading-relaxed text-muted-foreground">
              Nenhuma agência de checagem avaliou essa afirmação ainda.
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {resultado.evidencias.map((ev, i) => (
                <li
                  key={`${ev.source}-${ev.url ?? i}`}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background/60 p-3"
                >
                  <div className="flex min-w-0 flex-col">
                    <span className="truncate font-medium">{ev.source}</span>
                    {ev.rating && <span className="text-xs text-muted-foreground">{ev.rating}</span>}
                  </div>
                  {ev.url && (
                    <a
                      href={ev.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex shrink-0 items-center gap-1 text-xs font-semibold text-primary hover:underline"
                    >
                      Ver checagem
                      <ExternalLink className="size-3.5" />
                    </a>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Field>
      </div>

      <div className="flex flex-col gap-3 rounded-xl border border-primary/20 bg-primary/5 p-4">
        <p className="text-sm font-medium text-foreground">Depois da verificação, sua opinião mudou?</p>
        <LikertScale
          name="Depois da verificação, sua opinião mudou?"
          value={opiniao}
          onChange={(v) => {
            setOpiniao(v)
            if (envio === "erro") setEnvio("idle")
          }}
          minLabel="Não mudou"
          maxLabel="Mudou totalmente"
        />
        {envio === "enviado" ? (
          <p className="text-center text-xs text-muted-foreground">Resposta registrada. Obrigado!</p>
        ) : (
          <Button
            type="button"
            onClick={handleEnviar}
            disabled={opiniao === null || envio === "enviando"}
            className="h-10 w-full gap-2 text-sm font-semibold"
          >
            <Send className="size-4" />
            {envio === "enviando" ? "Enviando..." : "Enviar resposta"}
          </Button>
        )}
        {envio === "erro" && (
          <p className="text-center text-xs text-destructive">Não foi possível enviar sua resposta. Tente novamente.</p>
        )}
      </div>

      <Button
        type="button"
        onClick={onRestart}
        variant="outline"
        className="h-11 w-full gap-2 text-sm font-semibold"
      >
        <RotateCcw className="size-4" />
        Verificar outra notícia
      </Button>

      <p className="text-center text-xs text-muted-foreground">
        Resultado baseado no Google Fact Check. Use como apoio e confirme em fontes oficiais.
      </p>
    </div>
  )
}
