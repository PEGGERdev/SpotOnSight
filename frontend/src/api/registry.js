import { asText } from '../utils/sanitizers'

function normalizeMethod(value) {
  const method = asText(value).toUpperCase()
  if (method === 'GET' || method === 'POST' || method === 'PUT' || method === 'PATCH' || method === 'DELETE') {
    return method
  }
  throw new Error(`Unsupported API method: ${value}`)
}

const _REGISTRY = []
const _REGISTRY_BY_KEY = new Map()

function registerApiEndpoint({
  key,
  method,
  path,
  authenticated = true,
  formEncoded = false,
}) {
  const normalizedKey = asText(key)
  const normalizedPath = asText(path)

  if (!normalizedKey) {
    throw new Error('registerApiEndpoint() requires a key')
  }
  if (!normalizedPath.startsWith('/')) {
    throw new Error(`registerApiEndpoint('${normalizedKey}') requires an absolute path`)
  }
  if (_REGISTRY_BY_KEY.has(normalizedKey)) {
    throw new Error(`Duplicate api endpoint key: ${normalizedKey}`)
  }

  const binding = Object.freeze({
    key: normalizedKey,
    method: normalizeMethod(method),
    path: normalizedPath,
    authenticated: Boolean(authenticated),
    formEncoded: Boolean(formEncoded),
  })

  _REGISTRY.push(binding)
  _REGISTRY_BY_KEY.set(binding.key, binding)
  return binding
}

export const API_ENDPOINTS = Object.freeze({
  AUTH_LOGIN: 'auth.login',
  AUTH_REGISTER: 'auth.register',
  AUTH_ACCOUNT_DELETE: 'auth.account.delete',
  AUTH_ACCOUNT_EXPORT: 'auth.account.export',

  SOCIAL_ME_GET: 'social.me.get',
  SOCIAL_ME_UPDATE: 'social.me.update',
  SOCIAL_USERS_PROFILE: 'social.users.profile',
  SOCIAL_USERS_SEARCH: 'social.users.search',

  SOCIAL_SPOTS_LIST: 'social.spots.list',
  SOCIAL_SPOTS_CREATE: 'social.spots.create',
  SOCIAL_SPOTS_UPDATE: 'social.spots.update',
  SOCIAL_SPOTS_DELETE: 'social.spots.delete',
  SOCIAL_USERS_SPOTS: 'social.users.spots',
  SOCIAL_USERS_FAVORITES: 'social.users.favorites',

  SOCIAL_FAVORITES_LIST: 'social.favorites.list',
  SOCIAL_FAVORITES_CREATE: 'social.favorites.create',
  SOCIAL_FAVORITES_DELETE: 'social.favorites.delete',

  SOCIAL_SHARE_SPOT: 'social.share.spot',
  SOCIAL_FOLLOW_USER: 'social.follow.user',
  SOCIAL_UNFOLLOW_USER: 'social.unfollow.user',
  SOCIAL_REMOVE_FOLLOWER: 'social.followers.remove',
  SOCIAL_FOLLOW_REQUESTS_LIST: 'social.follow.requests.list',
  SOCIAL_FOLLOW_REQUEST_APPROVE: 'social.follow.requests.approve',
  SOCIAL_FOLLOW_REQUEST_REJECT: 'social.follow.requests.reject',
  SOCIAL_BLOCK_USER: 'social.block.user',
  SOCIAL_UNBLOCK_USER: 'social.unblock.user',
  SOCIAL_BLOCKED_LIST: 'social.blocked.list',
  SOCIAL_FOLLOWERS_LIST: 'social.followers.list',
  SOCIAL_FOLLOWING_LIST: 'social.following.list',

  SOCIAL_SUPPORT_TICKETS_CREATE: 'social.support.tickets.create',
  SUPPORT_ADMIN_TICKETS_LIST: 'support.admin.tickets.list',
  SOCIAL_REPORTS_CREATE: 'social.reports.create',
  SOCIAL_NOTIFICATIONS_LIST: 'social.notifications.list',
  ADMIN_REPORTS_LIST: 'admin.reports.list',
  ADMIN_REPORTS_REVIEW: 'admin.reports.review',
  ADMIN_USERS_LIST: 'admin.users.list',
  ADMIN_USERS_UPDATE: 'admin.users.update',

  SOCIAL_COMMENTS_LIST: 'social.comments.list',
  SOCIAL_COMMENTS_CREATE: 'social.comments.create',
  SOCIAL_COMMENTS_UPDATE: 'social.comments.update',
  SOCIAL_COMMENTS_DELETE: 'social.comments.delete',

  SOCIAL_MEETUPS_LIST: 'social.meetups.list',
  SOCIAL_MEETUPS_CREATE: 'social.meetups.create',
  SOCIAL_MEETUPS_UPDATE: 'social.meetups.update',
  SOCIAL_MEETUPS_DELETE: 'social.meetups.delete',
  SOCIAL_MEETUPS_INVITES_LIST: 'social.meetups.invites.list',
  SOCIAL_MEETUPS_RESPOND: 'social.meetups.respond',
  SOCIAL_MEETUP_COMMENTS_LIST: 'social.meetup.comments.list',
  SOCIAL_MEETUP_COMMENTS_CREATE: 'social.meetup.comments.create',
  SOCIAL_MEETUP_COMMENTS_UPDATE: 'social.meetup.comments.update',
  SOCIAL_MEETUP_COMMENTS_DELETE: 'social.meetup.comments.delete',
  SOCIAL_MEETUP_NOTIFICATIONS_LIST: 'social.meetup.notifications.list',
  SOCIAL_MEETUPS_SPOTS: 'social.meetups.spots',
})

