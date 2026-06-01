<script setup lang="ts">
import type { Game } from "../types"

defineProps<{
  game: Game
  showRelease?: boolean
}>()
</script>

<template>
  <RouterLink :to="`/game/${game.id}`" class="card">
    <div class="img-wrap">
      <img
        v-if="game.cover_image"
        :src="game.cover_image"
        :alt="game.name"
        loading="lazy"
      />
      <div v-else class="placeholder">&#x1F3AE;</div>
      <div v-if="game.discount_percent" class="discount-badge">-{{ game.discount_percent }}%</div>
    </div>
    <div class="card-info">
      <div class="name">{{ game.name }}</div>
      <div class="bottom">
        <div v-if="game.rating" class="rating">&#x2B50; {{ game.rating }}</div>
        <div class="price-row">
          <span v-if="game.final_price !== null && game.final_price > 0" class="price">
            &#xA5;{{ game.final_price }}
          </span>
          <span v-else-if="game.final_price === 0" class="price free">免费</span>
        </div>
      </div>
      <div v-if="showRelease && game.release_date" class="release">
        &#x1F4C5; {{ new Date(game.release_date).toLocaleDateString("zh-CN") }}
      </div>
    </div>
  </RouterLink>
</template>

<style scoped>
.card { background: #1a1c24; border-radius: 10px; overflow: hidden; text-decoration: none; transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; }
.card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.img-wrap { position: relative; aspect-ratio: 16/9; overflow: hidden; background: #252836; }
.img-wrap img { width: 100%; height: 100%; object-fit: cover; }
.placeholder { display: flex; align-items: center; justify-content: center; height: 100%; font-size: 2em; color: #555; }
.discount-badge { position: absolute; top: 8px; right: 8px; background: #4caf50; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 600; }
.card-info { padding: 10px 12px; flex: 1; display: flex; flex-direction: column; }
.name { font-size: 0.9em; color: #e1e1e1; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bottom { display: flex; justify-content: space-between; align-items: center; }
.rating { font-size: 0.85em; color: #ffc107; }
.price { color: #e1e1e1; font-size: 0.9em; font-weight: 600; }
.free { color: #4caf50; }
.release { font-size: 0.8em; color: #888; margin-top: 4px; }
.price-row { margin-top: auto; }
</style>
