import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  userEmail: string | null
  setTokens: (access: string, refresh: string) => void
  setEmail: (email: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      userEmail: null,
      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true }),
      setEmail: (email) => set({ userEmail: email }),
      logout: () =>
        set({ accessToken: null, refreshToken: null, isAuthenticated: false, userEmail: null }),
    }),
    { name: 'tailoriq-auth' }
  )
)
