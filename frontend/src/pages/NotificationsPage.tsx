import { Card } from '../components/ui/Card'

export function NotificationsPage() {
  return (
    <>
      <h1 className="font-mono text-3xl">Notifications</h1>

      <Card className="mt-6 p-4">
        <p className="text-sm text-muted">No notifications yet.</p>
      </Card>
    </>
  )
}