registerApiEndpoint({
  key: API_ENDPOINTS.AUTH_LOGIN,
  method: 'POST',
  path: '/auth/login',
  authenticated: false,
})

registerApiEndpoint({
  key: API_ENDPOINTS.AUTH_REGISTER,
  method: 'POST',
  path: '/auth/register',
  authenticated: false,
})

registerApiEndpoint({
  key: API_ENDPOINTS.AUTH_ACCOUNT_DELETE,
  method: 'DELETE',
  path: '/auth/account',
})

registerApiEndpoint({
  key: API_ENDPOINTS.AUTH_ACCOUNT_EXPORT,
  method: 'GET',
  path: '/auth/account/export',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_ME_GET,
  method: 'GET',
  path: '/social/me',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_ME_UPDATE,
  method: 'PUT',
  path: '/social/me',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_USERS_PROFILE,
  method: 'GET',
  path: '/social/users/{userId}/profile',
  authenticated: false,
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_USERS_SEARCH,
  method: 'GET',
  path: '/social/users/search',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_SPOTS_LIST,
  method: 'GET',
  path: '/social/spots',
  authenticated: false,
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_SPOTS_CREATE,
  method: 'POST',
  path: '/social/spots',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_SPOTS_UPDATE,
  method: 'PUT',
  path: '/social/spots/{spotId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_SPOTS_DELETE,
  method: 'DELETE',
  path: '/social/spots/{spotId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_USERS_SPOTS,
  method: 'GET',
  path: '/social/users/{userId}/spots',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_USERS_FAVORITES,
  method: 'GET',
  path: '/social/users/{userId}/favorites',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_FAVORITES_LIST,
  method: 'GET',
  path: '/social/favorites',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_FAVORITES_CREATE,
  method: 'POST',
  path: '/social/favorites/{spotId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_FAVORITES_DELETE,
  method: 'DELETE',
  path: '/social/favorites/{spotId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_SHARE_SPOT,
  method: 'POST',
  path: '/social/share/{spotId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_FOLLOW_USER,
  method: 'POST',
  path: '/social/follow/{userId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_UNFOLLOW_USER,
  method: 'DELETE',
  path: '/social/follow/{userId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_REMOVE_FOLLOWER,
  method: 'DELETE',
  path: '/social/followers/{userId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_FOLLOW_REQUESTS_LIST,
  method: 'GET',
  path: '/social/follow/requests',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_FOLLOW_REQUEST_APPROVE,
  method: 'POST',
  path: '/social/follow/requests/{userId}/approve',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_FOLLOW_REQUEST_REJECT,
  method: 'POST',
  path: '/social/follow/requests/{userId}/reject',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_BLOCK_USER,
  method: 'POST',
  path: '/social/block/{userId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_UNBLOCK_USER,
  method: 'DELETE',
  path: '/social/block/{userId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_BLOCKED_LIST,
  method: 'GET',
  path: '/social/blocked',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_FOLLOWERS_LIST,
  method: 'GET',
  path: '/social/followers/{userId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_FOLLOWING_LIST,
  method: 'GET',
  path: '/social/following/{userId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_SUPPORT_TICKETS_CREATE,
  method: 'POST',
  path: '/social/support/tickets',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_REPORTS_CREATE,
  method: 'POST',
  path: '/social/reports',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_NOTIFICATIONS_LIST,
  method: 'GET',
  path: '/social/notifications',
})

