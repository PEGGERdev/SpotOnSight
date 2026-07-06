<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { routeToAuth } from '../../router/routeSpec'

import SpotEditorModal from './SpotEditorModal.vue'
import SpotDetailsModal from './SpotDetailsModal.vue'
import MobileMapOverlay from './MobileMapOverlay.vue'
import { useMapGeolocation } from './composables/useMapGeolocation'
import { useMapLocationSearch } from './composables/useMapLocationSearch'
import { useSpotComments } from './composables/useSpotComments'
import { useOwnerProfiles } from '../../composables/useOwnerProfiles'
import {
  defaultSpotFilters,
  normalizeSubscriptionForUser,
  ownedSubscriptions,
  sanitizeSpotFilters,
} from './mapWorkspaceState'
import { applyFocusRequest as applyMapFocusRequest } from './mapWorkspaceFocus'
import {
  applyFilterSubscription as applySavedFilterSubscription,
  removeFilterSubscription as removeSavedFilterSubscription,
  subscribeCurrentFilters as saveCurrentFiltersSubscription,
} from './mapWorkspaceSubscriptions'
import {
  openEditorFromSpot as openWorkspaceEditorFromSpot,
  pickLocationFromEditor as pickWorkspaceLocationFromEditor,
  startCreateAt as startWorkspaceCreateAt,
} from './mapWorkspaceEditor'
import {
  shareSelectedSpot,
  toggleFavoriteForSpot as toggleWorkspaceFavoriteForSpot,
  toggleFavoriteSelection,
} from './mapWorkspaceInteractions'
import {
  closeEditorState,
  closeSpotDetails,
  goToSpotSelection,
  showSpotDetails as showWorkspaceSpotDetails,
} from './mapWorkspaceSelection'
import {
  getCurrentPosition,
  getStoredLocation,
} from '../../services/geolocationService'
import { distanceKm, tokenize } from '../../utils/sanitizers'

const SPOT_PAGE_SIZE = 10

const props = defineProps({
  state: { type: Object, required: true },
  focusRequest: { type: Object, default: () => ({ lat: null, lon: null, spotId: '' }) },
  behavior: { type: Object, required: true },
})

const router = useRouter()

function requireAuth() {
  if (!String(props.state?.session?.token || '').trim()) {
    router.push(routeToAuth())
    return false
  }
  return true
}

const { ownerLabel, ownerSearchText, warmOwnerProfiles } = useOwnerProfiles(
  (ownerId) => props.behavior.loadUserProfile(ownerId),
)

const detailsOpen = ref(false)
const editorOpen = ref(false)
const editorMode = ref('create')
const pickMode = ref(false)
const selectedSpot = ref(null)

const mapViewportAnchor = ref(null)
const visibleSpotCount = ref(SPOT_PAGE_SIZE)
const lastFocusSignature = ref('')

const { mapBounds, initializeUserLocation } = useMapGeolocation({
  state: props.state,
  getStoredLocation,
  getCurrentPosition,
})

const {
  locationQuery,
  locationSearchBusy,
  locationSearchError,
  locationResults,
  activeLocation,
  activeLocationLabel,
  updateLocationQuery,
  runLocationSearch,
  selectLocation,
  clearLocationFilter,
  radiusCenter,
  currentSubscriptionCenter,
} = useMapLocationSearch({
  state: props.state,
  searchLocations: (query, limit) => props.behavior.searchLocations(query, limit),
  notify: (payload) => props.behavior.notify(payload),
  onResetPagination: () => {
    visibleSpotCount.value = SPOT_PAGE_SIZE
  },
})

const currentUserId = computed(() => String(props.state.session?.user?.id || '').trim())

const {
  comments,
  commentsLoading,
  commentsBusy,
  commentDraft,
  createComment,
  updateComment,
  deleteComment,
} = useSpotComments({
  behavior: props.behavior,
  selectedSpot,
  detailsOpen,
  currentUserId,
})

onMounted(() => {
  void initializeUserLocation()
})

const editorDraft = reactive({
  id: '',
  title: '',
  description: '',
  tags: [],
  lat: 47.3769,
  lon: 8.5417,
  images: [],
  visibility: 'public',
  invite_user_ids: [],
})

const spotFilters = reactive(defaultSpotFilters())

const favoritesSet = computed(() => new Set((props.state.favorites || []).map((id) => String(id))))
const filterSubscriptions = computed(() => {
  const ownerUserId = currentUserId.value
  if (!ownerUserId) return []

  return ownedSubscriptions(props.state.map?.filterSubscriptions, ownerUserId)
})

