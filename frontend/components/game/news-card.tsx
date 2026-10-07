import { Newspaper } from "lucide-react"

import type { News } from "@/lib/types"

type NewsCardProps = {
  news: News
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
      <div className="flex flex-col gap-2 p-4 sm:p-5">
        <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <Newspaper className="size-3.5" />
          Notícia em análise
        </span>
        <h2 className="text-lg font-bold text-pretty text-foreground sm:text-xl">{news.title}</h2>
        <p className="text-sm leading-relaxed whitespace-pre-line text-foreground/90">{news.content}</p>
      </div>
    </article>
  )
}
