import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import AppShell from "./components/shell/AppShell.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: AppShell,
    children: [
      { path: "", name: "home", component: () => import("./views/Home.vue") },
      { path: "corpus", name: "corpus", component: () => import("./views/Corpus.vue") },
      { path: "explorations", name: "explorations", component: () => import("./views/Explorations.vue") },
      { path: "runs", name: "runs", component: () => import("./views/Runs.vue") },
      { path: "workbench", name: "workbench", component: () => import("./views/Workbench.vue") },
      { path: "ui-kit", name: "ui-kit", component: () => import("./views/ComponentShowcase.vue") },
    ],
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