const selectedSpotIsOwner = computed(() => {
  const meId = String(props.state.session?.user?.id || '').trim()
  const ownerId = String(selectedSpot.value?.owner_id || '').trim()
  return Boolean(meId && ownerId && meId === ownerId)
})

const hasActiveSpotFilters = computed(() => {
  return Boolean(
    spotFilters.text
    || spotFilters.tagsText
    || spotFilters.ownerText
    || spotFilters.visibility !== 'all'
    || spotFilters.onlyFavorites
    || Number(spotFilters.radiusKm || 0) > 0,
  )
})

const filteredSpots = computed(() => {
  const allSpots = Array.isArray(props.state.spots) ? props.state.spots : []
  const text = String(spotFilters.text || '').toLowerCase()
  const ownerText = String(spotFilters.ownerText || '').toLowerCase()
  const visibility = String(spotFilters.visibility || 'all')
  const requiredTags = tokenize(spotFilters.tagsText)
  const radiusKm = Number(spotFilters.radiusKm || 0)
  const center = radiusCenter()

  return allSpots.filter((spot) => {
    if (!spot || typeof spot !== 'object') return false

    if (spotFilters.onlyFavorites && !isFavorite(spot)) {
      return false
    }

    if (visibility !== 'all' && String(spot.visibility || 'public') !== visibility) {
      return false
    }

    if (text) {
      const haystack = [
        spot?.title,
        spot?.description,
        ...(Array.isArray(spot?.tags) ? spot.tags : []),
      ]
        .map((value) => String(value || '').toLowerCase())
        .join(' ')
      if (!haystack.includes(text)) {
        return false
      }
    }

    if (requiredTags.length) {
      const tags = (Array.isArray(spot?.tags) ? spot.tags : []).map((tag) => String(tag || '').toLowerCase())
      const hasAll = requiredTags.every((requested) => tags.some((tag) => tag.includes(requested)))
      if (!hasAll) {
        return false
      }
    }

    if (ownerText && !ownerSearchText(spot).includes(ownerText)) {
      return false
    }

    if (radiusKm > 0 && center) {
      const distance = distanceKm(
        Number(spot?.lat || 0),
        Number(spot?.lon || 0),
        center[0],
        center[1],
      )
      if (!Number.isFinite(distance) || distance > radiusKm) {
        return false
      }
    }

    return true
  })
})

const listedSpots = computed(() => filteredSpots.value.slice(0, visibleSpotCount.value))

const remainingSpotCount = computed(() => {
  return Math.max(0, filteredSpots.value.length - listedSpots.value.length)
})

const canLoadMoreSpots = computed(() => remainingSpotCount.value > 0)

const ownerIdsSignature = computed(() => {
  const ids = [...new Set(
    (Array.isArray(props.state.spots) ? props.state.spots : [])
      .map((spot) => String(spot?.owner_id || '').trim())
      .filter(Boolean),
  )]
    .sort()
  return ids.join('|')
})

watch(
  () => ownerIdsSignature.value,
  () => {
    void warmOwnerProfiles(props.state.spots)
  },
  { immediate: true },
)

watch(
  () => props.state.spots,
  () => {
    if (!selectedSpot.value?.id) return
    const next = (props.state.spots || []).find((spot) => String(spot?.id || '') === String(selectedSpot.value?.id || ''))
    if (next) {
      selectedSpot.value = next
    }
  },
  { deep: true },
)

watch(
  () => props.focusRequest,
  (next) => {
    applyFocusRequest(next)
  },
  { deep: true, immediate: true },
)

function spotDistanceLabel(spot) {
  const center = radiusCenter()
  if (!center) return ''

  const distance = distanceKm(
    Number(spot?.lat || 0),
    Number(spot?.lon || 0),
    center[0],
    center[1],
  )
  if (!Number.isFinite(distance)) return ''

  if (distance >= 10) {
    return `${distance.toFixed(0)} km away`
  }
  return `${distance.toFixed(1)} km away`
}

function isFavorite(spot) {
  const spotId = String(spot?.id || '').trim()
  return Boolean(spotId && favoritesSet.value.has(spotId))
}

function updateSpotFilters(next) {
  Object.assign(spotFilters, sanitizeSpotFilters(next))
  visibleSpotCount.value = SPOT_PAGE_SIZE
}

