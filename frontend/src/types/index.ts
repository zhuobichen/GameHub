export interface Game {
  id: number
  name: string
  name_cn?: string
  description?: string
  steam_app_id?: number
  release_date?: string
  platforms?: string[]
  genres?: string[]
  tags?: string[]
  developers?: string[]
  publishers?: string[]
  cover_image?: string
  screenshots?: string[]
  rating?: number
  metacritic_score?: number
  price?: number
  final_price?: number
  discount_percent: number
  current_players: number
  created_at: string
}

export interface GameListResponse {
  items: Game[]
  total: number
  page: number
  page_size: number
}

export interface SearchResponse {
  items: Game[]
  total: number
  query: string
  page: number
  page_size: number
}

export interface UserInfo {
  id: number
  username: string
  email?: string
  steam_id?: string
  preferences?: Record<string, any>
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserInfo
}
