<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useUserStore } from "../stores/user"
import { login, register as apiRegister } from "../api/endpoints"

const router = useRouter()
const userStore = useUserStore()

const mode = ref<"login" | "register">("login")
const username = ref("")
const email = ref("")
const password = ref("")
const error = ref("")

async function submit() {
  error.value = ""
  try {
    const fn = mode.value === "login" ? login : apiRegister
    const res = await fn(username.value, password.value, email.value || undefined)
    userStore.setToken(res.access_token)
    userStore.setUser(res.user)
    router.push("/")
  } catch (e: any) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="login-page">
    <form @submit.prevent="submit" class="form">
      <h2>{{ mode === "login" ? "登录" : "注册" }}</h2>
      <div v-if="error" class="error">{{ error }}</div>
      <input v-model="username" placeholder="用户名" required />
      <input v-if="mode === 'register'" v-model="email" placeholder="邮箱 (选填)" type="email" />
      <input v-model="password" placeholder="密码" type="password" required />
      <button type="submit">{{ mode === "login" ? "登录" : "注册" }}</button>
      <p class="switch">
        {{ mode === "login" ? "没有账号？" : "已有账号？" }}
        <a href="#" @click.prevent="mode = mode === 'login' ? 'register' : 'login'">
          {{ mode === "login" ? "去注册" : "去登录" }}
        </a>
      </p>
    </form>
  </div>
</template>

<style scoped>
.login-page { display: flex; justify-content: center; padding-top: 80px; }
.form { width: 360px; display: flex; flex-direction: column; gap: 16px; }
.form h2 { text-align: center; color: #fff; }
.error { background: #ff525220; color: #ff5252; padding: 8px 12px; border-radius: 6px; font-size: 0.9em; }
input { padding: 10px 14px; border-radius: 8px; border: 1px solid #2a2d3a; background: #1a1c24; color: #fff; font-size: 1em; }
button { padding: 12px; border-radius: 8px; border: none; background: #4fc3f7; color: #0f1117; font-weight: 600; cursor: pointer; font-size: 1em; }
.switch { text-align: center; color: #888; font-size: 0.9em; }
.switch a { color: #4fc3f7; }
</style>
