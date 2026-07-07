import { extractSpotId } from '../models/spotMapper'
import { normalizeUser } from '../models/userMapper'
import { API_ENDPOINTS } from '../api/registry'
import { asText, uniqueTextList } from '../utils/sanitizers'
import { getDeviceId } from '../utils/deviceId'
import { ApiStateService } from './baseService'

export class SocialService extends ApiStateService {
  constructor(api, state) {
    super(api, state, { serviceName: 'social' })
  }

  async _userProfilesByIds(userIds) {
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

  async loadFavorites() {
    if (!this.token()) {
      this.clearError()
      return []
    }
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_FAVORITES_LIST)
      const spotIds = Array.isArray(data)
        ? data
          .map((x) => asText(x?.spot_id) || extractSpotId(x))
          .filter(Boolean)
        : []
      const favorites = uniqueTextList(spotIds)
      this.clearError()
      return favorites
    } catch (error) {
      this.captureError(error, 'Could not load favorites')
      return []
    }
  }

  async favoriteSpot(spotId) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_FAVORITES_CREATE, {
        params: { spotId },
        body: {},
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not update favorite')
      return false
    }
  }

  async unfavoriteSpot(spotId) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_FAVORITES_DELETE, {
        params: { spotId },
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not update favorite')
      return false
    }
  }

  async shareSpot(spotId, message) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_SHARE_SPOT, {
        params: { spotId },
        body: { message: message || '' },
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not share spot')
      return false
    }
  }

  async reportContent(targetType, targetId, reason, details = '') {
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_REPORTS_CREATE, {
        body: {
          target_type: asText(targetType),
          target_id: asText(targetId),
          reason: asText(reason) || 'other',
          details: asText(details),
          device_id: getDeviceId(),
        },
      })
      this.clearError()
      return data || null
    } catch (error) {
      this.captureError(error, 'Could not submit report')
      return null
    }
  }

  async moderationNotifications() {
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_NOTIFICATIONS_LIST)
      this.clearError()
      return Array.isArray(data) ? data : []
    } catch (error) {
      this.captureError(error, 'Could not load moderation notifications')
      return []
    }
  }

  async followUser(userId) {
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_FOLLOW_USER, {
        params: { userId },
        body: {},
      })
      const status = String(data?.status || 'following').toLowerCase()
      this.clearError()
      if (status === 'pending') {
        return 'pending'
      }
      return 'following'
    } catch (error) {
      this.captureError(error, 'Could not follow user')
      return ''
    }
  }

  async unfollowUser(userId) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_UNFOLLOW_USER, {
        params: { userId },
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not unfollow user')
      return false
    }
  }

  async removeFollower(userId) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_REMOVE_FOLLOWER, {
        params: { userId },
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not remove follower')
      return false
    }
  }

  async incomingFollowRequests() {
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_FOLLOW_REQUESTS_LIST)
      this.clearError()
      if (!Array.isArray(data)) return []

       const followerIds = uniqueTextList(data.map((entry) => asText(entry?.follower_id)))
      const users = await this._userProfilesByIds(followerIds)
      const userById = new Map(users.map((user) => [asText(user?.id), user]))

      return data
        .map((entry) => {
          const followerId = asText(entry?.follower_id)
          const follower = userById.get(followerId)
          if (!followerId || !follower) return null
          return {
            follower_id: followerId,
            created_at: asText(entry?.created_at),
            follower,
          }
        })
        .filter(Boolean)
    } catch (error) {
      this.captureError(error, 'Could not load follow requests')
      return []
    }
  }

  async approveFollowRequest(userId) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_FOLLOW_REQUEST_APPROVE, {
        params: { userId },
        body: {},
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not approve follow request')
      return false
    }
  }

  async rejectFollowRequest(userId) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_FOLLOW_REQUEST_REJECT, {
        params: { userId },
        body: {},
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not reject follow request')
      return false
    }
  }

  async blockUser(userId) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_BLOCK_USER, {
        params: { userId },
        body: {},
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not block user')
      return false
    }
  }

  async unblockUser(userId) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_UNBLOCK_USER, {
        params: { userId },
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not unblock user')
      return false
    }
  }

  async blockedUsers() {
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_BLOCKED_LIST)
      this.clearError()
      if (!Array.isArray(data)) return []
      const ids = data.map((entry) => asText(entry?.user_id)).filter(Boolean)
      return this._userProfilesByIds(ids)
    } catch (error) {
      this.captureError(error, 'Could not load blocked users')
      return []
    }
  }

  async followersOf(userId) {
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_FOLLOWERS_LIST, {
        params: { userId },
      })
      this.clearError()
      if (!Array.isArray(data)) return []
      const ids = data.map((entry) => asText(entry?.user_id)).filter(Boolean)
      return this._userProfilesByIds(ids)
    } catch (error) {
      this.captureError(error, 'Could not load followers')
      return []
    }
  }

  async followingOf(userId) {
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_FOLLOWING_LIST, {
        params: { userId },
      })
      this.clearError()
      if (!Array.isArray(data)) return []
      const ids = data.map((entry) => asText(entry?.user_id)).filter(Boolean)
      return this._userProfilesByIds(ids)
    } catch (error) {
      this.captureError(error, 'Could not load following users')
      return []
    }
  }
}
