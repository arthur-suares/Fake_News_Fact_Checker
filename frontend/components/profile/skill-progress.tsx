import type { UserSkillState } from "@/lib/types"

type SkillProgressProps = {
  skill: UserSkillState
}

export function SkillProgress({ skill }: SkillProgressProps) {
  const value = Math.min(100, Math.max(0, skill.mastery_probability * 100))

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="font-medium text-slate-800">{skill.skill_code}</span>
        <span className="text-sm text-slate-600">{value.toFixed(0)}%</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-gradient-to-r from-sky-500 to-indigo-500"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}
