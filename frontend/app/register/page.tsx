
"use client"

import { useState, type FormEvent } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"

export default function RegisterPage() {
  const router = useRouter()

  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError("")
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          email,
          phone,
          password,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Não foi possível realizar o cadastro.")
      }

      router.push("/login")
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
            Crie sua conta para continuar
          </p>
        </div>

        <form onSubmit={handleRegister} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label htmlFor="name" className="text-sm font-medium">
              Nome completo
            </label>
            <input
              id="name"
              name="name"
              autoComplete="name"
              required
              minLength={2}
              maxLength={100}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="rounded-lg border bg-background px-3 py-2.5 outline-none focus:ring-2 focus:ring-primary"
              placeholder="Digite seu nome"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="email" className="text-sm font-medium">
              E-mail
            </label>
            <input
              id="email"
              name="email"
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
            <label htmlFor="phone" className="text-sm font-medium">
              Número de telefone
            </label>
            <input
              id="phone"
              name="phone"
              type="tel"
              autoComplete="tel"
              required
              maxLength={20}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="rounded-lg border bg-background px-3 py-2.5 outline-none focus:ring-2 focus:ring-primary"
              placeholder="(61) 99999-9999"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="password" className="text-sm font-medium">
              Senha
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              minLength={6}
              maxLength={100}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded-lg border bg-background px-3 py-2.5 outline-none focus:ring-2 focus:ring-primary"
              placeholder="Mínimo de 6 caracteres"
            />
          </div>

          {error && (
            <p role="alert" className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-primary px-4 py-3 font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Criando conta..." : "Criar conta"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Já tem uma conta?{" "}
          <Link href="/login" className="font-medium text-primary underline-offset-4 hover:underline">
            Entrar
          </Link>
        </p>
      </section>
    </main>
  )
}