function resetSpotFilters() {
  Object.assign(spotFilters, defaultSpotFilters())
  visibleSpotCount.value = SPOT_PAGE_SIZE
}

function applyFocusRequest(input) {
  applyMapFocusRequest({
    input,
    state: props.state,
    lastFocusSignature,
    showSpotDetails,
  })
}

function subscribeCurrentFilters() {
  saveCurrentFiltersSubscription({
    currentUserId,
    filteredSpots,
    spotFilters,
    currentSubscriptionCenter,
    state: props.state,
    notify: props.behavior.notify,
  })
}

function removeFilterSubscription(subId) {
  removeSavedFilterSubscription({
    currentUserId,
    subId,
    state: props.state,
    notify: props.behavior.notify,
  })
}

function applyFilterSubscription(subscription) {
  applySavedFilterSubscription({
    subscription,
    currentUserId,
    activeLocation,
    spotFilters,
    state: props.state,
    visibleSpotCount,
    pageSize: SPOT_PAGE_SIZE,
    normalizeSubscriptionForUser,
    notify: props.behavior.notify,
  })
}

function startCreateAt(lat, lon) {
  if (!requireAuth()) return
  startWorkspaceCreateAt({ editorMode, detailsOpen, editorDraft, editorOpen, lat, lon })
}

function openEditorFromSpot(spot) {
  openWorkspaceEditorFromSpot({ editorMode, editorDraft, editorOpen, spot })
}

function onMapTap(lat, lon) {
  if (pickMode.value && editorOpen.value) {
    editorDraft.lat = lat
    editorDraft.lon = lon
    pickMode.value = false
    return
  }

  if (pickMode.value) {
    editorDraft.lat = lat
    editorDraft.lon = lon
    pickMode.value = false
    editorOpen.value = true
    return
  }

  startCreateAt(lat, lon)
}

function onMarkerSelect(spot) {
  showSpotDetails(spot)
}

function showSpotDetails(spot) {
  showWorkspaceSpotDetails({ selectedSpot, detailsOpen, spot })
}

function goToSpot(spot) {
  goToSpotSelection({
    spot,
    selectedSpot,
    detailsOpen,
    state: props.state,
    mapViewportAnchor,
  })
}

function onViewportChange(center, zoom) {
  props.state.map.center = center
  props.state.map.zoom = zoom
}

async function saveSpot(spot) {
  const ok = await props.behavior.saveSpot(spot)
  if (!ok) return
  editorOpen.value = false
}

async function deleteSpot() {
  if (!requireAuth()) return
  if (!selectedSpot.value?.id) return
  const ok = await props.behavior.deleteSpot(selectedSpot.value.id)
  if (!ok) return
  detailsOpen.value = false
}

async function toggleFavorite() {
  if (!requireAuth()) return
  await toggleFavoriteSelection({
    selectedSpot,
    behavior: props.behavior,
    isFavorite,
  })
}

async function toggleFavoriteForSpot(spot) {
  if (!requireAuth()) return
  await toggleWorkspaceFavoriteForSpot({
    spot,
    behavior: props.behavior,
    isFavorite,
  })
}

async function shareSpot(message) {
  if (!requireAuth()) return false
  return shareSelectedSpot({
    selectedSpot,
    behavior: props.behavior,
    notify: props.behavior.notify,
    message,
  })
}

function pickLocationFromEditor(draft) {
  pickWorkspaceLocationFromEditor({
    editorDraft,
    editorOpen,
    pickMode,
    notify: props.behavior.notify,
    draft,
  })
}

function closeEditor() {
  closeEditorState({ editorOpen, pickMode })
}

function closeDetails() {
  closeSpotDetails({ detailsOpen })
}

function handleCreateMeetupAtSpot(spot) {
  if (!requireAuth()) return
  props.behavior.createMeetupAtSpot(spot)
}

function editFromDetails() {
  if (!requireAuth()) return
  detailsOpen.value = false
  openEditorFromSpot(selectedSpot.value)
}

function openOwnerProfile(userId) {
  const nextId = String(userId || '').trim()
  if (!nextId) return
  props.behavior.openProfile(nextId)
}

function loadMoreSpots() {
  visibleSpotCount.value += SPOT_PAGE_SIZE
}

function toggleSpotResultsExpanded() {
  visibleSpotCount.value = SPOT_PAGE_SIZE
}

async function onReload() {
  await props.behavior.reload()
}

function onSearchUsers(query, limit = 20) {
  return props.behavior.searchUsers(query, limit)
}