registerApiEndpoint({
  key: API_ENDPOINTS.ADMIN_REPORTS_LIST,
  method: 'GET',
  path: '/social/admin/reports',
})

registerApiEndpoint({
  key: API_ENDPOINTS.ADMIN_REPORTS_REVIEW,
  method: 'PATCH',
  path: '/social/admin/reports/{reportId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.ADMIN_USERS_LIST,
  method: 'GET',
  path: '/social/admin/users',
})

registerApiEndpoint({
  key: API_ENDPOINTS.ADMIN_USERS_UPDATE,
  method: 'PATCH',
  path: '/social/admin/users/{userId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SUPPORT_ADMIN_TICKETS_LIST,
  method: 'GET',
  path: '/social/support/tickets/admin/all',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_COMMENTS_LIST,
  method: 'GET',
  path: '/social/spots/{spotId}/comments',
  authenticated: false,
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_COMMENTS_CREATE,
  method: 'POST',
  path: '/social/spots/{spotId}/comments',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_COMMENTS_UPDATE,
  method: 'PATCH',
  path: '/social/comments/{commentId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_COMMENTS_DELETE,
  method: 'DELETE',
  path: '/social/comments/{commentId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUPS_LIST,
  method: 'GET',
  path: '/social/meetups',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUPS_CREATE,
  method: 'POST',
  path: '/social/meetups',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUPS_UPDATE,
  method: 'PUT',
  path: '/social/meetups/{meetupId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUPS_DELETE,
  method: 'DELETE',
  path: '/social/meetups/{meetupId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUPS_INVITES_LIST,
  method: 'GET',
  path: '/social/meetups/invites',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUPS_RESPOND,
  method: 'POST',
  path: '/social/meetups/{meetupId}/respond',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUP_COMMENTS_LIST,
  method: 'GET',
  path: '/social/meetups/{meetupId}/comments',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUP_COMMENTS_CREATE,
  method: 'POST',
  path: '/social/meetups/{meetupId}/comments',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUP_COMMENTS_UPDATE,
  method: 'PATCH',
  path: '/social/meetup-comments/{commentId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUP_COMMENTS_DELETE,
  method: 'DELETE',
  path: '/social/meetup-comments/{commentId}',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUP_NOTIFICATIONS_LIST,
  method: 'GET',
  path: '/social/meetup-notifications',
})

registerApiEndpoint({
  key: API_ENDPOINTS.SOCIAL_MEETUPS_SPOTS,
  method: 'GET',
  path: '/social/meetups/spots',
})

export function getApiEndpointBinding(key) {
  const normalizedKey = asText(key)
  const binding = _REGISTRY_BY_KEY.get(normalizedKey)
  if (!binding) {
    throw new Error(`Unknown api endpoint key: ${normalizedKey}`)
  }
  return binding
}

export function getApiEndpointBindings() {
  return [..._REGISTRY]
}
