import type { ResultadoVerificacao, Veredito, VerificacaoApi } from "@/lib/types"

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "")

const POLL_INTERVAL_MS = 1000
const POLL_TIMEOUT_MS = 60_000

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init)
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = typeof body?.detail === "string" ? body.detail : res.statusText
    throw new Error(`${res.status} ${detail}`)
  }
  return res.json() as Promise<T>
}

// O backend devolve "true", "false", o textualRating cru ou null (backend/app/services/verification.py)
export function mapVerdict(verdict: string | null): Veredito {
  if (!verdict) return "nao_verificado"
  const v = verdict.toLowerCase()
  if (v === "false") return "falso"
  if (v === "true") return "verdadeiro"
  if (/(engan|mislead|distorc|exager|impreci|contexto|context|parcial|partly|half)/.test(v)) return "enganoso"
  return "nao_verificado"
}

export async function criarVerificacao(texto: string, imagem: File | null): Promise<string> {
  const form = new FormData()
  form.append("text", texto)
  if (imagem) form.append("image", imagem)
  const { id } = await request<{ id: string; status: string }>("/api/verifications", {
    method: "POST",
    body: form,
  })
  return id
}

export async function aguardarVerificacao(id: string): Promise<VerificacaoApi> {
  const inicio = Date.now()
  while (Date.now() - inicio < POLL_TIMEOUT_MS) {
    const verificacao = await request<VerificacaoApi>(`/api/verifications/${id}`)
    if (verificacao.status === "completed") return verificacao
    if (verificacao.status === "failed") throw new Error("A verificação falhou no servidor")
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
  }
  throw new Error("Tempo esgotado aguardando a verificação")
}

export async function verificarNoticia(texto: string, imagem: File | null): Promise<ResultadoVerificacao> {
  const id = await criarVerificacao(texto, imagem)
  const verificacao = await aguardarVerificacao(id)
  return {
    id: verificacao.id,
    veredito: mapVerdict(verificacao.verdict),
    classificacao: verificacao.evidence[0]?.rating ?? null,
    evidencias: verificacao.evidence,
    temImagem: Boolean(imagem),
  }
}

export async function enviarFeedback(verificationId: string, answers: Record<string, unknown>): Promise<void> {
  await request(`/api/verifications/${verificationId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  })
}
