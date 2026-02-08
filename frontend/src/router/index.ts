import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/library',
      name: 'Library',
      component: () => import('@/views/LibraryView.vue'),
    },
    {
      path: '/study/:lessonId',
      name: 'Study',
      component: () => import('@/views/StudySessionView.vue'),
      meta: { fullscreen: true },
    },
    {
      path: '/cards/:cardId',
      name: 'CardDetail',
      component: () => import('@/views/CardDetailView.vue'),
    },
    {
      path: '/summary/:lessonId',
      name: 'Summary',
      component: () => import('@/views/SummaryView.vue'),
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/SettingsView.vue'),
    },
  ],
})

export default router
