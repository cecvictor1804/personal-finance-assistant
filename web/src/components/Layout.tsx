import {
  Bell,
  LayoutDashboard,
  ListOrdered,
  Plug,
  RefreshCw,
  Repeat,
  SlidersHorizontal,
  Target,
  Wallet,
} from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '@/auth/AuthProvider'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { useAlerts, useSyncNow } from '@/hooks/useApi'
import { cn } from '@/lib/utils'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/transactions', label: 'Transactions', icon: ListOrdered, end: false },
  { to: '/budgets', label: 'Budgets', icon: Target, end: false },
  { to: '/recurring', label: 'Recurring', icon: Repeat, end: false },
  { to: '/rules', label: 'Rules', icon: SlidersHorizontal, end: false },
  { to: '/alerts', label: 'Alerts', icon: Bell, end: false },
  { to: '/connections', label: 'Connections', icon: Plug, end: false },
]

export function Layout() {
  const { user, logout } = useAuth()
  const sync = useSyncNow()
  const unreadQ = useAlerts(true)
  const unread = unreadQ.data?.length ?? 0

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-slate-200 bg-white px-3 py-5 sm:flex">
        <div className="mb-6 flex items-center gap-2 px-2">
          <Wallet className="h-6 w-6 text-slate-900" />
          <span className="text-sm font-semibold">Finance Assistant</span>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium',
                  isActive ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:bg-slate-50',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
          <div className="text-sm text-slate-500">{user?.email ?? 'Local session'}</div>
          <div className="flex items-center gap-2">
            <Link
              to="/alerts"
              className="relative rounded-md p-2 text-slate-600 hover:bg-slate-100"
              aria-label="Alerts"
            >
              <Bell className="h-4 w-4" />
              {unread > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
                  {unread > 9 ? '9+' : unread}
                </span>
              )}
            </Link>
            <Button
              variant="outline"
              size="sm"
              onClick={() => sync.mutate()}
              disabled={sync.isPending}
            >
              {sync.isPending ? <Spinner /> : <RefreshCw className="h-4 w-4" />}
              Sync now
            </Button>
            {user && (
              <Button variant="ghost" size="sm" onClick={() => logout()}>
                Sign out
              </Button>
            )}
          </div>
        </header>

        {sync.isError && (
          <div className="bg-red-50 px-6 py-2 text-xs text-red-700">
            Sync failed: {(sync.error as Error).message}
          </div>
        )}
        {sync.isSuccess && (
          <div className="bg-emerald-50 px-6 py-2 text-xs text-emerald-700">
            Synced: {sync.data.added} added, {sync.data.modified} modified,{' '}
            {sync.data.flagged_duplicates} flagged as possible duplicates.
          </div>
        )}

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
