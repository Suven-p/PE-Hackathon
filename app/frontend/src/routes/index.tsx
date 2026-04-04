import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/")({
  component: HomeComponent,
})

// TODO: login form here, that redirects to /user/<user_id>
function HomeComponent() {
  return <></>
}
