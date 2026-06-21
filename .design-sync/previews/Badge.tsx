import { Badge } from 'pfa-web'

export function Statuses() {
  return (
    <div className="flex flex-wrap gap-2">
      <Badge className="bg-emerald-100 text-emerald-700">Posted</Badge>
      <Badge className="bg-amber-100 text-amber-700">Pending</Badge>
      <Badge className="bg-slate-100 text-slate-600">Manual entry</Badge>
      <Badge className="bg-red-100 text-red-700">Possible duplicate</Badge>
    </div>
  )
}
