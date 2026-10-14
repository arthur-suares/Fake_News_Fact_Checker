"use client"

import { useState, type FormEvent } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"

const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "")

export default function LoginPage() {
  const router = useRouter()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setLoading(true)

    try {
      const body = new URLSearchParams()
      body.set("username", email)
      body.set("password", password)

      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || "Não foi possível entrar. Confira seus dados."
        )
      }

      if (!data.access_token) {
        throw new Error("O servidor não retornou o token de acesso.")
      }

      sessionStorage.setItem("access_token", data.access_token)
      router.push("/")
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro de conexão com o servidor."
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-dvh items-center justify-center bg-gradient-to-br from-primary/20 via-background to-accent/20 px-4 py-10">
      <section className="w-full max-w-md rounded-2xl border bg-card p-6 shadow-xl sm:p-8">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold tracking-tight">Verifica.</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Entre na sua conta para continuar
          </p>
        </div>

        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label htmlFor="email" className="text-sm font-medium">
              E-mail
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded-lg border bg-background px-3 py-2.5 outline-none focus:ring-2 focus:ring-primary"
              placeholder="seu@email.com"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="password" className="text-sm font-medium">
              Senha
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded-lg border bg-background px-3 py-2.5 outline-none focus:ring-2 focus:ring-primary"
              placeholder="Digite sua senha"
            />
          </div>

          {error && (
            <p
              role="alert"
              className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-primary px-4 py-3 font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Ainda não tem uma conta?{" "}
          <Link
            href="/register"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Criar conta
          </Link>
        </p>
      </section>
    </main>
  )
}