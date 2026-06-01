<script setup lang="ts">
import { ref } from "vue"
import { searchGames } from "../api/endpoints"
import type { Game } from "../types"
import GameCard from "../components/GameCard.vue"

const query = ref("")
const results = ref<Game[]>([])
const total = ref(0)
const loading = ref(false)

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  try {
    const res = await searchGames({ q: query.value, page: 1, page_size: 20 })
    results.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="search-page">
    <div class="search-box">
      <input
        v-model="query"
        @keyup.enter="doSearch"
        placeholder="搜索游戏名、类型、标签..."
        class="search-input"
      />
      <button @click="doSearch" :disabled="loading" class="search-btn">
        {{ loading ? "搜索中..." : "搜索" }}
      </button>
    </div>

    <div v-if="total > 0" class="result-info">找到 {{ total }} 个结果</div>

    <div class="grid" v-if="results.length">
      <GameCard v-for="g in results" :key="g.id" :game="g" />
    </div>

    <div v-if="!loading && total === 0 && query" class="empty">
      暂无结果，尝试其他关键词
    </div>
  </div>
</template>

<style scoped>
.search-box { display: flex; gap: 12px; margin-bottom: 24px; }
.search-input { flex: 1; padding: 12px 16px; border-radius: 8px; border: 1px solid #2a2d3a; background: #1a1c24; color: #fff; font-size: 1em; }
.search-btn { padding: 12px 24px; border-radius: 8px; border: none; background: #4fc3f7; color: #0f1117; font-weight: 600; cursor: pointer; }
.search-btn:disabled { opacity: 0.6; }
.result-info { margin-bottom: 16px; color: #888; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.empty { text-align: center; color: #666; padding: 60px 0; }
</style>
