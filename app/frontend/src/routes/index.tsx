import { type FormEvent, useState } from "react"
import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export const Route = createFileRoute("/")({
  component: HomeComponent,
})

function HomeComponent() {
  const navigate = useNavigate()
  const [userId, setUserId] = useState("")
  const [error, setError] = useState("")

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const trimmed = userId.trim()
    if (!trimmed) {
      setError("Please enter your user ID.")
      return
    }

    const parsedId = Number(trimmed)
    if (!Number.isInteger(parsedId) || parsedId <= 0) {
      setError("User ID must be a positive whole number.")
      return
    }

    setError("")
    navigate({
      to: "/users/$id",
      params: { id: String(parsedId) },
    })
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Log In</CardTitle>
        <CardDescription>
          Enter your user ID to continue to your dashboard.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="user-id">User ID</Label>
            <Input
              id="user-id"
              type="number"
              min={1}
              step={1}
              placeholder="e.g. 1"
              value={userId}
              onChange={(event) => {
                setUserId(event.target.value)
                if (error) setError("")
              }}
              aria-invalid={error ? true : undefined}
            />
            {error && <p className="text-xs text-destructive">{error}</p>}
          </div>
          <Button type="submit" className="w-full" size="lg">
            Continue
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
