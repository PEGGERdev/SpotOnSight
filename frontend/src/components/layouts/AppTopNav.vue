<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApp } from '../../core/injection'
import { toImageSource } from '../../models/imageMapper'
import { NOTIFICATION_CATEGORIES } from '../../services/notificationService'
import {
  ROUTE_NAMES,
  routeToAdmin,
  routeToAuth,
  routeToHome,
  routeToMap,
  routeToProfile,
  routeToSettings,
  routeToSocial,
  routeToSupport,
} from '../../router/routeSpec'
import ActionButton from '../common/ActionButton.vue'
import TopNavLinks from './TopNavLinks.vue'
import TopNavNotificationsPanel from './TopNavNotificationsPanel.vue'
import TopNavUserMenu from './TopNavUserMenu.vue'
import { useResponsiveTopNav } from './composables/useResponsiveTopNav'

const app = useApp()
const route = useRoute()
const router = useRouter()

const notificationsOpen = ref(false)
const userMenuOpen = ref(false)
const expandedLogEntries = ref({})
const activeLogCategory = ref('all')

const NOTIFICATION_CATEGORY_LABELS = {
  all: 'All',
  [NOTIFICATION_CATEGORIES.SYSTEM]: 'System',
  [NOTIFICATION_CATEGORIES.SOCIAL]: 'Social',
  [NOTIFICATION_CATEGORIES.MAP]: 'Map',
  [NOTIFICATION_CATEGORIES.ACCOUNT]: 'Account',
}

const navEntries = computed(() => {
  const items = [
    { key: ROUTE_NAMES.MAP, label: 'Map', icon: 'bi-map', to: routeToMap() },
  ]
  if (isAuth.value) {
    items.push({ key: ROUTE_NAMES.SOCIAL, label: 'Social', icon: 'bi-people', to: routeToSocial() })
    items.push({ key: ROUTE_NAMES.HOME, label: 'Home', icon: 'bi-house', to: routeToHome() })
    if (Boolean(me.value?.is_admin)) {
      items.unshift({ key: ROUTE_NAMES.ADMIN, label: 'Admin', icon: 'bi-shield-lock', to: routeToAdmin() })
    }
  }
  return items
})

const me = computed(() => app.state.session.user || null)

const logEntries = computed(() => {
  const source = Array.isArray(app.state.notificationLog) ? app.state.notificationLog : []
  return [...source].reverse()
})

const logCategoryOptions = computed(() => {
  const counts = {
    [NOTIFICATION_CATEGORIES.SYSTEM]: 0,
    [NOTIFICATION_CATEGORIES.SOCIAL]: 0,
    [NOTIFICATION_CATEGORIES.MAP]: 0,
    [NOTIFICATION_CATEGORIES.ACCOUNT]: 0,
  }

  for (const entry of logEntries.value) {
    const key = String(entry?.category || NOTIFICATION_CATEGORIES.SYSTEM)
    if (Object.prototype.hasOwnProperty.call(counts, key)) {
      counts[key] += 1
    }
  }

  return [
    { key: 'all', label: NOTIFICATION_CATEGORY_LABELS.all, count: logEntries.value.length },
    ...Object.values(NOTIFICATION_CATEGORIES).map((key) => ({
      key,
      label: NOTIFICATION_CATEGORY_LABELS[key],
      count: counts[key],
    })),
  ]
})

const filteredLogEntries = computed(() => {
  if (activeLogCategory.value === 'all') {
    return logEntries.value
  }
  return logEntries.value.filter((entry) => String(entry?.category || NOTIFICATION_CATEGORIES.SYSTEM) === activeLogCategory.value)
})

const logCount = computed(() => logEntries.value.length)

const userMenuRouteNames = new Set([
  ROUTE_NAMES.SETTINGS,
  ROUTE_NAMES.PROFILE,
  ROUTE_NAMES.SUPPORT,
])

const userMenuRouteActive = computed(() => {
  return userMenuRouteNames.has(String(route.name || ''))
})

const userNavExpanded = computed(() => {
  if (isMobileBottomNav.value) {
    return false
  }
  return !navIconOnly.value || userMenuRouteActive.value
})

const userTriggerClass = computed(() => {
  const classes = ['app-top-nav__tool-btn', 'app-top-nav__user-trigger-btn']
  if (navIconOnly.value) classes.push('app-top-nav__user-trigger-btn--compact')
  if (userNavExpanded.value) classes.push('app-top-nav__user-trigger-btn--expanded')
  if (userMenuOpen.value || userMenuRouteActive.value) {
    classes.push('btn', 'btn-primary', 'app-top-nav__user-trigger--active')
    return classes.join(' ')
  }
  classes.push('btn', 'btn-outline-secondary')
  return classes.join(' ')
})

