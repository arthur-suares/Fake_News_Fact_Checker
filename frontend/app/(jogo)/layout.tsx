import { SiteHeader } from "@/components/site-header"

// Layout compartilhado por /game e /profile (o grupo "(jogo)" não aparece na URL)
export default function JogoLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <SiteHeader />
      <div className="flex flex-1 flex-col">{children}</div>
    </div>
  )
}
