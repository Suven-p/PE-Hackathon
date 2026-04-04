import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export interface Url {
  id: number
  user_id: number
  short_code: string
  original_url: string
  title: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export function URLTableView({
  urls,
  userId,
}: {
  urls: Url[]
  userId: string
}) {
  return (
    <Table>
      <TableCaption>URLs for user {userId}</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[60px]">ID</TableHead>
          <TableHead>Title</TableHead>
          <TableHead>Original URL</TableHead>
          <TableHead>Short Code</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created At</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {urls.map((url) => (
          <TableRow key={url.id}>
            <TableCell className="font-medium">{url.id}</TableCell>
            <TableCell>{url.title || "—"}</TableCell>
            <TableCell className="max-w-xs truncate">
              <a
                href={url.original_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                {url.original_url}
              </a>
            </TableCell>
            <TableCell>
              <code className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono">
                {url.short_code}
              </code>
            </TableCell>
            <TableCell>
              <Badge variant={url.is_active ? "default" : "secondary"}>
                {url.is_active ? "Active" : "Inactive"}
              </Badge>
            </TableCell>
            <TableCell className="text-muted-foreground">
              {new Date(url.created_at).toLocaleDateString()}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
