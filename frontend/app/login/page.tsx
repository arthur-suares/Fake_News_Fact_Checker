"use client"

import { useState } from "react"
import type { FormEvent } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { AlertCircle, Loader2, LogIn, UserPlus } from "lucide-react"

import { BrandLogo } from "@/components/brand-logo"
import { Button } from "@/components/ui/button"
import { describeApiError, login, registerAndLogin } from "@/lib/game-api"

type AuthMode = "login" | "register"

export default function LoginPage() {
  const router = useRouter()
  const [mode, setMode] = useState<AuthMode>("login")
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      if (mode === "register") {
        await registerAndLogin(name, email, phone, password)
      } else {
        await login(email, password)
      }
      router.replace("/game")
      router.refresh()
    } catch (requestError) {
      setError(describeApiError(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="flex min-h-dvh items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <div className="flex justify-center">
          <BrandLogo />
        </div>
        <section className="rounded-xl border border-border bg-card p-6 shadow-sm sm:p-8">
          <div className="mb-6 grid grid-cols-2 border-b border-border">
            {(["login", "register"] as const).map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={mode === option}
                onClick={() => {
                  setMode(option)
                  setError(null)
                }}
                className={`border-b-2 px-3 py-3 text-sm font-semibold transition ${
                  mode === option
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                {option === "login" ? "Entrar" : "Criar conta"}
              </button>
            ))}
          </div>

          <h1 className="text-xl font-semibold text-foreground">
            {mode === "login" ? "Acesse sua conta" : "Crie sua conta"}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Sua evolução fica associada à sua conta.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {mode === "register" && (
              <>
                <label className="block space-y-1.5 text-sm font-medium text-foreground">
                  Nome
                  <input
                    required
                    minLength={2}
                    maxLength={100}
                    autoComplete="name"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    className="h-10 w-full rounded-md border border-input bg-background px-3 font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </label>
                <label className="block space-y-1.5 text-sm font-medium text-foreground">
                  Telefone
                  <input
                    required
                    autoComplete="tel"
                    value={phone}
                    onChange={(event) => setPhone(event.target.value)}
                    className="h-10 w-full rounded-md border border-input bg-background px-3 font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </label>
              </>
            )}
            <label className="block space-y-1.5 text-sm font-medium text-foreground">
              E-mail
              <input
                required
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="h-10 w-full rounded-md border border-input bg-background px-3 font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
            <label className="block space-y-1.5 text-sm font-medium text-foreground">
              Senha
              <input
                required
                type="password"
                minLength={6}
                maxLength={100}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="h-10 w-full rounded-md border border-input bg-background px-3 font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>

            {error && (
              <p role="alert" className="flex items-start gap-2 text-sm text-destructive">
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <span>{error}</span>
              </p>
            )}
            <Button type="submit" disabled={submitting} className="h-11 w-full gap-2">
              {submitting ? (
                <Loader2 className="size-4 animate-spin" />
              ) : mode === "login" ? (
                <LogIn className="size-4" />
              ) : (
                <UserPlus className="size-4" />
              )}
              {submitting ? "Aguarde..." : mode === "login" ? "Entrar" : "Criar conta"}
            </Button>
          </form>
        </section>
        <p className="text-center text-sm text-muted-foreground">
          <Link href="/" className="font-medium text-primary hover:underline">
            Voltar ao início
          </Link>
        </p>
      </div>
    </main>
  )
}