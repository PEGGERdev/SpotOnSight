import { getApiEndpointBinding } from '../api/registry'
import { ApiStateService } from './baseService'
import { asText } from '../utils/sanitizers'

function buildPath(pathTemplate, params = {}) {
  const source = asText(pathTemplate)
  const path = source.replace(/\{([a-zA-Z0-9_]+)\}/g, (_full, name) => {
    const raw = params[name]
    const normalized = asText(raw)
    if (!normalized) {
      throw new Error(`Missing path parameter: ${name}`)
    }
    return encodeURIComponent(normalized)
  })

  if (/\{[a-zA-Z0-9_]+\}/.test(path)) {
    throw new Error(`Unresolved path template: ${source}`)
  }

  return path
}

function appendQuery(path, query = {}) {
  const entries = Object.entries(query || {})
  if (!entries.length) return path

  const search = new URLSearchParams()
  for (const [key, value] of entries) {
    const queryKey = asText(key)
    if (!queryKey || value == null) continue

    const queryValue = String(value)
    if (!queryValue.trim()) continue
    search.append(queryKey, queryValue)
  }

  const qs = search.toString()
  if (!qs) return path
  return `${path}?${qs}`
}

export class ApiGatewayService extends ApiStateService {
  constructor(api, state) {
    super(api, state, { serviceName: 'api' })
  }

  _resolveToken({ authenticated, token }) {
    const tokenOverride = asText(token)
    if (!authenticated) {
      return tokenOverride || asText(this.token())
    }

    const activeToken = tokenOverride || asText(this.token())
    if (!activeToken) {
      throw new Error('Authentication required')
    }
    return activeToken
  }

  async _dispatchRequest(method, path, { body, token, formEncoded }) {
    if (method === 'GET') {
      return this.api.get(path, { token })
    }
    if (method === 'POST') {
      if (formEncoded) {
        return this.api.postForm(path, body || {}, { token })
      }
      return this.api.post(path, body || {}, { token })
    }
    if (method === 'PUT') {
      return this.api.put(path, body || {}, { token })
    }
    if (method === 'PATCH') {
      return this.api.patch(path, body || {}, { token })
    }
    if (method === 'DELETE') {
      return this.api.delete(path, { token })
    }
    throw new Error(`Unsupported API method: ${method}`)
  }

  async request(endpointKey, { params = {}, query = {}, body = undefined, token = '', formEncoded } = {}) {
    const binding = getApiEndpointBinding(endpointKey)
    const pathWithParams = buildPath(binding.path, params)
    const path = appendQuery(pathWithParams, query)
    const resolvedToken = this._resolveToken({
      authenticated: binding.authenticated,
      token,
    })

    const useFormEncoded = typeof formEncoded === 'boolean'
      ? formEncoded
      : binding.formEncoded

    return this._dispatchRequest(binding.method, path, {
      body,
      token: resolvedToken,
      formEncoded: useFormEncoded,
    })
  }
}