function onLoadFriendUsers() {
  return props.behavior.loadFriendUsers()
}

function onLoadUserProfile(userId) {
  return props.behavior.loadUserProfile(userId)
}

function onNotify(payload) {
  props.behavior.notify(payload)
}

function handleGoToCurrentLocation() {
  void initializeUserLocation()
}

function setCommentDraft(next) {
  commentDraft.value = String(next || '')
}
</script>

<template>
  <section class="map-workspace">
    <MobileMapOverlay
      :spots="state.spots"
      :filtered-spots="filteredSpots"
      :listed-spots="listedSpots"
      :center="state.map.center"
      :zoom="state.map.zoom"
      :max-bounds="mapBounds"
      :filters="spotFilters"
      :active-location-label="activeLocationLabel"
      :result-count="filteredSpots.length"
      :total-count="state.spots.length"
      :can-reset="hasActiveSpotFilters"
      :subscriptions="filterSubscriptions"
      :location-query="locationQuery"
      :location-search-busy="locationSearchBusy"
      :location-search-error="locationSearchError"
      :location-results="locationResults"
      :active-location="activeLocation"
      :owner-label="ownerLabel"
      :spot-distance-label="spotDistanceLabel"
      :is-favorite="isFavorite"
      :can-report-spot="(spot) => String(spot?.owner_id || '').trim() !== currentUserId"
      :on-map-tap="onMapTap"
      :on-marker-select="onMarkerSelect"
      :on-viewport-change="onViewportChange"
      :on-update-filters="updateSpotFilters"
      :on-reset-filters="resetSpotFilters"
      :on-subscribe-filters="subscribeCurrentFilters"
      :on-apply-subscription="applyFilterSubscription"
      :on-remove-subscription="removeFilterSubscription"
      :on-update-location-query="updateLocationQuery"
      :on-search-location="runLocationSearch"
      :on-select-location="selectLocation"
      :on-clear-location="clearLocationFilter"
      :on-reload="onReload"
      :on-go-to-current-location="handleGoToCurrentLocation"
      :on-create-spot="() => startCreateAt(state.map.center[0], state.map.center[1])"
      :on-open-spot="showSpotDetails"
      :on-toggle-favorite="toggleFavoriteForSpot"
      :on-load-more="loadMoreSpots"
      :can-load-more="canLoadMoreSpots"
      :remaining-count="remainingSpotCount"
      :on-report-spot="(spot, reason, details) => requireAuth() && props.behavior.reportContent('spot', String(spot?.id || ''), reason, details)"
    />

    <SpotEditorModal
      :open="editorOpen"
      :mode="editorMode"
      :draft="editorDraft"
      :on-cancel="closeEditor"
      :on-submit="saveSpot"
      :on-pick-location="pickLocationFromEditor"
      :on-search-users="onSearchUsers"
      :on-load-friend-users="onLoadFriendUsers"
      :on-load-user-profile="onLoadUserProfile"
      :on-notify="onNotify"
    />

    <SpotDetailsModal
      :open="detailsOpen"
      :spot="selectedSpot"
      :is-favorite="isFavorite(selectedSpot)"
      :favorite-busy="state.loading.mapFavorite"
      :can-edit="selectedSpotIsOwner"
      :can-delete="selectedSpotIsOwner"
      :can-share="true"
      :can-report="!selectedSpotIsOwner"
      :show-create-meetup="true"
      :on-close="closeDetails"
      :on-edit="editFromDetails"
      :on-delete="deleteSpot"
      :on-toggle-favorite="toggleFavorite"
      :on-share="shareSpot"
      :on-report="(spot, reason, details) => props.behavior.reportContent('spot', String(spot?.id || ''), reason, details)"
      :on-go-to-spot="goToSpot"
      :on-notify="onNotify"
      :on-load-user-profile="onLoadUserProfile"
      :on-open-owner-profile="openOwnerProfile"
      :current-user-id="currentUserId"
      :comments="comments"
      :comments-loading="commentsLoading"
      :comments-busy="commentsBusy"
      :comment-draft="commentDraft"
      :on-comment-draft-change="setCommentDraft"
      :on-create-comment="createComment"
      :on-update-comment="updateComment"
      :on-delete-comment="deleteComment"
      :on-report-comment="(comment, reason, details) => props.behavior.reportContent('comment', String(comment?.id || ''), reason, details)"
      @create-meetup-at-spot="handleCreateMeetupAtSpot"
    />
  </section>
</template>
