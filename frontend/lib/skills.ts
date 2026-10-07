import type { SkillCode } from "@/lib/types"

// Feedback pré-autorado por habilidade (não depende de LLM).
// `nextAction` orienta o usuário para a próxima rodada conforme acertou ou errou.
export const SKILL_INFO: Record<
  SkillCode,
  { name: string; description: string; nextAction: { correct: string; incorrect: string } }
> = {
  SOURCE: {
    name: "Análise de fonte",
    description: "Analisar a origem e a fonte da informação.",
    nextAction: {
      correct: "Continue checando quem publicou e se o veículo tem histórico confiável.",
      incorrect: "Na próxima rodada, procure o autor e o veículo antes de responder. Fontes anônimas ou desconhecidas pedem cautela.",
    },
  },
  EVIDENCE: {
    name: "Avaliação de evidências",
    description: "Avaliar as evidências que sustentam a alegação.",
    nextAction: {
      correct: "Mantenha o hábito de procurar dados, documentos ou estudos citados na notícia.",
      incorrect: "Na próxima rodada, pergunte-se: que prova concreta sustenta essa afirmação? Opinião não é evidência.",
    },
  },
  CONTEXT: {
    name: "Percepção de contexto",
    description: "Perceber contexto omitido, distorcido ou incompatível.",
    nextAction: {
      correct: "Continue comparando data, local e circunstâncias com o que a notícia afirma.",
      incorrect: "Na próxima rodada, confira data, local e o que pode ter ficado de fora. Fatos reais fora de contexto também enganam.",
    },
  },
  VISUAL: {
    name: "Análise visual",
    description: "Validar se uma imagem realmente sustenta a alegação.",
    nextAction: {
      correct: "Continue desconfiando de imagens sem origem clara e verificando se combinam com o fato.",
      incorrect: "Na próxima rodada, observe se a imagem mostra de fato o que a legenda diz. Uma busca reversa ajuda a achar a origem.",
    },
  },
}

export function toSkillCode(value: string): SkillCode | null {
  const code = value.toUpperCase()
  return code in SKILL_INFO ? (code as SkillCode) : null
}
