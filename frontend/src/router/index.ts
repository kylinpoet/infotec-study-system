import { createRouter, createWebHistory } from "vue-router";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "portal", component: () => import("../views/PortalView.vue") },
    { path: "/teacher", name: "teacher", component: () => import("../views/TeacherWorkbenchView.vue") },
    { path: "/teacher/settings", name: "teacher-settings", component: () => import("../views/TeacherSettingsView.vue") },
    {
      path: "/teacher/showcase/:courseId?",
      name: "teacher-showcase",
      component: () => import("../views/TeacherShowcaseView.vue")
    },
    { path: "/student", name: "student", component: () => import("../views/StudentCenterView.vue") },
    { path: "/student/settings", name: "student-settings", component: () => import("../views/StudentSettingsView.vue") },
    { path: "/admin", name: "admin", component: () => import("../views/PortalAdminView.vue") },
    { path: "/school-admin", name: "school-admin", component: () => import("../views/SchoolAdminView.vue") }
  ]
});
