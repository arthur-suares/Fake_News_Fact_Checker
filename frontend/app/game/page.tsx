import { GameScreen } from "@/components/game/game-screen"
import type { Question } from "@/lib/types"

const demoQuestion: Question = {
  id: "demo-question",
  text: "A imagem apresentada realmente mostra o evento descrito?",
  difficulty: 0.45,
  options: {
    A: "Sim, a imagem corresponde ao evento descrito.",
    B: "Não, ela é antiga ou foi usada fora de contexto.",
    C: "Não é possível afirmar com segurança apenas pela imagem.",
  },
  skill_id: "VISUAL",
  explanation: "Uma análise visual correta depende de contexto e validade da imagem.",
}

export default function GamePage() {
  return <GameScreen game={{ id: "demo-game", status: "IN_PROGRESS", user_id: "demo-user", started_at: new Date().toISOString() }} question={demoQuestion} />
}
