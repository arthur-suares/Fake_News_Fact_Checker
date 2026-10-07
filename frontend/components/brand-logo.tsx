import Link from "next/link"
import { ShieldCheck } from "lucide-react"

import { cn } from "@/lib/utils"

type BrandLogoProps = {
  size?: "sm" | "md"
  className?: string
}

export function BrandLogo({ size = "md", className }: BrandLogoProps) {
  return (
    <Link href="/" aria-label="Verifica. — página inicial" className={cn("flex items-center gap-2", className)}>
      <span
        className={cn(
          "flex items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-primary-foreground shadow-lg shadow-primary/30",
          size === "md" ? "size-9" : "size-8",
        )}
      >
        <ShieldCheck className={size === "md" ? "size-5" : "size-4"} />
      </span>
      <span
        className={cn(
          "bg-gradient-to-r from-primary to-accent bg-clip-text font-bold tracking-tight text-transparent",
          size === "md" ? "text-xl" : "text-lg",
        )}
      >
        Verifica.
      </span>
    </Link>
  )
}
