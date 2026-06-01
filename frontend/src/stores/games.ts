import { defineStore } from "pinia"
import { ref } from "vue"
import type { Game } from "../types"
import { getGames, getUpcoming, getRecommendations } from "../api/endpoints"

export const useGameStore = defineStore("games", () => {
  const featured = ref<Game[]>([])
  const upcoming = ref<Game[]>([])
  const recommendations = ref<Game[]>([])

  async function fetchHome() {
    const [recResult, upResult] = await Promise.all([
      getRecommendations(10).catch(() => ({ games: [], based_on: [] })),
      getUpcoming(1).catch(() => ({ items: [], total: 0, page: 1, page_size: 20 })),
    ])
    recommendations.value = recResult.games
    upcoming.value = upResult.items
  }

  return { featured, upcoming, recommendations, fetchHome }
})
