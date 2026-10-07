import type {
  Answer,
  Game,
  GameResult,
  Question,
  Skill,
  UserSkillState,
} from "@/lib/types"

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "")

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === "string" ? body.detail : response.statusText
    throw new Error(`${response.status} ${detail}`)
  }
  return (await response.json()) as T
}

export async function createGame(): Promise<Game> {
  return request<Game>("/api/games", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
}

export async function submitAnswer(payload: {
  question_id: string
  game_round_id: string
  selected_option: string
  confidence?: number
  response_time?: number
}): Promise<GameResult> {
  return request<GameResult>(`/api/games/${payload.game_round_id}/answers`, {
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

export type { Answer, Game, GameResult, Question, Skill, UserSkillState }
