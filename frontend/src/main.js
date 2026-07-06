import { createApp } from 'vue'
import { watch } from 'vue'
import AOS from 'aos'
import { buildAppContext } from './bootstrap/appBootstrap'
import { APP_CTX_KEY } from './core/injection'
import { createAppRouter } from './router'
import { ROUTE_NAMES, ROUTE_PATHS, routeToAuth } from './router/routeSpec'
import {
  persistFilterSubscriptions,
  persistSession,
  persistTheme,
  syncUserFilterSubscriptions,
} from './stores/appState'

import 'bootswatch/dist/flatly/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import 'aos/dist/aos.css'
import './style.css'
import 'cesium/Build/Cesium/Widgets/widgets.css'
import App from './App.vue'

const appCtx = buildAppContext()
const router = createAppRouter(appCtx)
const runtime = appCtx.service('runtime')
const platform = appCtx.service('platform')

await platform.hydrateState()

function applyTheme(theme) {
  const next = String(theme || 'light').toLowerCase() === 'dark' ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', next)
  document.body.classList.toggle('theme-dark', next === 'dark')
}

applyTheme(appCtx.state.ui.theme)

AOS.init({
  duration: 900,
  once: true,
  easing: 'ease-in-out-cubic',
  offset: 18,
})

await platform.initializeRuntimeLifecycle(runtime)
await platform.applyStatusBarTheme()

router.afterEach(() => {
  setTimeout(() => {
    AOS.refreshHard()
  }, 0)
  void runtime.tick({ notify: true })
})

watch(
  () => [appCtx.state.session.token, appCtx.state.session.user],
  () => {
    persistSession(appCtx.state)
    void platform.persistSession()
  },
  { deep: true },
)

watch(
  () => String(appCtx.state.session.user?.id || '').trim(),
  () => {
    if (platform.isNative()) {
      void platform.syncUserFilterSubscriptions()
      return
    }
    syncUserFilterSubscriptions(appCtx.state)
  },
  { immediate: true },
)

watch(
  () => appCtx.state.session.token,
  (token) => {
    const hasToken = Boolean(String(token || '').trim())
    if (hasToken) {
      runtime.start()
      void runtime.tick({ notify: true })
      return
    }

    runtime.stop()

    const currentRoute = router.currentRoute.value
    if (String(currentRoute?.name || '') === ROUTE_NAMES.AUTH) return
    if (currentRoute?.meta?.requiresAuth) {
      void router.replace(routeToAuth())
    }
  },
  { immediate: true },
)

router.isReady().then(() => {
  const currentRoute = router.currentRoute.value
  if (!appCtx.ui.isAuthenticated() && String(currentRoute?.name || '') === ROUTE_NAMES.AUTH && !currentRoute?.meta?.guestOnly) {
    void router.replace(ROUTE_PATHS.MAP)
  }
})

watch(
  () => appCtx.state.ui.theme,
  () => {
    applyTheme(appCtx.state.ui.theme)
    persistTheme(appCtx.state)
    void platform.persistTheme()
    void platform.applyStatusBarTheme()
  },
)

watch(
  () => appCtx.state.map.filterSubscriptions,
  () => {
    persistFilterSubscriptions(appCtx.state)
    void platform.persistFilterSubscriptions()
  },
  { deep: true },
)

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    void platform.disposeRuntimeLifecycle()
  })
}

const app = createApp(App)
app.provide(APP_CTX_KEY, appCtx)
app.use(router)
app.mount('#app')
