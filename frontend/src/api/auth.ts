import api from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  expires_in: number
}

export async function login(data: LoginRequest): Promise<AuthTokens> {
  const res = await api.post('/auth/login', data)
  return res.data
}

export async function register(data: RegisterRequest): Promise<{ user_id: string; message: string }> {
  const res = await api.post('/auth/register', data)
  return res.data
}

export async function refreshToken(token: string): Promise<{ access_token: string }> {
  const res = await api.post('/auth/refresh', { refresh_token: token })
  return res.data
}
