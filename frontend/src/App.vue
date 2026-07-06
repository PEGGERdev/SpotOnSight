<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterView } from 'vue-router'
import NotificationStack from './components/common/NotificationStack.vue'
import SosLoader from './components/common/SosLoader.vue'
import AppTopNav from './components/layouts/AppTopNav.vue'
import { useApp } from './core/injection'
import { NOTIFICATION_CATEGORIES } from './services/notificationService'

const app = useApp()
const bootLoading = ref(true)
const backendLoading = computed(() => Number(app.state.ui?.backendRequestCount || 0) > 0)

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

onMounted(async () => {
  const startedAt = Date.now()

  try {
    const loaders = []
    if (app.ui.isAuthenticated()) {
      loaders.push(
        app.action('users').refreshProfile(),
        app.service('dashboard').reloadCoreData(),
      )
    } else {
      loaders.push(app.action('spots').reload())
    }
    await Promise.all(loaders)
  } catch (error) {
    if (!app.ui.isAuthenticated()) {
      return
    }
    app.service('notify').push({
      category: NOTIFICATION_CATEGORIES.SYSTEM,
      level: 'error',
      title: 'Initial load failed',
      message: 'Some data could not be loaded on startup.',
      details: String(error?.message || error),
    })
  } finally {
    const elapsed = Date.now() - startedAt
    const minimumVisibleMs = 450
    if (elapsed < minimumVisibleMs) {
      await wait(minimumVisibleMs - elapsed)
    }
    bootLoading.value = false
  }
})

</script>

<template>
  <div class="app-shell position-relative">
    <div class="orb orb--one" />
    <div class="orb orb--two" />

    <AppTopNav />

    <RouterView v-slot="{ Component, route }">
      <Transition name="route-fade" mode="out-in">
        <component :is="Component" :key="route.fullPath" />
      </Transition>
    </RouterView>

    <Transition name="app-loader-fade">
      <div class="app-loader-screen" v-if="bootLoading">
        <div class="app-loader-panel card border-0 shadow-sm">
          <SosLoader size="lg" label="Loading app..." />
          <p class="text-secondary small mb-0">Please wait a moment.</p>
        </div>
      </div>
    </Transition>

    <Transition name="app-loader-fade">
      <div class="app-loader-screen app-loader-screen--action" v-if="!bootLoading && backendLoading">
        <div class="app-loader-panel card border-0 shadow-sm">
          <SosLoader size="lg" label="Working..." />
          <p class="text-secondary small mb-0">Please wait until this request finishes.</p>
        </div>
      </div>
    </Transition>

    <NotificationStack />
  </div>
</template>

<style scoped>
.app-loader-screen {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: color-mix(in srgb, rgba(7, 18, 28, 0.52) 72%, transparent);
  backdrop-filter: blur(10px);
}

.app-loader-screen--action {
  z-index: 1150;
}

.app-loader-panel {
  width: min(100%, 25rem);
  padding: 1.25rem 1.5rem;
  display: grid;
  gap: 0.75rem;
  justify-items: center;
  text-align: center;
}

.app-loader-fade-enter-active,
.app-loader-fade-leave-active {
  transition: opacity 0.18s ease;
}

.app-loader-fade-enter-from,
.app-loader-fade-leave-to {
  opacity: 0;
}
</style>
