import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '../components/ui/Button'
import { TextField } from '../components/ui/TextField'
import { isValidEmail } from '../utils/validation'

type LoginErrors = {
  email?: string
  password?: string
}

export function LoginPage() {
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<LoginErrors>({})

  function validate(): LoginErrors {
    const found: LoginErrors = {}

    if (!email.trim()) found.email = 'Required'
    else if (!isValidEmail(email)) found.email = 'Not a valid email'

    if (!password) found.password = 'Required'

    return found
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()

    const found = validate()
    setErrors(found)
    if (Object.keys(found).length > 0) return

    navigate('/')
  }

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <p className="border-b border-fg pb-3 font-mono text-xs tracking-widest uppercase">
          Transcendence
        </p>

        <h1 className="mt-6 font-mono text-2xl">Log in</h1>
        <p className="mt-1 text-sm text-muted">Find and erase your data online.</p>

        <form onSubmit={handleSubmit} noValidate className="mt-8 flex flex-col gap-5">
          <TextField
            label="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            error={errors.email}
          />

          <TextField
            label="Password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            error={errors.password}
          />

          <Button type="submit" className="mt-2 w-full">
            Log in
          </Button>
        </form>
      </div>
    </div>
  )
}
