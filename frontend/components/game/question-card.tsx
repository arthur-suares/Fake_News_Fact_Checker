import type { Question } from "@/lib/types"

type QuestionCardProps = {
  question: Question | null
  onAnswer: (option: string) => void
}

export function QuestionCard({ question, onAnswer }: QuestionCardProps) {
  if (!question) {
    return <div className="rounded-xl border border-slate-200 bg-slate-50 p-6 text-slate-600">Nenhuma pergunta ativa.</div>
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <span className="rounded-full bg-sky-100 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-sky-700">
          {question.skill_id}
        </span>
        <span className="text-sm text-slate-500">Dificuldade {question.difficulty.toFixed(2)}</span>
      </div>

      <h2 className="mb-5 text-xl font-semibold text-slate-900">{question.text}</h2>

      <div className="grid gap-3">
        {Object.entries(question.options).map(([key, value]) => (
          <button
            key={key}
            type="button"
            onClick={() => onAnswer(key)}
            className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-left text-slate-700 transition hover:border-sky-300 hover:bg-sky-50"
          >
            <span className="mr-2 font-semibold text-slate-900">{key}.</span>
            {value}
          </button>
        ))}
      </div>
    </div>
  )
}
