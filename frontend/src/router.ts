import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "home",
    component: () => import("./views/Home.vue"),
  },
  {
    path: "/ui-kit",
    name: "ui-kit",
    component: () => import("./views/ComponentShowcase.vue"),
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
