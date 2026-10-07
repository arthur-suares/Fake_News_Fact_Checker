import type {
  Answer,
  AnswerResponse,
  AnswerSubmission,
  Game,
  GameRoundPayload,
  Question,
  Skill,
  UserSkillState,
} from "@/lib/types"

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "")

// status 0 = falha de rede (backend fora do ar, CORS, sem internet)
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(status ? `${status} ${detail}` : detail)
    this.name = "ApiError"
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, init)
  } catch {
    throw new ApiError(0, "Não foi possível conectar ao servidor.")
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === "string" ? body.detail : response.statusText
    throw new ApiError(response.status, detail)
  }
  return (await response.json()) as T
}

// Mensagem amigável para exibir ao usuário
export function describeApiError(error: unknown): string {
  if (!(error instanceof ApiError)) return "Algo deu errado. Tente novamente."
  if (error.status === 0) return "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente."
  if (error.status === 404) return "Partida não encontrada. Inicie uma nova partida."
  if (error.status === 422) return `Não foi possível registrar a resposta: ${error.detail}`
  return "O servidor encontrou um erro. Tente novamente em instantes."
}

export async function createGame(): Promise<GameRoundPayload> {
  return request<GameRoundPayload>("/api/games", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
}

// null quando a partida terminou (10 rodadas ou sem perguntas novas)
export async function getNextRound(gameId: string): Promise<GameRoundPayload | null> {
  return request<GameRoundPayload | null>(`/api/games/${encodeURIComponent(gameId)}/next`)
}

export async function submitAnswer(gameId: string, payload: AnswerSubmission): Promise<AnswerResponse> {
  return request<AnswerResponse>(`/api/games/${encodeURIComponent(gameId)}/answers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function getUserSkills(): Promise<UserSkillState[]> {
  const response = await request<{ skills: UserSkillState[] }>("/api/users/me/skills")
  return response.skills
}

export async function getAvailableSkills(): Promise<Skill[]> {
  return [
    { id: "source", code: "SOURCE", name: "Source Analysis" },
    { id: "evidence", code: "EVIDENCE", name: "Evidence Evaluation" },
    { id: "context", code: "CONTEXT", name: "Context Perception" },
    { id: "visual", code: "VISUAL", name: "Visual Analysis" },
  ]
}

export async function getExampleQuestion(): Promise<Question> {
  return {
    id: "demo-question",
    text: "A imagem apresentada realmente mostra o evento descrito?",
    difficulty: 0.45,
    options: {
      A: "Sim, a imagem corresponde ao evento descrito.",
      B: "Não, a imagem é antiga ou fora de contexto.",
      C: "Não dá para afirmar com base na imagem isolada.",
    },
    skill_id: "visual",
    explanation: "Avaliar contexto visual é parte da habilidade VISUAL.",
  }
}

export type { Answer, AnswerResponse, AnswerSubmission, Game, GameRoundPayload, Question, Skill, UserSkillState }
