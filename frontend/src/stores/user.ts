import { defineStore } from "pinia"
import { ref, computed } from "vue"
import type { UserInfo } from "../types"
import { getMe } from "../api/endpoints"

export const useUserStore = defineStore("user", () => {
  const user = ref<UserInfo | null>(null)
  const token = ref<string | null>(localStorage.getItem("token"))

  const isLoggedIn = computed(() => !!user.value)

  async function fetchUser() {
    if (!token.value) return
    try {
      user.value = await getMe()
    } catch {
      logout()
    }
  }

  function setToken(t: string) {
    token.value = t
    localStorage.setItem("token", t)
  }

  function setUser(u: UserInfo) {
    user.value = u
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem("token")
  }

  return { user, token, isLoggedIn, fetchUser, setToken, setUser, logout }
})
