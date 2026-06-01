import { createRouter, createWebHistory } from "vue-router"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: () => import("../views/HomeView.vue") },
    { path: "/search", name: "search", component: () => import("../views/SearchView.vue") },
    { path: "/game/:id", name: "game", component: () => import("../views/GameView.vue") },
    { path: "/library", name: "library", component: () => import("../views/LibraryView.vue") },
    { path: "/settings", name: "settings", component: () => import("../views/SettingsView.vue") },
    { path: "/login", name: "login", component: () => import("../views/LoginView.vue") },
  ],
})

export default router