const incomingCount = computed(() => {
  const list = Array.isArray(app.state.social?.incomingRequests)
    ? app.state.social.incomingRequests
    : []
  return list.length
})

const primaryEntries = computed(() => navEntries.value)

const isAuth = computed(() => app.ui.isAuthenticated())

const show = computed(() => {
  const name = String(route.name || '')
  if (name === ROUTE_NAMES.AUTH) return false
  if (isAuth.value) return true
  return name === ROUTE_NAMES.MAP
})

const navIconOnly = computed(() => compactBySpace.value)

const showUserNavName = computed(() => userNavExpanded.value && !isMobileBottomNav.value)

const userAvatar = computed(() => {
  const raw = String(me.value?.avatar_image || '').trim()
  if (!raw) return ''
  return toImageSource(raw)
})

const userTitle = computed(() => {
  return String(me.value?.display_name || me.value?.username || 'Your account')
})

const userNavName = computed(() => {
  const username = String(me.value?.username || '').trim()
  if (username) return `@${username}`
  return String(me.value?.display_name || 'Profile')
})

const userSubtitle = computed(() => {
  const username = String(me.value?.username || '').trim()
  if (!username) return ''
  return `@${username}`
})

const userDetails = computed(() => {
  const details = []
  const email = String(me.value?.email || '').trim()
  if (email) details.push(email)
  if (incomingCount.value > 0) {
    details.push(`${incomingCount.value} follow request(s)`)
  }
  return details
})

watch(
  () => route.fullPath,
  () => {
    notificationsOpen.value = false
    userMenuOpen.value = false
  },
)

const {
  isMobile,
  isMobileBottomNav,
  compactBySpace,
  navRoot,
  panelRoot,
  primaryLinksRoot,
} = useResponsiveTopNav({
  show,
  notificationsOpen,
  userMenuOpen,
  routePath: computed(() => route.fullPath),
})

function closePanels() {
  notificationsOpen.value = false
  userMenuOpen.value = false
}

function open(entry) {
  if (!entry?.to) return
  closePanels()
  router.push(entry.to)
}

function isActive(entry) {
  return String(route.name || '') === String(entry.key)
}

function logout() {
  closePanels()
  app.action('auth').logout()
  app.service('notify').push({
    category: NOTIFICATION_CATEGORIES.ACCOUNT,
    level: 'info',
    title: 'Logged out',
    message: 'Session ended.',
  })
  router.push(routeToAuth())
}

function openHome() {
  closePanels()
  router.push(routeToHome())
}

function toggleNotifications() {
  userMenuOpen.value = false
  notificationsOpen.value = !notificationsOpen.value
}

function toggleUserMenu() {
  notificationsOpen.value = false
  userMenuOpen.value = !userMenuOpen.value
}

function openMyProfile() {
  const userId = String(me.value?.id || '').trim()
  closePanels()
  router.push(routeToProfile(userId))
}

function openSettings() {
  closePanels()
  router.push(routeToSettings())
}

function openSupport() {
  closePanels()
  router.push(routeToSupport())
}

function clearNotificationLog() {
  app.service('notify').clearLog()
  expandedLogEntries.value = {}
  activeLogCategory.value = 'all'
}

function setLogCategory(categoryKey) {
  activeLogCategory.value = categoryKey
}

function notificationEntryKey(entry) {
  const id = String(entry?.id || '').trim()
  if (id) return id
  const createdAt = String(entry?.createdAt || '').trim()
  const title = String(entry?.title || '').trim()
  return `${createdAt}-${title}`
}

function notificationDetails(entry) {
  return String(entry?.details || '').trim()
}

function hasNotificationDetails(entry) {
  return Boolean(notificationDetails(entry))
}

function isNotificationExpanded(entry) {
  return Boolean(expandedLogEntries.value[notificationEntryKey(entry)])
}

function toggleNotificationExpanded(entry) {
  const key = notificationEntryKey(entry)
  expandedLogEntries.value = {
    ...expandedLogEntries.value,
    [key]: !isNotificationExpanded(entry),
  }
}

function notificationMessage(entry) {
  const message = String(entry?.message || '').trim()
  if (message) return message
  const details = String(entry?.details || '').trim()
  if (!details) return 'No details provided.'
  return details.split(/\r?\n/)[0]
}

