
import type {
  GameCreateResponse,
  GameResult,
  UserSkillProfileResponse,
} from "@/lib/types"

const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "")

async function request<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init)

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail =
      typeof body?.detail === "string"
        ? body.detail
        : response.statusText

    throw new Error(`${response.status} ${detail}`)
  }

  return (await response.json()) as T
}

export async function createGame(): Promise<GameCreateResponse> {
  return request<GameCreateResponse>("/api/games", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
}

export async function submitAnswer(
  gameId: string,
  payload: {
    question_id: string
    game_round_id: string
    selected_option: string
    confidence?: number
    response_time?: number
  }
): Promise<GameResult> {
  return request<GameResult>(`/api/games/${gameId}/answers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function getUserSkills(): Promise<UserSkillProfileResponse> {
  return request<UserSkillProfileResponse>("/api/users/me/skills")
}