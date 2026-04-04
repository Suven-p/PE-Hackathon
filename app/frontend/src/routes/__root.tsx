import { HugeiconsIcon } from "@hugeicons/react"
import { useQuery } from "@tanstack/react-query"
import { Link02Icon } from "@hugeicons/core-free-icons"
import type { QueryClient } from "@tanstack/react-query"
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools"
import { Outlet, createRootRouteWithContext } from "@tanstack/react-router"

import { API_BASE_URL } from "@/lib/api"
import { ModeToggle } from "@/components/mode-toggle"
import { HealthBadge } from "@/components/custom/HealthBadge"

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()(
  {
    component: RootComponent,
  }
)

function RootComponent() {
  const { data, isError, isPending } = useQuery({
    queryKey: ["health"],
    queryFn: () =>
      fetch(`${API_BASE_URL}/health`).then((r) => r.json()) as Promise<{
        status: string
      }>,
    refetchInterval: 200,
    retry: false,
  })

  const isHealthy = !isError && !isPending && data?.status === "ok"

  return (
    <>
      <div className="fixed right-4 top-4 z-50">
        <div className="flex justify-center items-center gap-4">
          <HealthBadge isHealthy={isHealthy} />
          <ModeToggle />
        </div>
      </div>
      <div className="flex min-h-screen flex-col items-center bg-background px-4 py-20">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <div className="mb-2 flex items-center justify-center rounded-full bg-primary/10 p-3">
            <HugeiconsIcon icon={Link02Icon} className="size-6 text-primary" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            URL Shortener
          </h1>
        </div>
        <Outlet />
      </div>
      <TanStackRouterDevtools position="bottom-left" />
    </>
  )
}
