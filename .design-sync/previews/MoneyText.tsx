import { MoneyText } from 'pfa-web'

export function Colorized() {
  return (
    <div className="flex flex-col gap-1 text-lg">
      <MoneyText cents={482310} colorize />
      <MoneyText cents={-12999} colorize />
      <MoneyText cents={0} colorize />
    </div>
  )
}

export function Neutral() {
  return (
    <div className="flex flex-col gap-1 text-lg">
      <MoneyText cents={1500000} />
      <MoneyText cents={-4250} />
    </div>
  )
}
