import { apiGet, apiPost, apiPut } from "./client"
import type { Game, GameListResponse, SearchResponse, TokenResponse, UserInfo } from "../types"

// Auth
export const login = (username: string, password: string) =>
  apiPost<TokenResponse>("/auth/login", { username, password })

export const register = (username: string, password: string, email?: string) =>
  apiPost<TokenResponse>("/auth/register", { username, password, email })

export const getMe = () => apiGet<UserInfo>("/auth/me")

// Games
export const getGames = (page = 1) =>
  apiGet<GameListResponse>(`/games/?page=${page}`)

export const getUpcoming = (page = 1) =>
  apiGet<GameListResponse>(`/games/upcoming?page=${page}`)

export const getGame = (id: number) => apiGet<Game>(`/games/${id}`)

// Search
export const searchGames = (params: Record<string, any>) =>
  apiPost<SearchResponse>("/search/", params)

// Recommendations
export const getRecommendations = (limit = 10) =>
  apiGet<{ games: Game[]; based_on: string[] }>(`/recommendations/?limit=${limit}`)

// Users
export const updatePreferences = (prefs: Record<string, any>) =>
  apiPut<UserInfo>("/users/preferences", prefs)

export const getLibrary = () => apiGet<any[]>("/users/library")

export const unbindSteam = () => apiDelete("/users/steam")

// Notifications
export const getNotifications = () => apiGet<any[]>("/notifications/")
