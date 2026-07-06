import { createRouter, createWebHistory } from 'vue-router'
import { getRoutes } from './registry'
import { ROUTE_PATHS, routeToAuth, routeToHome } from './routeSpec'

export function createAppRouter(appCtx) {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: ROUTE_PATHS.ROOT, redirect: ROUTE_PATHS.MAP },
      ...getRoutes(),
    ],
  })

  router.beforeEach((to) => {
    const isAuth = appCtx.ui.isAuthenticated()

    if (to.meta.requiresAuth && !isAuth) {
      return routeToAuth()
    }
    if (to.meta.guestOnly && isAuth) {
      return routeToHome()
    }
    return true
  })

  return router
}
