import { Badge } from "@/components/ui/badge"

interface HealthBadgeProps {
  isHealthy: boolean
}

export function HealthBadge({ isHealthy }: HealthBadgeProps) {
  const label = isHealthy ? "Healthy" : "Unhealthy"
  const variant = isHealthy ? "default" : "destructive"

  return (
    <Badge
      variant={variant}
      className="flex items-center gap-1.5 px-4 py-4 text-xs text-md"
    >
      <span
        className={`size-3 rounded-full ${
          isHealthy ? "bg-green-400" : "bg-red-400"
        }`}
      />
      {label}
    </Badge>
  )
}
