<script setup lang="ts">
import { onMounted } from "vue"
import { useGameStore } from "../stores/games"
import GameCard from "../components/GameCard.vue"

const gameStore = useGameStore()

onMounted(() => {
  gameStore.fetchHome()
})
</script>

<template>
  <div class="home">
    <section class="section" v-if="gameStore.recommendations.length">
      <h2>&#x1F525; 为你推荐</h2>
      <div class="grid">
        <GameCard v-for="g in gameStore.recommendations" :key="g.id" :game="g" />
      </div>
    </section>

    <section class="section" v-if="gameStore.upcoming.length">
      <h2>&#x1F4C5; 即将发售</h2>
      <div class="grid">
        <GameCard v-for="g in gameStore.upcoming.slice(0, 10)" :key="g.id" :game="g" showRelease />
      </div>
    </section>
  </div>
</template>

<style scoped>
.section { margin-bottom: 40px; }
.section h2 { font-size: 1.4em; margin-bottom: 16px; color: #fff; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
</style>
