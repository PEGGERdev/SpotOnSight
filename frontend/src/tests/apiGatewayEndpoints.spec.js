import { describe, expect, it, vi } from 'vitest'

import { API_ENDPOINTS, getApiEndpointBindings } from '../api/registry'
import { ApiGatewayService } from '../services/apiGatewayService'

class TestApiGatewayService extends ApiGatewayService {}

function createState({ token = 'session-token', userId = 'me-1' } = {}) {
  return {
    session: {
      token,
      user: {
        id: userId,
      },
    },
  }
}

function createApiClientMock() {
  return {
    get: vi.fn(async (path, options) => ({ method: 'GET', path, options })),
    post: vi.fn(async (path, body, options) => ({ method: 'POST', path, body, options })),
    postForm: vi.fn(async (path, body, options) => ({ method: 'POST_FORM', path, body, options })),
    put: vi.fn(async (path, body, options) => ({ method: 'PUT', path, body, options })),
    patch: vi.fn(async (path, body, options) => ({ method: 'PATCH', path, body, options })),
    delete: vi.fn(async (path, options) => ({ method: 'DELETE', path, options })),
  }
}

const ENDPOINT_FIXTURES = Object.freeze({
  [API_ENDPOINTS.AUTH_LOGIN]: {
    options: {
      body: {
        username_or_email: 'alice',
        password: 'password123',
      },
    },
    expectedPath: '/auth/login',
  },
  [API_ENDPOINTS.AUTH_REGISTER]: {
    options: {
      body: {
        username: 'alice',
        email: 'alice@example.com',
        password: 'password123',
        display_name: 'Alice',
      },
    },
    expectedPath: '/auth/register',
  },
  [API_ENDPOINTS.AUTH_ACCOUNT_DELETE]: {
    options: {
      body: {
        password: 'password123',
      },
    },
    expectedPath: '/auth/account',
  },
  [API_ENDPOINTS.AUTH_ACCOUNT_EXPORT]: {
    options: {},
    expectedPath: '/auth/account/export',
  },

  [API_ENDPOINTS.SOCIAL_ME_GET]: {
    options: {},
    expectedPath: '/social/me',
  },
  [API_ENDPOINTS.SOCIAL_ME_UPDATE]: {
    options: {
      body: {
        display_name: 'Alice Updated',
      },
    },
    expectedPath: '/social/me',
  },
  [API_ENDPOINTS.SOCIAL_USERS_PROFILE]: {
    options: {
      params: {
        userId: 'user 1',
      },
    },
    expectedPath: '/social/users/user%201/profile',
  },
  [API_ENDPOINTS.SOCIAL_USERS_SEARCH]: {
    options: {
      query: {
        q: 'mountain lake',
        limit: 15,
      },
    },
    expectedPath: '/social/users/search?q=mountain+lake&limit=15',
  },

  [API_ENDPOINTS.SOCIAL_SPOTS_LIST]: {
    options: {},
    expectedPath: '/social/spots',
  },
  [API_ENDPOINTS.SOCIAL_SPOTS_CREATE]: {
    options: {
      body: {
        title: 'New Spot',
      },
    },
    expectedPath: '/social/spots',
  },
  [API_ENDPOINTS.SOCIAL_SPOTS_UPDATE]: {
    options: {
      params: {
        spotId: 'spot 1',
      },
      body: {
        title: 'Updated Spot',
      },
    },
    expectedPath: '/social/spots/spot%201',
  },
  [API_ENDPOINTS.SOCIAL_SPOTS_DELETE]: {
    options: {
      params: {
        spotId: 'spot 1',
      },
    },
    expectedPath: '/social/spots/spot%201',
  },
  [API_ENDPOINTS.SOCIAL_USERS_SPOTS]: {
    options: {
      params: {
        userId: 'user 1',
      },
    },
    expectedPath: '/social/users/user%201/spots',
  },
  [API_ENDPOINTS.SOCIAL_USERS_FAVORITES]: {
    options: {
      params: {
        userId: 'user 1',
      },
    },
    expectedPath: '/social/users/user%201/favorites',
  },

  [API_ENDPOINTS.SOCIAL_FAVORITES_LIST]: {
    options: {},
    expectedPath: '/social/favorites',
  },
  [API_ENDPOINTS.SOCIAL_FAVORITES_CREATE]: {
    options: {
      params: {
        spotId: 'spot 1',
      },
      body: {},
    },
    expectedPath: '/social/favorites/spot%201',
  },
  [API_ENDPOINTS.SOCIAL_FAVORITES_DELETE]: {
    options: {
      params: {
        spotId: 'spot 1',
      },
    },
    expectedPath: '/social/favorites/spot%201',
  },

  [API_ENDPOINTS.SOCIAL_SHARE_SPOT]: {
    options: {
      params: {
        spotId: 'spot 1',
      },
      body: {
        message: 'shared message',
      },
    },
    expectedPath: '/social/share/spot%201',
  },
  [API_ENDPOINTS.SOCIAL_FOLLOW_USER]: {
    options: {
      params: {
        userId: 'user 1',
      },
      body: {},
    },
    expectedPath: '/social/follow/user%201',
  },
  [API_ENDPOINTS.SOCIAL_UNFOLLOW_USER]: {
    options: {
      params: {
        userId: 'user 1',
      },
    },
    expectedPath: '/social/follow/user%201',
  },
  [API_ENDPOINTS.SOCIAL_REMOVE_FOLLOWER]: {
    options: {
      params: {
        userId: 'user 1',
      },
    },
    expectedPath: '/social/followers/user%201',
  },
  [API_ENDPOINTS.SOCIAL_FOLLOW_REQUESTS_LIST]: {
    options: {},
    expectedPath: '/social/follow/requests',
  },
  [API_ENDPOINTS.SOCIAL_FOLLOW_REQUEST_APPROVE]: {
    options: {
      params: {
        userId: 'user 1',
      },
      body: {},
    },
    expectedPath: '/social/follow/requests/user%201/approve',
  },
  [API_ENDPOINTS.SOCIAL_FOLLOW_REQUEST_REJECT]: {
    options: {
      params: {
        userId: 'user 1',
      },
      body: {},
    },
    expectedPath: '/social/follow/requests/user%201/reject',
  },
  [API_ENDPOINTS.SOCIAL_BLOCK_USER]: {
    options: {
      params: {
        userId: 'user 1',
      },
      body: {},
    },
    expectedPath: '/social/block/user%201',
  },
  [API_ENDPOINTS.SOCIAL_UNBLOCK_USER]: {
    options: {
      params: {
        userId: 'user 1',
      },
    },
    expectedPath: '/social/block/user%201',
  },
  [API_ENDPOINTS.SOCIAL_BLOCKED_LIST]: {
    options: {},
    expectedPath: '/social/blocked',
  },
  [API_ENDPOINTS.SOCIAL_FOLLOWERS_LIST]: {
    options: {
      params: {
        userId: 'user 1',
      },
    },
    expectedPath: '/social/followers/user%201',
  },
  [API_ENDPOINTS.SOCIAL_FOLLOWING_LIST]: {
    options: {
      params: {
        userId: 'user 1',
      },
    },
    expectedPath: '/social/following/user%201',
  },

  [API_ENDPOINTS.SOCIAL_SUPPORT_TICKETS_CREATE]: {
    options: {
      body: {
        subject: 'Need help',
      },
    },
    expectedPath: '/social/support/tickets',
  },
  [API_ENDPOINTS.SOCIAL_REPORTS_CREATE]: {
    options: {
      body: {
        target_type: 'spot',
        target_id: 'spot-1',
        reason: 'spam',
        details: 'Looks like spam.',
      },
    },
    expectedPath: '/social/reports',
  },
  [API_ENDPOINTS.SOCIAL_NOTIFICATIONS_LIST]: {
    options: {},
    expectedPath: '/social/notifications',
  },
  [API_ENDPOINTS.ADMIN_REPORTS_LIST]: {
    options: {
      query: {
        status: 'open',
        limit: 50,
      },
    },
    expectedPath: '/social/admin/reports?status=open&limit=50',
  },
  [API_ENDPOINTS.ADMIN_REPORTS_REVIEW]: {
    options: {
      params: {
        reportId: 'report 1',
      },
      body: {
        status: 'upheld',
        action: 'hide_content',
        severity: 'medium',
        admin_notes: 'Confirmed by admin.',
      },
    },
    expectedPath: '/social/admin/reports/report%201',
  },
  [API_ENDPOINTS.ADMIN_USERS_LIST]: {
    options: {
      query: {
        q: 'demo',
        limit: 25,
      },
    },
    expectedPath: '/social/admin/users?q=demo&limit=25',
  },
  [API_ENDPOINTS.ADMIN_USERS_UPDATE]: {
    options: {
      params: {
        userId: 'user 1',
      },
      body: {
        account_status: 'watch',
        reason: 'Timeout active.',
        posting_timeout_until: '2026-03-19T10:00:00Z',
      },
    },
    expectedPath: '/social/admin/users/user%201',
  },

  [API_ENDPOINTS.SOCIAL_COMMENTS_LIST]: {
    options: {
      params: {
        spotId: 'spot 1',
      },
    },
    expectedPath: '/social/spots/spot%201/comments',
  },
  [API_ENDPOINTS.SOCIAL_COMMENTS_CREATE]: {
    options: {
      params: {
        spotId: 'spot 1',
      },
      body: {
        content: 'Great spot!',
      },
    },
    expectedPath: '/social/spots/spot%201/comments',
  },
  [API_ENDPOINTS.SOCIAL_COMMENTS_UPDATE]: {
    options: {
      params: {
        commentId: 'comment 1',
      },
      body: {
        content: 'Updated comment',
      },
    },
    expectedPath: '/social/comments/comment%201',
  },
  [API_ENDPOINTS.SOCIAL_COMMENTS_DELETE]: {
    options: {
      params: {
        commentId: 'comment 1',
      },
    },
    expectedPath: '/social/comments/comment%201',
  },

  [API_ENDPOINTS.SOCIAL_MEETUPS_LIST]: {
    options: {
      query: {
        scope: 'upcoming',
      },
    },
    expectedPath: '/social/meetups?scope=upcoming',
  },
  [API_ENDPOINTS.SOCIAL_MEETUPS_CREATE]: {
    options: {
      body: {
        title: 'Sunday Meetup',
        starts_at: '2027-02-10T10:00:00Z',
      },
    },
    expectedPath: '/social/meetups',
  },
  [API_ENDPOINTS.SOCIAL_MEETUPS_UPDATE]: {
    options: {
      params: {
        meetupId: 'meetup 1',
      },
      body: {
        title: 'Updated Meetup',
      },
    },
    expectedPath: '/social/meetups/meetup%201',
  },
  [API_ENDPOINTS.SOCIAL_MEETUPS_DELETE]: {
    options: {
      params: {
        meetupId: 'meetup 1',
      },
    },
    expectedPath: '/social/meetups/meetup%201',
  },
  [API_ENDPOINTS.SOCIAL_MEETUPS_INVITES_LIST]: {
    options: {},
    expectedPath: '/social/meetups/invites',
  },
  [API_ENDPOINTS.SOCIAL_MEETUPS_RESPOND]: {
    options: {
      params: {
        meetupId: 'meetup 1',
      },
      body: {
        status: 'accepted',
        comment: 'See you there!',
      },
    },
    expectedPath: '/social/meetups/meetup%201/respond',
  },
  [API_ENDPOINTS.SOCIAL_MEETUP_COMMENTS_LIST]: {
    options: {
      params: {
        meetupId: 'meetup 1',
      },
    },
    expectedPath: '/social/meetups/meetup%201/comments',
  },
  [API_ENDPOINTS.SOCIAL_MEETUP_COMMENTS_CREATE]: {
    options: {
      params: {
        meetupId: 'meetup 1',
      },
      body: {
        message: 'Looking forward to it',
      },
    },
    expectedPath: '/social/meetups/meetup%201/comments',
  },
  [API_ENDPOINTS.SOCIAL_MEETUP_COMMENTS_UPDATE]: {
    options: {
      params: {
        commentId: 'comment 1',
      },
      body: {
        message: 'Updated meetup note',
      },
    },
    expectedPath: '/social/meetup-comments/comment%201',
  },
  [API_ENDPOINTS.SOCIAL_MEETUP_COMMENTS_DELETE]: {
    options: {
      params: {
        commentId: 'comment 1',
      },
    },
    expectedPath: '/social/meetup-comments/comment%201',
  },
  [API_ENDPOINTS.SOCIAL_MEETUP_NOTIFICATIONS_LIST]: {
    options: {},
    expectedPath: '/social/meetup-notifications',
  },
  [API_ENDPOINTS.SOCIAL_MEETUPS_SPOTS]: {
    options: {
      params: {
        spotId: 'spot 1',
      },
    },
    expectedPath: '/social/meetups/spots',
  },
  [API_ENDPOINTS.SUPPORT_ADMIN_TICKETS_LIST]: {
    options: {},
    expectedPath: '/social/support/tickets/admin/all',
  },
})

