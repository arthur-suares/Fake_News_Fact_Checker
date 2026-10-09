"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { BarChart3, Gamepad2, LogIn, LogOut } from "lucide-react"

import { BrandLogo } from "@/components/brand-logo"
import { clearAccessToken, getAccessToken } from "@/lib/game-api"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { href: "/game", label: "Jogar", Icon: Gamepad2 },
  { href: "/profile", label: "Minhas habilidades", Icon: BarChart3 },
]

export function SiteHeader() {
  const pathname = usePathname()
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    setIsAuthenticated(Boolean(getAccessToken()))
  }, [])

  function handleLogout() {
    clearAccessToken()
    setIsAuthenticated(false)
    router.replace("/login")
  }

  return (
    <header className="border-b border-border bg-card/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-3xl items-center justify-between gap-3 px-4">
        <BrandLogo size="sm" />
        <nav aria-label="Navegação principal" className="flex items-center gap-1">
          {NAV_ITEMS.map(({ href, label, Icon }) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium transition",
                  active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <Icon className="size-4" />
                {/* No mobile só o ícone, para caber ao lado do logo */}
                <span className="sr-only sm:not-sr-only">{label}</span>
              </Link>
            )
          })}
        </nav>
        {isAuthenticated ? (
          <button
            type="button"
            onClick={handleLogout}
            aria-label="Sair da conta"
            title="Sair da conta"
            className="flex size-9 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground"
          >
            <LogOut className="size-4" />
          </button>
        ) : (
          <Link
            href="/login"
            aria-label="Entrar"
            title="Entrar"
            className="flex size-9 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground"
          >
            <LogIn className="size-4" />
          </Link>
        )}
      </div>
    </header>
  )
}
