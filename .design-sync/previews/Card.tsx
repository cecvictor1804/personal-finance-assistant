import { Card, CardHeader, CardTitle, CardContent, MoneyText } from 'pfa-web'

export function BalanceCard() {
  return (
    <div className="w-72">
      <Card>
        <CardHeader>
          <CardTitle>Checking · Chase ····4821</CardTitle>
        </CardHeader>
        <CardContent>
          <MoneyText cents={482310} className="text-2xl font-semibold" />
        </CardContent>
      </Card>
    </div>
  )
}

export function BudgetCard() {
  return (
    <div className="w-72">
      <Card>
        <CardHeader>
          <CardTitle>Groceries · spent this month</CardTitle>
        </CardHeader>
        <CardContent className="flex items-baseline justify-between">
          <MoneyText cents={-31245} colorize className="text-xl font-semibold" />
          <span className="text-sm text-slate-500">of $400</span>
        </CardContent>
      </Card>
    </div>
  )
}
