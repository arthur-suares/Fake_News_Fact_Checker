export type Veredito = "verdadeiro" | "falso" | "enganoso" | "nao_verificado"

// Formatos retornados pelo backend (backend/app/schemas.py)
export type StatusVerificacao = "processing" | "completed" | "failed"

export interface Evidencia {
  source: string
  rating: string | null
  url: string | null
}

export interface VerificacaoApi {
  id: string
  status: StatusVerificacao
  verdict: string | null
  evidence: Evidencia[]
  created_at: string
}

export interface ResultadoVerificacao {
  id: string
  veredito: Veredito
  classificacao: string | null
  evidencias: Evidencia[]
  temImagem: boolean
}

export interface RespostasPre {
  achavaVerdadeira: number
  quantoAcreditava: number
  costumaVerificar: number
  confiaRedes: number
  abertoMudarOpiniao: number
  probabilidadeCompartilhar: number
  impactoEmocional: number
}

export const PERGUNTAS_PRE = [
  {
    id: "achavaVerdadeira",
    texto: "Antes da verificação, você achava que a notícia era verdadeira?",
    min: "Definitivamente falsa",
    max: "Definitivamente verdadeira",
  },
  {
    id: "quantoAcreditava",
    texto: "O quanto você acreditava na notícia?",
    min: "Nada",
    max: "Totalmente",
  },
  {
    id: "costumaVerificar",
    texto: "Você costuma verificar informações antes de compartilhá-las?",
    min: "Nunca",
    max: "Sempre",
  },
  {
    id: "confiaRedes",
    texto: "Com que frequência você confia em informações recebidas pelas redes sociais?",
    min: "Nunca",
    max: "Sempre",
  },
  {
    id: "abertoMudarOpiniao",
    texto: "Se a verificação indicar o oposto do que você acha, o quão aberto você está para mudar de opinião?",
    min: "Nada aberto",
    max: "Totalmente aberto",
  },
  {
    id: "probabilidadeCompartilhar",
    texto:
      "Qual a probabilidade de você compartilhar essa notícia com outras pessoas (grupos de app, redes sociais, amigos)?",
    min: "Muito improvável",
    max: "Muito provável",
  },
  {
    id: "impactoEmocional",
    texto: "O quanto o assunto desta notícia mexeu com suas emoções?",
    min: "Nada",
    max: "Muito",
  },
] as const
