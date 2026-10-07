import { cn } from "@/lib/utils"

type ConfidenceSelectorProps = {
  value: number | null
  disabled?: boolean
  onChange: (value: number) => void
}

const OPTIONS = [1, 2, 3, 4, 5]

export function ConfidenceSelector({ value, disabled = false, onChange }: ConfidenceSelectorProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Nível de confiança"
      aria-disabled={disabled}
      className={cn("flex flex-col gap-3", disabled && "opacity-60")}
    >
      <p className="text-sm font-medium text-foreground">Qual sua confiança nessa resposta?</p>
      <div className="grid grid-cols-5 gap-2">
        {OPTIONS.map((option) => (
          <button
            key={option}
            type="button"
            role="radio"
            aria-checked={value === option}
            disabled={disabled}
            onClick={() => onChange(option)}
            className={cn(
              "h-11 rounded-lg border text-sm font-semibold transition outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
              value === option
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background text-foreground hover:border-primary/40 hover:bg-muted",
            )}
          >
            {option}
          </button>
        ))}
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Pouca confiança</span>
        <span>Muita confiança</span>
      </div>
    </div>
  )
}