describe('ApiGatewayService endpoint dispatch', () => {
  it('provides fixtures for every registered endpoint', () => {
    const endpointKeys = getApiEndpointBindings().map((binding) => binding.key).sort()
    const fixtureKeys = Object.keys(ENDPOINT_FIXTURES).sort()
    expect(fixtureKeys).toEqual(endpointKeys)
  })

  for (const binding of getApiEndpointBindings()) {
    it(`dispatches endpoint '${binding.key}'`, async () => {
      const fixture = ENDPOINT_FIXTURES[binding.key]
      const apiClient = createApiClientMock()
      const gateway = new TestApiGatewayService(apiClient, createState())

      await gateway.request(binding.key, fixture.options)

      const transport = fixture.options?.formEncoded
        ? 'postForm'
        : binding.method === 'DELETE'
          ? 'delete'
          : binding.method.toLowerCase()
      const expectedToken = 'session-token'

      if (transport === 'get' || transport === 'delete') {
        expect(apiClient[transport]).toHaveBeenCalledWith(fixture.expectedPath, { token: expectedToken })
      } else {
        const expectedBody = Object.prototype.hasOwnProperty.call(fixture.options || {}, 'body')
          ? fixture.options.body
          : {}
        expect(apiClient[transport]).toHaveBeenCalledWith(fixture.expectedPath, expectedBody, { token: expectedToken })
      }
    })
  }

  it('supports form-encoded requests when explicitly requested', async () => {
    const apiClient = createApiClientMock()
    const gateway = new TestApiGatewayService(apiClient, createState())

    await gateway.request(API_ENDPOINTS.AUTH_LOGIN, {
      body: {
        username: 'alice',
        password: 'pw',
      },
      formEncoded: true,
    })

    expect(apiClient.postForm).toHaveBeenCalledWith('/auth/login', {
      username: 'alice',
      password: 'pw',
    }, { token: 'session-token' })
    expect(apiClient.post).not.toHaveBeenCalled()
  })

  it('throws when an authenticated endpoint is called without token', async () => {
    const apiClient = createApiClientMock()
    const gateway = new TestApiGatewayService(apiClient, createState({ token: '' }))

    await expect(gateway.request(API_ENDPOINTS.SOCIAL_ME_GET)).rejects.toThrow('Authentication required')
  })

  it('throws when a required path parameter is missing', async () => {
    const apiClient = createApiClientMock()
    const gateway = new TestApiGatewayService(apiClient, createState())

    await expect(
      gateway.request(API_ENDPOINTS.SOCIAL_USERS_PROFILE, {
        params: {},
      }),
    ).rejects.toThrow('Missing path parameter: userId')
  })
})

