"use client"

import { useState } from "react"
import { SurveyForm } from "@/components/survey-form"
import { NewsEntry } from "@/components/news-entry"
import { ProcessingScreen } from "@/components/processing-screen"
import { ResultScreen } from "@/components/result-screen"
import { enviarFeedback, verificarNoticia } from "@/lib/api"
import type { RespostasPre, ResultadoVerificacao } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { BrandLogo } from "@/components/brand-logo"
import { AlertCircle, ArrowLeft } from "lucide-react"

type Etapa = "survey" | "entry" | "processing" | "result"

export default function VerificarPage() {
  const [etapa, setEtapa] = useState<Etapa>("survey")
  const [respostasPre, setRespostasPre] = useState<RespostasPre | null>(null)
  const [hasImage, setHasImage] = useState(false)
  const [resultado, setResultado] = useState<ResultadoVerificacao | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  async function handleVerify(news: string, image: File | null) {
    setErro(null)
    setHasImage(Boolean(image))
    setEtapa("processing")

    const started = Date.now()
    try {
      const data = await verificarNoticia(news, image)

      // garante que a animação de análise seja perceptível
      const elapsed = Date.now() - started
      const minTime = image ? 3600 : 2600
      if (elapsed < minTime) await new Promise((r) => setTimeout(r, minTime - elapsed))

      setResultado(data)
      setEtapa("result")
    } catch (e) {
      console.error("Falha na verificação:", e)
      setErro("Não foi possível concluir a verificação. Tente novamente.")
      setEtapa("entry")
    }
  }

  async function handleEnviarOpiniao(opiniaoMudou: number) {
    if (!resultado) return
    await enviarFeedback(resultado.id, { ...respostasPre, q9: opiniaoMudou })
  }

  function handleRestart() {
    setResultado(null)
    setErro(null)
    setHasImage(false)
    setRespostasPre(null)
    setEtapa("survey")
  }

  return (
    <main className="relative min-h-dvh overflow-hidden bg-gradient-to-br from-primary/35 via-background to-accent/35">
      <div className="pointer-events-none absolute -left-40 -top-40 size-[36rem] rounded-full bg-primary/60 blur-3xl" aria-hidden />
      <div className="pointer-events-none absolute -bottom-40 -right-40 size-[36rem] rounded-full bg-accent/55 blur-3xl" aria-hidden />
      <div className="pointer-events-none absolute -right-24 top-10 size-72 rounded-full bg-primary/40 blur-3xl" aria-hidden />
      <div className="pointer-events-none absolute -left-24 bottom-10 size-72 rounded-full bg-accent/40 blur-3xl" aria-hidden />
      <div className="relative mx-auto flex min-h-dvh w-full max-w-2xl flex-col justify-center px-4 py-8 sm:py-10">
        <div className="relative mb-5 flex items-center justify-center gap-2">
          {(etapa === "entry" || etapa === "result") && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleRestart}
              className="absolute left-0 gap-1 text-muted-foreground"
            >
              <ArrowLeft />
              <span className="hidden sm:inline">Recomeçar</span>
              <span className="sr-only sm:hidden">Recomeçar verificação</span>
            </Button>
          )}
          <BrandLogo />
        </div>

        <div className="rounded-2xl bg-gradient-to-br from-primary via-primary/60 to-accent p-[2px] shadow-2xl shadow-primary/40">
        <div className="relative overflow-hidden rounded-[calc(1rem-2px)] bg-card/90 p-6 backdrop-blur-sm sm:p-8 md:p-10">
          <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-primary to-accent" aria-hidden />
          {etapa === "survey" && (
            <SurveyForm
              onComplete={(r) => {
                setRespostasPre(r)
                setEtapa("entry")
              }}
            />
          )}

          {etapa === "entry" && (
            <div className="flex flex-col gap-4">
              {erro && (
                <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                  <AlertCircle className="size-4 shrink-0" />
                  {erro}
                </div>
              )}
              <NewsEntry onVerify={handleVerify} />
            </div>
          )}

          {etapa === "processing" && <ProcessingScreen hasImage={hasImage} />}

          {etapa === "result" && resultado && (
            <ResultScreen
              resultado={resultado}
              onRestart={handleRestart}
              onEnviarOpiniao={handleEnviarOpiniao}
            />
          )}
        </div>
        </div>

        <footer className="mt-6 text-center text-xs text-muted-foreground">
          Verificação de notícias powered by Minalba
        </footer>
      </div>
    </main>
  )
}
