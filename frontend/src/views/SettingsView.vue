<script setup lang="ts">
import { ref } from "vue"
import { useUserStore } from "../stores/user"
import { updatePreferences, unbindSteam } from "../api/endpoints"

const userStore = useUserStore()

const genresInput = ref((userStore.user?.preferences?.genres || []).join(", "))
const steamKey = ref("")
const saving = ref(false)

async function savePrefs() {
  saving.value = true
  try {
    const t = genresInput.value.split(",").map(s => s.trim()).filter(Boolean)
    const updated = await updatePreferences({ genres: t })
    userStore.setUser(updated)
  } finally {
    saving.value = false
  }
}

async function doUnbind() {
  if (!confirm("解绑 Steam 将清除游戏库数据，确定？")) return
  await unbindSteam()
  await userStore.fetchUser()
}
</script>

<template>
  <div class="settings" v-if="userStore.user">
    <h2>&#x2699;&#xFE0F; 设置</h2>

    <section class="card">
      <h3>账号信息</h3>
      <p>用户名: {{ userStore.user.username }}</p>
      <p>Steam ID: {{ userStore.user.steam_id || "未绑定" }}</p>
      <button v-if="userStore.user.steam_id" @click="doUnbind" class="btn-danger">解绑 Steam</button>
    </section>

    <section class="card">
      <h3>Steam 绑定</h3>
      <input v-model="steamKey" placeholder="输入 Steam API Key" />
      <p class="hint">在 https://steamcommunity.com/dev/apikey 获取</p>
      <button @click="savePrefs" :disabled="saving">保存 API Key</button>
    </section>

    <section class="card">
      <h3>游戏偏好</h3>
      <label>喜欢的类型（逗号分隔）</label>
      <input v-model="genresInput" placeholder="RPG, FPS, 策略, 动作" />
      <button @click="savePrefs" :disabled="saving">
        {{ saving ? "保存中..." : "保存偏好" }}
      </button>
    </section>
  </div>
</template>

<style scoped>
h2 { margin-bottom: 24px; }
.card { background: #1a1c24; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; }
.card h3 { margin-bottom: 12px; color: #fff; }
.card p { color: #b0b8c1; margin-bottom: 8px; }
.hint { font-size: 0.85em; color: #666 !important; }
input { width: 100%; padding: 10px 14px; margin: 8px 0 12px; border-radius: 8px; border: 1px solid #2a2d3a; background: #0f1117; color: #fff; font-size: 1em; box-sizing: border-box; }
button { padding: 10px 20px; border-radius: 8px; border: none; background: #4fc3f7; color: #0f1117; font-weight: 600; cursor: pointer; }
button:disabled { opacity: 0.5; }
.btn-danger { background: #ff5252; color: #fff; }
label { display: block; color: #b0b8c1; margin-bottom: 4px; }
</style>
