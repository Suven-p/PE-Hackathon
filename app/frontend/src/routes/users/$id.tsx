import { useState } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { createFileRoute } from "@tanstack/react-router"
import {
  queryOptions,
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import {
  ArrowRight01Icon,
  CheckmarkCircle01Icon,
  Copy01Icon,
  Loading02Icon,
} from "@hugeicons/core-free-icons"

import { API_BASE_URL } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { URLTableView, type Url } from "@/components/custom/URLTableView"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const userQueryOptions = (id: string) =>
  queryOptions({
    queryKey: ["user", id],
    queryFn: (): Promise<Url[]> =>
      fetch(`${API_BASE_URL}/urls?user_id=${id}`).then((r) => r.json()),
  })

export const Route = createFileRoute("/users/$id")({
  component: UserComponent,
  loader: ({ context, params }) => {
    context.queryClient.ensureQueryData(userQueryOptions(params.id))
  },
})

function UserComponent() {
  const { id } = Route.useParams()
  const queryClient = useQueryClient()
  const { data: urls } = useSuspenseQuery(userQueryOptions(id))

  const [url, setUrl] = useState("")
  const [copied, setCopied] = useState(false)

  const shortenMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE_URL}/urls`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: Number(id),
          original_url: url,
        }),
      })
      if (!res.ok) throw new Error("Server error")
      return res.json() as Promise<{ short_url: string }>
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", id] })
    },
  })

  const handleShorten = () => {
    if (url.trim()) shortenMutation.mutate()
  }

  const handleCopy = async () => {
    if (!shortenMutation.data?.short_url) return
    await navigator.clipboard.writeText(shortenMutation.data.short_url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !shortenMutation.isPending) {
      handleShorten()
    }
  }

  return (
    <div className="p-6 gap-10 flex flex-col gap-5 w-200">
      <Card>
        <CardHeader>
          <CardTitle>Shorten a URL</CardTitle>
          <CardDescription>
            Enter any URL below to generate a short link.
          </CardDescription>
        </CardHeader>

        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="url-input">Destination URL</Label>
            <Input
              id="url-input"
              type="url"
              placeholder="https://very.long/url/goes/here"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value)
                if (shortenMutation.isError) shortenMutation.reset()
              }}
              onKeyDown={handleKeyDown}
              aria-invalid={shortenMutation.isError ? true : undefined}
              className="h-9 text-sm"
            />
            {shortenMutation.isError && (
              <p className="text-xs text-destructive">
                {shortenMutation.error?.message ?? "Something went wrong"}
              </p>
            )}
          </div>

          <Button
            id="shorten-btn"
            onClick={handleShorten}
            disabled={shortenMutation.isPending || !url.trim()}
            className="w-full"
            size="lg"
          >
            {shortenMutation.isPending ? (
              <>
                <HugeiconsIcon
                  icon={Loading02Icon}
                  data-icon="inline-start"
                  className="animate-spin"
                />
                Shortening…
              </>
            ) : (
              <>
                <HugeiconsIcon icon={ArrowRight01Icon} data-icon="inline-end" />
                Shorten URL
              </>
            )}
          </Button>
        </CardContent>

        {shortenMutation.isSuccess && shortenMutation.data?.short_url && (
          <>
            <Separator />
            <CardFooter className="flex flex-col items-start gap-3 pt-4">
              <div className="flex w-full items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">
                  Your short link
                </span>
                <Badge variant="secondary">
                  <HugeiconsIcon
                    icon={CheckmarkCircle01Icon}
                    data-icon="inline-start"
                  />
                  Ready
                </Badge>
              </div>

              <div className="flex w-full items-center gap-2 rounded-md border border-border bg-muted/40 px-3 py-2">
                <span className="min-w-0 flex-1 truncate text-sm font-medium text-primary">
                  {shortenMutation.data.short_url}
                </span>
                <Button
                  id="copy-btn"
                  variant="ghost"
                  size="icon-sm"
                  onClick={handleCopy}
                  aria-label="Copy shortened URL"
                >
                  <HugeiconsIcon
                    icon={copied ? CheckmarkCircle01Icon : Copy01Icon}
                  />
                </Button>
              </div>

              {copied && (
                <p className="text-xs text-muted-foreground">
                  Copied to clipboard!
                </p>
              )}
            </CardFooter>
          </>
        )}
      </Card>
      <URLTableView urls={urls} userId={id} />
    </div>
  )
}
