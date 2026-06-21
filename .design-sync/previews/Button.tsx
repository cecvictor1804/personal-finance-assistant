import { Button } from 'pfa-web'

export function Variants() {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button>Add transaction</Button>
      <Button variant="outline">Export CSV</Button>
      <Button variant="ghost">Cancel</Button>
      <Button variant="destructive">Remove account</Button>
    </div>
  )
}

export function Sizes() {
  return (
    <div className="flex items-center gap-3">
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="icon" aria-label="Add">+</Button>
    </div>
  )
}

export function Disabled() {
  return <Button disabled>Syncing…</Button>
}
