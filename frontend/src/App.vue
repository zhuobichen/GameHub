<script setup lang="ts">
import { RouterView, RouterLink, useRouter } from "vue-router"
import { useUserStore } from "./stores/user"
import { onMounted } from "vue"

const userStore = useUserStore()
const router = useRouter()

onMounted(() => {
  userStore.fetchUser()
})

function doLogout() {
  userStore.logout()
  router.push("/")
}
</script>

<template>
  <div class="app">
    <header class="header">
      <div class="header-inner">
        <RouterLink to="/" class="logo">&#x1F3AE; GameHub</RouterLink>
        <nav class="nav">
          <RouterLink to="/">&#x1F3E0; 首页</RouterLink>
          <RouterLink to="/search">&#x1F50D; 搜索</RouterLink>
          <RouterLink v-if="userStore.isLoggedIn" to="/library">&#x1F3AE; 我的游戏</RouterLink>
        </nav>
        <div class="user-area">
          <template v-if="userStore.isLoggedIn">
            <RouterLink to="/settings">&#x2699;&#xFE0F; {{ userStore.user?.username }}</RouterLink>
            <button class="btn-link" @click="doLogout">退出</button>
          </template>
          <template v-else>
            <RouterLink to="/login">&#x1F464; 登录</RouterLink>
          </template>
        </div>
      </div>
    </header>
    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app { min-height: 100vh; background: #0f1117; color: #e1e1e1; }
.header { background: #1a1c24; border-bottom: 1px solid #2a2d3a; padding: 0 24px; position: sticky; top: 0; z-index: 100; }
.header-inner { max-width: 1280px; margin: 0 auto; display: flex; align-items: center; height: 56px; gap: 24px; }
.logo { font-size: 1.3em; font-weight: 700; color: #4fc3f7; text-decoration: none; }
.nav { display: flex; gap: 16px; }
.nav a { color: #b0b8c1; text-decoration: none; font-size: 0.9em; transition: color 0.2s; }
.nav a:hover, .nav a.router-link-active { color: #4fc3f7; }
.user-area { margin-left: auto; display: flex; gap: 12px; align-items: center; }
.user-area a { color: #b0b8c1; text-decoration: none; font-size: 0.9em; }
.btn-link { background: none; border: none; color: #666; cursor: pointer; font-size: 0.85em; }
.main { max-width: 1280px; margin: 0 auto; padding: 24px; }
</style>
