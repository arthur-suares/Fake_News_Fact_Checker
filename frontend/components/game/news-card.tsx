import { CalendarDays, ExternalLink, Megaphone, Newspaper, ShieldCheck } from "lucide-react"

import type { News, NewsDetails } from "@/lib/types"

type NewsCardProps = {
  news: News
}

function DetailItem({ icon: Icon, label, value }: { icon: typeof Megaphone; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div className="flex min-w-0 flex-col">
        <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</dt>
        <dd className="text-sm break-words text-foreground">{value}</dd>
      </div>
    </div>
  )
}

// Alegação checada do dataset: o texto que circulou, quem espalhou, quando e
// o link para a checagem original, para o jogador poder investigar.
function ClaimDetails({ details }: { details: NewsDetails }) {
  const checker = details.fact_checker ?? details.fact_checker_site

  return (
    <>
      <blockquote className="border-l-4 border-primary/40 pl-3 text-sm leading-relaxed whitespace-pre-line text-foreground/90 sm:text-base">
        “{details.claim}”
      </blockquote>

      <dl className="grid gap-3 rounded-lg bg-muted/60 p-3 sm:grid-cols-3">
        <DetailItem
          icon={Megaphone}
          label="Quem disse / onde circulou"
          value={details.origin ?? "Origem não identificada"}
        />
        {details.checked_on && <DetailItem icon={CalendarDays} label="Data da checagem" value={details.checked_on} />}
        {checker && <DetailItem icon={ShieldCheck} label="Checada por" value={checker} />}
      </dl>

      {details.source_url && (
        <a
          href={details.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex w-fit items-center gap-1.5 text-sm font-semibold text-primary underline-offset-4 hover:underline"
        >
          <ExternalLink className="size-4" />
          Consultar a checagem{details.fact_checker_site ? ` em ${details.fact_checker_site}` : ""}
        </a>
      )}
    </>
  )
}

export function NewsCard({ news }: NewsCardProps) {
  return (
    <article className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      {news.image_url && (
        // eslint-disable-next-line @next/next/no-img-element -- imagens vêm de URLs externas variadas
        <img
          src={news.image_url}
          alt="Imagem que acompanha a notícia"
          className="max-h-80 w-full bg-muted object-cover"
        />
      )}
      <div className="flex flex-col gap-3 p-4 sm:p-5">
        <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <Newspaper className="size-3.5" />
          {news.details ? "Alegação em análise" : "Notícia em análise"}
        </span>
        <h2 className="text-lg font-bold text-pretty text-foreground sm:text-xl">{news.title}</h2>
        {news.details ? (
          <ClaimDetails details={news.details} />
        ) : (
          <p className="text-sm leading-relaxed whitespace-pre-line text-foreground/90">{news.content}</p>
        )}
      </div>
    </article>
  )
}
