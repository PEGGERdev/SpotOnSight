import { normalizeUser } from '../models/userMapper'
import { API_ENDPOINTS } from '../api/registry'
import { asText, compareText, normalizeSearchText, uniqueTextList } from '../utils/sanitizers'
import { ApiStateService } from './baseService'

function addIfDefined(out, key, value) {
  if (value === undefined) return
  out[key] = value
}

function addIfPresentText(out, key, value) {
  if (value === undefined || value === null) return
  const text = String(value).trim()
  if (!text) return
  out[key] = text
}

function dedupeUsers(items) {
  if (!Array.isArray(items)) return []

  const out = []
  const seen = new Set()
  for (const item of items) {
    const user = normalizeUser(item)
    const id = String(user.id || '').trim()
    if (!id || seen.has(id)) continue
    seen.add(id)
    out.push(user)
  }
  return out
}

function byDisplayName(a, b) {
  return compareText(a?.display_name || a?.username, b?.display_name || b?.username)
}

function textIncludesUser(user, query) {
  const q = normalizeSearchText(query)
  if (!q) return true

  const haystack = [
    user?.display_name,
    user?.username,
    user?.email,
    user?.id,
  ]
    .map((value) => normalizeSearchText(value))
    .join(' ')

  return haystack.includes(q)
}

export class UsersService extends ApiStateService {
  constructor(api, state) {
    super(api, state, { serviceName: 'users' })
  }

  async _profilesByIds(userIds) {
    const ids = uniqueTextList(userIds)
    const rows = await Promise.all(
      ids.map(async (id) => {
        try {
          const data = await this.api.request(API_ENDPOINTS.SOCIAL_USERS_PROFILE, {
            params: { userId: id },
          })
          return normalizeUser(data)
        } catch {
          return null
        }
      }),
    )
    return rows.filter(Boolean)
  }

  async me() {
    if (!this.token()) {
      this.captureError('Authentication required', 'Authentication required')
      return null
    }

    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_ME_GET)
      this.clearError()
      return normalizeUser(data)
    } catch (error) {
      this.captureError(error, 'Could not load user profile')
      return null
    }
  }

  async profile(userId) {
    const id = String(userId || '').trim()
    if (!id) {
      this.captureError('User id is required', 'User id is required')
      return null
    }

    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_USERS_PROFILE, {
        params: { userId: id },
      })
      this.clearError()
      return normalizeUser(data)
    } catch (error) {
      this.captureError(error, 'Could not load user profile')
      return null
    }
  }

  async searchByUsername(query, limit = 20) {
    if (!this.token()) {
      this.captureError('Authentication required', 'Authentication required')
      return []
    }

    const q = String(query || '').trim()
    if (!q) {
      this.clearError()
      return []
    }

    const safeLimit = Math.min(50, Math.max(1, Number(limit) || 20))

    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_USERS_SEARCH, {
        query: {
          q,
          limit: safeLimit,
        },
      })
      this.clearError()
      return Array.isArray(data) ? data.map((item) => normalizeUser(item)) : []
    } catch (error) {
      this.captureError(error, 'Could not search users')
      return []
    }
  }

  async friendDirectory() {
    if (!this.token()) {
      this.captureError('Authentication required', 'Authentication required')
      return []
    }

    const userId = String(this.state?.session?.user?.id || '').trim()
    if (!userId) {
      this.captureError('User profile not loaded', 'User profile not loaded')
      return []
    }

    try {
      const [followers, following] = await Promise.all([
        this.api.request(API_ENDPOINTS.SOCIAL_FOLLOWERS_LIST, {
          params: { userId },
        }),
        this.api.request(API_ENDPOINTS.SOCIAL_FOLLOWING_LIST, {
          params: { userId },
        }),
      ])

      const meId = userId
      const ids = uniqueTextList([
        ...(Array.isArray(followers) ? followers.map((entry) => asText(entry?.user_id)) : []),
        ...(Array.isArray(following) ? following.map((entry) => asText(entry?.user_id)) : []),
      ])
      const hydrated = await this._profilesByIds(ids)
      const merged = dedupeUsers(hydrated)
        .filter((user) => String(user.id || '') !== meId)
        .sort(byDisplayName)

      this.clearError()
      return merged
    } catch (error) {
      this.captureError(error, 'Could not load friend list')
      return []
    }
  }

  async searchFriends(query, limit = 20) {
    const safeLimit = Math.min(100, Math.max(1, Number(limit) || 20))
    const friends = await this.friendDirectory()
    return friends
      .filter((user) => textIncludesUser(user, query))
      .slice(0, safeLimit)
  }

  async updateMe(input) {
    if (!this.token()) {
      this.captureError('Authentication required', 'Authentication required')
      return null
    }

    const src = input && typeof input === 'object' ? input : {}
    const payload = {}

    addIfDefined(payload, 'username', src.username)
    addIfDefined(payload, 'email', src.email)
    addIfDefined(payload, 'display_name', src.displayName)
    addIfDefined(payload, 'bio', src.bio)
    addIfDefined(payload, 'avatar_image', src.avatarImage)
    addIfDefined(payload, 'social_accounts', src.socialAccounts)
    addIfDefined(payload, 'follow_requires_approval', src.followRequiresApproval)
    addIfPresentText(payload, 'current_password', src.currentPassword)
    addIfPresentText(payload, 'new_password', src.newPassword)

    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_ME_UPDATE, {
        body: payload,
      })
      this.clearError()
      return normalizeUser(data)
    } catch (error) {
      this.captureError(error, 'Could not save user profile')
      return null
    }
  }
}
