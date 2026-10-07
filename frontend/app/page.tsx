import Link from "next/link"
import { ArrowRight, BarChart3, FileSearch, Gamepad2, Image as ImageIcon, Layers, SearchCheck, UserCheck } from "lucide-react"

import { BrandLogo } from "@/components/brand-logo"
import { buttonVariants } from "@/components/ui/button"
import { SKILL_INFO } from "@/lib/skills"
import type { SkillCode } from "@/lib/types"
import { cn } from "@/lib/utils"

const SKILL_ICONS: Record<SkillCode, typeof UserCheck> = {
  SOURCE: UserCheck,
  EVIDENCE: SearchCheck,
  CONTEXT: Layers,
  VISUAL: ImageIcon,
}

export default function HomePage() {
  return (
    <main className="relative min-h-dvh overflow-hidden bg-gradient-to-br from-primary/35 via-background to-accent/35">
      <div className="pointer-events-none absolute -left-40 -top-40 size-[36rem] rounded-full bg-primary/60 blur-3xl" aria-hidden />
      <div className="pointer-events-none absolute -bottom-40 -right-40 size-[36rem] rounded-full bg-accent/55 blur-3xl" aria-hidden />
      <div className="relative mx-auto flex min-h-dvh w-full max-w-2xl flex-col justify-center px-4 py-8 sm:py-10">
        <div className="mb-5 flex justify-center">
          <BrandLogo />
        </div>

        <div className="rounded-2xl bg-gradient-to-br from-primary via-primary/60 to-accent p-[2px] shadow-2xl shadow-primary/40">
          <div className="relative flex flex-col gap-6 overflow-hidden rounded-[calc(1rem-2px)] bg-card/90 p-6 backdrop-blur-sm sm:p-8 md:p-10">
            <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-primary to-accent" aria-hidden />

            <header className="flex flex-col gap-2 text-center">
              <h1 className="text-2xl font-bold text-balance text-foreground sm:text-3xl">
                Aprenda a identificar desinformação jogando
              </h1>
              <p className="text-sm leading-relaxed text-pretty text-muted-foreground sm:text-base">
                Em cada rodada você analisa uma notícia, responde uma pergunta e recebe uma explicação. O jogo
                acompanha sua evolução em quatro habilidades.
              </p>
            </header>

            <div className="flex flex-col gap-2 sm:flex-row">
              <Link href="/game" className={cn(buttonVariants(), "h-12 flex-1 gap-2 text-base font-semibold")}>
                <Gamepad2 className="size-5" />
                Jogar
              </Link>
              <Link
                href="/profile"
                className={cn(buttonVariants({ variant: "outline" }), "h-12 flex-1 gap-2 text-sm font-semibold")}
              >
                <BarChart3 className="size-4" />
                Minhas habilidades
              </Link>
            </div>

            <ul className="grid gap-2 sm:grid-cols-2">
              {(Object.keys(SKILL_INFO) as SkillCode[]).map((code) => {
                const Icon = SKILL_ICONS[code]
                return (
                  <li key={code} className="flex items-start gap-3 rounded-xl border border-border bg-background/60 p-3">
                    <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Icon className="size-4" />
                    </span>
                    <div className="flex flex-col">
                      <span className="text-sm font-semibold text-foreground">{SKILL_INFO[code].name}</span>
                      <span className="text-xs leading-snug text-muted-foreground">{SKILL_INFO[code].description}</span>
                    </div>
                  </li>
                )
              })}
            </ul>

            <Link
              href="/verificar"
              className="group flex items-center justify-between gap-3 rounded-xl border border-dashed border-border p-3 text-sm transition hover:border-primary/40 hover:bg-muted"
            >
              <span className="flex items-center gap-2 text-muted-foreground">
                <FileSearch className="size-4 shrink-0" />
                Quer checar uma notícia específica?
              </span>
              <span className="flex shrink-0 items-center gap-1 font-semibold text-primary">
                Verificar notícia
                <ArrowRight className="size-4 transition group-hover:translate-x-0.5" />
              </span>
            </Link>
          </div>
        </div>

        <footer className="mt-6 text-center text-xs text-muted-foreground">
          Verificação de notícias powered by Minalba
        </footer>
      </div>
    </main>
  )
}
