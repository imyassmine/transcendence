import { Route, Routes } from 'react-router-dom'

import { AuthLayout } from './components/layout/AuthLayout'
import { Layout } from './components/layout/Layout'
import { HomePage } from './pages/HomePage'
import { LegalPage } from './pages/LegalPage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { NotificationsPage } from './pages/NotificationsPage'
import { OrganisationPage } from './pages/OrganisationPage'
import { RequestPage } from './pages/RequestPage'
import { RequestsPage } from './pages/RequestsPage'
import { SignupPage } from './pages/SignupPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
      </Route>

      <Route element={<AuthLayout wide />}>
        <Route path="/privacy" element={<LegalPage kind="privacy" />} />
        <Route path="/terms" element={<LegalPage kind="terms" />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/organisations/:id" element={<OrganisationPage />} />
        <Route path="/requests" element={<RequestsPage />} />
        <Route path="/requests/:id" element={<RequestPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
      </Route>
    </Routes>
  )
}
