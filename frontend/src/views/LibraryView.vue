<script setup lang="ts">
import { ref, onMounted } from "vue"
import { getLibrary } from "../api/endpoints"
import { useUserStore } from "../stores/user"
import { useRouter } from "vue-router"

const userStore = useUserStore()
const router = useRouter()
const games = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  if (!userStore.isLoggedIn) { router.push("/login"); return }
  try {
    games.value = await getLibrary()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="library">
    <h2>&#x1F3AE; 我的游戏库</h2>
    <div v-if="loading">加载中...</div>
    <div v-else-if="games.length === 0" class="empty">
      <p>还没有绑定 Steam 账号</p>
      <RouterLink to="/settings">去设置绑定</RouterLink>
    </div>
    <div v-else class="list">
      <div class="item" v-for="g in games" :key="g.game_id">
        <RouterLink :to="`/game/${g.game_id}`">游戏 #{{ g.game_id }}</RouterLink>
        <span class="playtime">{{ Math.round(g.playtime_forever / 60) }} 小时</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
h2 { margin-bottom: 20px; }
.empty { text-align: center; padding: 60px 0; color: #888; }
.empty a { color: #4fc3f7; }
.list { display: flex; flex-direction: column; gap: 8px; }
.item { display: flex; justify-content: space-between; padding: 12px 16px; background: #1a1c24; border-radius: 8px; }
.item a { color: #e1e1e1; text-decoration: none; }
.item a:hover { color: #4fc3f7; }
.playtime { color: #888; font-size: 0.9em; }
</style>
