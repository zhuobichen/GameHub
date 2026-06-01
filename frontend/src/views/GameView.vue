<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import { getGame } from "../api/endpoints"
import type { Game } from "../types"

const route = useRoute()
const game = ref<Game | null>(null)

onMounted(async () => {
  const id = Number(route.params.id)
  if (id) game.value = await getGame(id)
})
</script>

<template>
  <div class="game-detail" v-if="game">
    <div class="hero">
      <img v-if="game.cover_image" :src="game.cover_image" class="cover" alt="" />
      <div class="info">
        <h1>{{ game.name }}</h1>
        <div class="meta">
          <span v-if="game.rating">&#x2B50; {{ game.rating }}</span>
          <span v-if="game.metacritic_score">Metacritic: {{ game.metacritic_score }}</span>
          <span v-if="game.current_players > 0">&#x1F465; {{ game.current_players.toLocaleString() }} 在线</span>
        </div>
        <div class="tags" v-if="game.genres?.length">
          <span class="tag" v-for="g in game.genres" :key="g">{{ g }}</span>
        </div>
        <div class="price" v-if="game.final_price !== null">
          <span v-if="game.discount_percent" class="discount">-{{ game.discount_percent }}%</span>
          <span class="final">&#xA5;{{ game.final_price }}</span>
          <span v-if="game.price && game.price > (game.final_price || 0)" class="original">&#xA5;{{ game.price }}</span>
        </div>
        <p class="desc" v-if="game.description">{{ game.description }}</p>
      </div>
    </div>

    <div class="screenshots" v-if="game.screenshots?.length">
      <h2>截图</h2>
      <div class="shot-grid">
        <img v-for="(s, i) in game.screenshots" :key="i" :src="s" :alt="`screenshot ${i + 1}`" />
      </div>
    </div>
  </div>

  <div v-else class="loading">加载中...</div>
</template>

<style scoped>
.hero { display: flex; gap: 32px; margin-bottom: 40px; }
.cover { width: 300px; border-radius: 12px; }
.info h1 { font-size: 2em; margin-bottom: 12px; color: #fff; }
.meta { display: flex; gap: 16px; color: #888; margin-bottom: 12px; font-size: 0.95em; }
.tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.tag { background: #2a2d3a; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; color: #b0b8c1; }
.price { margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.discount { background: #4caf50; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 0.9em; font-weight: 600; }
.final { font-size: 1.4em; font-weight: 700; color: #fff; }
.original { color: #666; text-decoration: line-through; font-size: 0.9em; }
.desc { color: #b0b8c1; line-height: 1.6; max-width: 600px; }
.screenshots h2 { margin-bottom: 16px; }
.shot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.shot-grid img { width: 100%; border-radius: 8px; }
</style>