function notificationTimestamp(entry) {
  const text = String(entry?.createdAt || '').trim()
  if (!text) return ''

  const date = new Date(text)
  if (Number.isNaN(date.getTime())) return ''

  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function notificationCategory(entry) {
  const key = String(entry?.category || NOTIFICATION_CATEGORIES.SYSTEM)
  return NOTIFICATION_CATEGORY_LABELS[key] || NOTIFICATION_CATEGORY_LABELS.system
}
</script>

<template>
  <nav class="app-top-nav card border-0 shadow-sm" v-if="show" data-aos="fade-down" ref="navRoot">
    <div class="app-top-nav__inner">
      <button class="app-top-nav__brand app-top-nav__brand-button" type="button" aria-label="Go to home" @click="openHome">
        <span class="brand rounded-4"><i class="bi bi-compass-fill"></i></span>
        <div>
          <strong>SpotOnSight</strong>
          <div class="small text-secondary">Navigation</div>
        </div>
      </button>

      <div class="app-top-nav__center">
        <div ref="primaryLinksRoot">
          <TopNavLinks
            :entries="primaryEntries"
            :nav-icon-only="navIconOnly"
            :mobile-bottom-nav="isMobileBottomNav"
            :is-active="isActive"
            :on-open="open"
          />
        </div>
      </div>

      <div class="app-top-nav__tools">
        <template v-if="isAuth">
          <ActionButton
            :class-name="notificationsOpen ? 'btn btn-primary app-top-nav__tool-btn app-top-nav__tool-btn--icon-only' : 'btn btn-outline-secondary app-top-nav__tool-btn app-top-nav__tool-btn--icon-only'"
            icon="bi-bell"
            :label="isMobileBottomNav ? '' : (navIconOnly ? '' : `Notifications (${logCount})`)"
            :icon-only="isMobileBottomNav || navIconOnly"
            aria-label="Open notification log"
            @click="toggleNotifications"
          />
          <ActionButton
            :class-name="userTriggerClass"
            aria-label="Open user menu"
            @click="toggleUserMenu"
          >
            <span :class="userNavExpanded ? 'app-top-nav__user-trigger app-top-nav__user-trigger--expanded' : 'app-top-nav__user-trigger'">
              <span class="app-top-nav__user-avatar" v-if="userAvatar">
                <img :src="userAvatar" alt="profile avatar" loading="lazy" />
              </span>
              <span class="app-top-nav__user-avatar app-top-nav__user-avatar--empty" v-else>
                <i class="bi bi-person"></i>
              </span>
              <span :class="showUserNavName ? 'app-top-nav__user-name app-top-nav__user-name--visible' : 'app-top-nav__user-name'">{{ userNavName }}</span>
            </span>
          </ActionButton>
        </template>
        <template v-else>
          <ActionButton
            class-name="btn btn-outline-primary app-top-nav__tool-btn"
            icon="bi-box-arrow-in-right"
            label="Sign In"
            @click="router.push(routeToAuth())"
          />
          <ActionButton
            class-name="btn btn-primary app-top-nav__tool-btn"
            icon="bi-person-plus"
            label="Register"
            @click="router.push(routeToAuth())"
          />
        </template>
      </div>
    </div>

    <Transition name="app-nav-expand" v-if="isAuth">
      <div class="app-top-nav__panel" ref="panelRoot" v-if="notificationsOpen || userMenuOpen">
        <TopNavNotificationsPanel
          v-if="notificationsOpen"
          :entries="filteredLogEntries"
          :category-options="logCategoryOptions"
          :active-category="activeLogCategory"
          :category-for="notificationCategory"
          :is-expanded="isNotificationExpanded"
          :has-details="hasNotificationDetails"
          :message-for="notificationMessage"
          :details-for="notificationDetails"
          :timestamp-for="notificationTimestamp"
          :on-toggle-expanded="toggleNotificationExpanded"
          :on-select-category="setLogCategory"
          :on-clear="clearNotificationLog"
        />

        <TopNavUserMenu
          v-if="userMenuOpen"
          :title="userTitle"
          :subtitle="userSubtitle"
          :avatar="userAvatar"
          :details="userDetails"
          :on-profile="openMyProfile"
          :on-settings="openSettings"
          :on-support="openSupport"
          :on-logout="logout"
        />
      </div>
    </Transition>
  </nav>
</template>
