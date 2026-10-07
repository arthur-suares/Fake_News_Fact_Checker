type ConfidenceSelectorProps = {
  value: number | null
  onChange: (value: number) => void
}

export function ConfidenceSelector({ value, onChange }: ConfidenceSelectorProps) {
  const options = [1, 2, 3, 4, 5]

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-slate-700">Nível de confiança</p>
      <div className="flex gap-2 flex-wrap">
        {options.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => onChange(option)}
            className={`rounded-full border px-3 py-2 text-sm transition ${
              value === option
                ? "border-sky-500 bg-sky-500 text-white"
                : "border-slate-300 bg-white text-slate-700 hover:border-slate-400"
            }`}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  )
}
