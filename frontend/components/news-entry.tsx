"use client"

import { useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { ImagePlus, ShieldCheck, X } from "lucide-react"

interface NewsEntryProps {
  onVerify: (news: string, image: File | null) => void
}

export function NewsEntry({ onVerify }: NewsEntryProps) {
  const [news, setNews] = useState("")
  const [image, setImage] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setImage(file)
    const reader = new FileReader()
    reader.onload = () => setPreview(reader.result as string)
    reader.readAsDataURL(file)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (news.trim().length < 3) return
    onVerify(news.trim(), image)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      <header className="flex flex-col items-center gap-3 text-center">
        <span className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <ShieldCheck className="size-6" />
        </span>
        <div>
          <h1 className="text-balance text-2xl font-bold text-foreground">Verificação de notícia</h1>
          <p className="mt-1 text-pretty text-sm text-muted-foreground">
            Cole o texto da notícia e, se quiser, envie uma imagem para análise.
          </p>
        </div>
      </header>

      <div className="flex flex-col gap-2">
        <label htmlFor="news" className="text-sm font-medium text-foreground">
          Cole a notícia
        </label>
        <textarea
          id="news"
          value={news}
          onChange={(e) => setNews(e.target.value)}
          placeholder="Ex.: Uma mensagem afirma que..."
          rows={6}
          className="w-full resize-y rounded-xl border border-input bg-card p-3 text-sm text-foreground shadow-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/40"
        />
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-sm font-medium text-foreground">Imagem (opcional)</span>
        <input ref={fileRef} type="file" accept="image/*" onChange={handleFile} className="sr-only" />

        {image && preview ? (
          <div className="relative overflow-hidden rounded-xl border border-border">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={preview} alt="Pré-visualização da imagem enviada" className="max-h-64 w-full object-contain bg-muted" />
            <button
              type="button"
              onClick={() => {
                setImage(null)
                setPreview(null)
                if (fileRef.current) fileRef.current.value = ""
              }}
              className="absolute right-2 top-2 flex size-8 items-center justify-center rounded-full bg-foreground/70 text-background transition-colors hover:bg-foreground"
              aria-label="Remover imagem"
            >
              <X className="size-4" />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="flex items-center justify-center gap-2 rounded-xl border border-dashed border-accent/60 bg-secondary/50 p-4 text-sm font-medium text-accent transition-colors hover:bg-secondary"
          >
            <ImagePlus className="size-5" />
            Enviar imagem
          </button>
        )}
      </div>

      <Button
        type="submit"
        disabled={news.trim().length < 3}
        className="h-12 w-full bg-primary text-base font-semibold text-primary-foreground hover:bg-primary/90"
      >
        Verificar
      </Button>
    </form>
  )
}
