import { Input } from 'pfa-web'

export function States() {
  return (
    <div className="flex w-72 flex-col gap-3">
      <Input placeholder="Search transactions…" />
      <Input defaultValue="Whole Foods Market" />
      <Input type="number" defaultValue={42.5} />
      <Input placeholder="Disabled" disabled />
    </div>
  )
}
