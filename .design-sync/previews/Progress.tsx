import { Progress } from 'pfa-web'

export function BudgetUsage() {
  return (
    <div className="flex w-72 flex-col gap-4">
      <Progress value={45} />
      <Progress value={82} barClassName="bg-amber-500" />
      <Progress value={100} barClassName="bg-red-500" />
    </div>
  )
}
