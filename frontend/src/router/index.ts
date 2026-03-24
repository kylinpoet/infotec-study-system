import { createRouter, createWebHistory } from "vue-router";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "portal", component: () => import("../views/PortalView.vue") },
    { path: "/teacher", name: "teacher", component: () => import("../views/TeacherWorkbenchView.vue") },
    { path: "/student", name: "student", component: () => import("../views/StudentCenterView.vue") }
  ]
});
