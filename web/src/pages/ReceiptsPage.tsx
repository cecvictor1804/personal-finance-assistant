import { CheckCircle2, FileWarning, ReceiptText } from 'lucide-react'
import { MoneyText } from '@/components/MoneyText'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { CenteredSpinner } from '@/components/ui/spinner'
import { useAttachReceipt, useReceipts } from '@/hooks/useApi'
import { formatDate } from '@/lib/utils'
import type { ReceiptStatus } from '@/types'

function StatusBadge({ status }: { status: ReceiptStatus }) {
  const map: Record<ReceiptStatus, { label: string; cls: string }> = {
    pending: { label: 'Processing', cls: 'bg-slate-100 text-slate-600' },
    parsed: { label: 'Parsed', cls: 'bg-sky-100 text-sky-700' },
    matched: { label: 'Matched', cls: 'bg-emerald-100 text-emerald-700' },
    error: { label: 'Failed', cls: 'bg-red-100 text-red-700' },
  }
  const s = map[status]
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${s.cls}`}>{s.label}</span>
}

export function ReceiptsPage() {
  const receiptsQ = useReceipts()
  const attach = useAttachReceipt()

  return (
    <div className="flex flex-col gap-4">
      <h1 className="flex items-center gap-2 text-xl font-semibold">
        <ReceiptText className="h-5 w-5" /> Receipts
      </h1>
      <p className="text-sm text-slate-500">
        Receipts captured in the mobile app are OCR-parsed and matched to a transaction. Confirm a
        suggested match to attach it.
      </p>

      <Card>
        <CardContent className="p-0">
          {receiptsQ.isLoading ? (
            <CenteredSpinner label="Loading receipts…" />
          ) : (receiptsQ.data ?? []).length === 0 ? (
            <p className="p-6 text-sm text-slate-400">
              No receipts yet. Capture one in the mobile app to see it here.
            </p>
          ) : (
            <div className="divide-y divide-slate-100">
              {(receiptsQ.data ?? []).map((r) => (
                <div key={r.id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="truncate font-medium">{r.merchant || 'Unknown merchant'}</span>
                      <StatusBadge status={r.status} />
                    </div>
                    <div className="text-xs text-slate-400">
                      {r.date ? formatDate(r.date) : 'No date'}
                      {r.total_cents > 0 && (
                        <>
                          {' · '}
                          <MoneyText cents={-r.total_cents} />
                        </>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {r.status === 'matched' ? (
                      <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
                        <CheckCircle2 className="h-4 w-4" /> Attached
                      </span>
                    ) : r.matched_txn_id ? (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={attach.isPending}
                        onClick={() =>
                          attach.mutate({ receiptId: r.id, txnId: r.matched_txn_id as string })
                        }
                      >
                        Confirm match
                      </Button>
                    ) : r.status === 'error' ? (
                      <span className="inline-flex items-center gap-1 text-xs text-red-600">
                        <FileWarning className="h-4 w-4" /> Failed
                      </span>
                    ) : (
                      <span className="text-xs text-slate-400">No match found</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
