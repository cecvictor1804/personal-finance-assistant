import { Spinner, CenteredSpinner } from 'pfa-web'

export function Inline() {
  return (
    <div className="flex items-center gap-2 text-slate-600">
      <Spinner />
      <span className="text-sm">Syncing transactions…</span>
    </div>
  )
}

export function Centered() {
  return (
    <div className="w-72 rounded-lg border border-slate-200">
      <CenteredSpinner label="Loading accounts…" />
    </div>
  )
}
