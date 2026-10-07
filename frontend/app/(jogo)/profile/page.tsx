import { SkillProfile } from "@/components/profile/skill-profile"
import type { UserSkillState } from "@/lib/types"

const demoSkills: UserSkillState[] = [
  { id: "1", user_id: "demo-user", skill_id: "source", skill_code: "SOURCE", mastery_probability: 0.72, updated_at: new Date().toISOString() },
  { id: "2", user_id: "demo-user", skill_id: "evidence", skill_code: "EVIDENCE", mastery_probability: 0.58, updated_at: new Date().toISOString() },
  { id: "3", user_id: "demo-user", skill_id: "context", skill_code: "CONTEXT", mastery_probability: 0.41, updated_at: new Date().toISOString() },
  { id: "4", user_id: "demo-user", skill_id: "visual", skill_code: "VISUAL", mastery_probability: 0.66, updated_at: new Date().toISOString() },
]

export default function ProfilePage() {
  return <SkillProfile skills={demoSkills} />
}
