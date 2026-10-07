import type { UserSkillState } from "@/lib/types"
import { SkillProgress } from "@/components/profile/skill-progress"

type SkillProfileProps = {
  skills: UserSkillState[]
}

export function SkillProfile({ skills }: SkillProfileProps) {
  return (
    <div className="mx-auto max-w-3xl space-y-4 px-4 py-8">
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">Perfil de habilidades</h1>
        <p className="mt-2 text-sm text-slate-600">
          Estado atual de domínio por habilidade para o MVP de avaliação de informação.
        </p>
      </div>

      <div className="space-y-3">
        {skills.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-slate-500">
            Nenhum estado de habilidade registrado ainda.
          </div>
        ) : (
          skills.map((skill) => <SkillProgress key={skill.skill_code} skill={skill} />)
        )}
      </div>
    </div>
  )
}
