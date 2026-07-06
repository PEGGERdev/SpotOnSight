import { UI_SCREENS } from '../core/uiElements'
import { asText } from '../utils/sanitizers'

export const ROUTE_NAMES = Object.freeze({
  ADMIN: UI_SCREENS.ADMIN,
  AUTH: UI_SCREENS.AUTH,
  HOME: UI_SCREENS.HOME,
  MAP: UI_SCREENS.MAP,
  SOCIAL: UI_SCREENS.SOCIAL,
  SETTINGS: UI_SCREENS.SETTINGS,
  PROFILE: UI_SCREENS.PROFILE,
  SUPPORT: UI_SCREENS.SUPPORT,
})

export const ROUTE_PATHS = Object.freeze({
  ROOT: '/',
  ADMIN: '/admin',
  AUTH: '/auth',
  HOME: '/home',
  MAP: '/map',
  SOCIAL: '/social',
  SETTINGS: '/settings',
  PROFILE: '/profile/:userId?',
  SUPPORT: '/support',
})

const GUEST_ONLY_META = Object.freeze({ guestOnly: true })
const REQUIRES_AUTH_META = Object.freeze({ requiresAuth: true })

export const ROUTE_BINDINGS = Object.freeze([
  Object.freeze({
    key: ROUTE_NAMES.ADMIN,
    path: ROUTE_PATHS.ADMIN,
    name: ROUTE_NAMES.ADMIN,
    screen: UI_SCREENS.ADMIN,
    meta: REQUIRES_AUTH_META,
  }),
  Object.freeze({
    key: ROUTE_NAMES.AUTH,
    path: ROUTE_PATHS.AUTH,
    name: ROUTE_NAMES.AUTH,
    screen: UI_SCREENS.AUTH,
    meta: GUEST_ONLY_META,
  }),
  Object.freeze({
    key: ROUTE_NAMES.HOME,
    path: ROUTE_PATHS.HOME,
    name: ROUTE_NAMES.HOME,
    screen: UI_SCREENS.HOME,
    meta: REQUIRES_AUTH_META,
  }),
  Object.freeze({
    key: ROUTE_NAMES.MAP,
    path: ROUTE_PATHS.MAP,
    name: ROUTE_NAMES.MAP,
    screen: UI_SCREENS.MAP,
    meta: Object.freeze({ requiresAuth: false }),
  }),
  Object.freeze({
    key: ROUTE_NAMES.SOCIAL,
    path: ROUTE_PATHS.SOCIAL,
    name: ROUTE_NAMES.SOCIAL,
    screen: UI_SCREENS.SOCIAL,
    meta: REQUIRES_AUTH_META,
  }),
  Object.freeze({
    key: ROUTE_NAMES.SETTINGS,
    path: ROUTE_PATHS.SETTINGS,
    name: ROUTE_NAMES.SETTINGS,
    screen: UI_SCREENS.SETTINGS,
    meta: REQUIRES_AUTH_META,
  }),
  Object.freeze({
    key: ROUTE_NAMES.PROFILE,
    path: ROUTE_PATHS.PROFILE,
    name: ROUTE_NAMES.PROFILE,
    screen: UI_SCREENS.PROFILE,
    meta: REQUIRES_AUTH_META,
  }),
  Object.freeze({
    key: ROUTE_NAMES.SUPPORT,
    path: ROUTE_PATHS.SUPPORT,
    name: ROUTE_NAMES.SUPPORT,
    screen: UI_SCREENS.SUPPORT,
    meta: REQUIRES_AUTH_META,
  }),
])

export function routeToAuth() {
  return { name: ROUTE_NAMES.AUTH }
}

export function routeToAdmin() {
  return { name: ROUTE_NAMES.ADMIN }
}

export function routeToHome() {
  return { name: ROUTE_NAMES.HOME }
}

export function routeToMap({ lat = null, lon = null, spotId = '' } = {}) {
  const query = {}

  if (Number.isFinite(lat) && Number.isFinite(lon)) {
    query.lat = String(lat)
    query.lon = String(lon)
  }

  const sid = asText(spotId)
  if (sid) {
    query.spotId = sid
  }

  if (Object.keys(query).length === 0) {
    return { name: ROUTE_NAMES.MAP }
  }
  return { name: ROUTE_NAMES.MAP, query }
}

export function routeToSocial() {
  return { name: ROUTE_NAMES.SOCIAL }
}

export function routeToSettings() {
  return { name: ROUTE_NAMES.SETTINGS }
}

export function routeToProfile(userId = '') {
  const normalized = asText(userId)
  if (!normalized) {
    return { name: ROUTE_NAMES.PROFILE }
  }
  return {
    name: ROUTE_NAMES.PROFILE,
    params: {
      userId: normalized,
    },
  }
}

export function routeToSupport() {
  return { name: ROUTE_NAMES.SUPPORT }
}
