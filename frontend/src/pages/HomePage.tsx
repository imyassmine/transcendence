import { Button } from '../components/ui/Button'

const ROWS = [
  { n: '01', site: '42 paris', type: 'broker', risk: 80, state: 'todo' },
  { n: '02', site: '42 lisbon', type: 'search', risk: 60, state: 'J-8' },
  { n: '03', site: '42 tokyo', type: 'social', risk: 30, state: 'erased' },
]

export function HomePage() {
  return (
    <>
      <h1 className="font-mono text-3xl leading-tight md:text-4xl">
        Your data is held by 3 organisations.
      </h1>
      <p className="mt-3 text-muted">1 erasure request in progress.</p>

      <table className="mt-10 w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border text-left font-mono text-xs text-muted uppercase">
            <th className="py-2 font-normal">N°</th>
            <th className="py-2 font-normal">Organisation</th>
            <th className="py-2 font-normal">Type</th>
            <th className="py-2 font-normal">Risk</th>
            <th className="py-2 text-right font-normal">State</th>
          </tr>
        </thead>
        <tbody>
          {ROWS.map((row) => (
            <tr key={row.n} className="border-b border-border">
              <td className="py-3 font-mono text-muted">{row.n}</td>
              <td className="py-3 font-medium">{row.site}</td>
              <td className="py-3 text-muted">{row.type}</td>
              <td className="py-3 font-mono tabular-nums">{row.risk}</td>
              <td className="py-3 text-right">
                {row.state === 'todo' && <Button size="sm">Start</Button>}
                {row.state === 'erased' && (
                  <span className="font-mono text-xs text-success">ERASED</span>
                )}
                {row.state.startsWith('J-') && (
                  <span className="font-mono text-xs text-warning">{row.state}</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}
