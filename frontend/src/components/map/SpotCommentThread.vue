<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { routeToAuth } from '../../router/routeSpec'
import { useOwnerProfiles } from '../../composables/useOwnerProfiles'
import ActionButton from '../common/ActionButton.vue'
import AppTextField from '../common/AppTextField.vue'
import ReportContentModal from '../common/ReportContentModal.vue'

const props = defineProps({
  comments: { type: Array, default: () => [] },
  commentsLoading: { type: Boolean, default: false },
  commentsBusy: { type: Boolean, default: false },
  commentDraft: { type: String, default: '' },
  currentUserId: { type: String, default: '' },
  onCommentDraftChange: { type: Function, default: null },
  onCreateComment: { type: Function, default: null },
  onUpdateComment: { type: Function, default: null },
  onDeleteComment: { type: Function, default: null },
  onReportComment: { type: Function, default: null },
  onLoadUserProfile: { type: Function, default: null },
})

const router = useRouter()
const editingCommentId = ref('')
const editingCommentDraft = ref('')
const reportComment = ref(null)
const reportBusy = ref(false)

function requireAuth() {
  if (!String(props.currentUserId || '').trim()) {
    router.push(routeToAuth())
    return false
  }
  return true
}
const { ownerLabel, warmOwnerProfiles } = useOwnerProfiles((userId) => props.onLoadUserProfile(userId))

watch(
  () => props.comments,
  (comments) => {
    if (typeof props.onLoadUserProfile !== 'function') return
    void warmOwnerProfiles((comments || []).map((comment) => ({ owner_id: comment?.user_id })))
  },
  { immediate: true, deep: true },
)

function updateCommentDraft(next) {
  if (typeof props.onCommentDraftChange !== 'function') return
  props.onCommentDraftChange(String(next || ''))
}

async function submitComment() {
  if (typeof props.onCreateComment !== 'function') return
  if (!requireAuth()) return
  await props.onCreateComment(String(props.commentDraft || ''))
}

function isCommentOwner(comment) {
  const me = String(props.currentUserId || '').trim()
  const owner = String(comment?.user_id || '').trim()
  return Boolean(me && owner && me === owner)
}

function beginEditComment(comment) {
  if (!isCommentOwner(comment)) return
  editingCommentId.value = String(comment?.id || '')
  editingCommentDraft.value = String(comment?.message || '')
}

function cancelEditComment() {
  editingCommentId.value = ''
  editingCommentDraft.value = ''
}

async function saveCommentEdit(comment) {
  if (typeof props.onUpdateComment !== 'function') return
  const id = String(comment?.id || '').trim()
  if (!id) return
  const ok = await props.onUpdateComment(id, editingCommentDraft.value)
  if (ok) cancelEditComment()
}

async function removeComment(comment) {
  if (typeof props.onDeleteComment !== 'function') return
  const id = String(comment?.id || '').trim()
  if (!id) return
  await props.onDeleteComment(id)
}

function formatCommentDate(value) {
  const text = String(value || '').trim()
  if (!text) return ''
  const date = new Date(text)
  if (Number.isNaN(date.getTime())) return text
  return date.toLocaleString()
}

function commentAuthorLabel(comment) {
  return ownerLabel(comment?.user_id)
}

function openReportDialog(comment) {
  if (isCommentOwner(comment) || typeof props.onReportComment !== 'function') return
  reportComment.value = comment
}

function closeReportDialog() {
  reportComment.value = null
}

async function submitReport(payload) {
  if (typeof props.onReportComment !== 'function' || !reportComment.value) return false
  reportBusy.value = true
  try {
    return await props.onReportComment(reportComment.value, payload.reason, payload.details)
  } finally {
    reportBusy.value = false
  }
}
</script>

<template>
  <section class="comments-box">
    <header class="d-flex align-items-center justify-content-between gap-2">
      <h4 class="h6 mb-0">Comments</h4>
      <span class="small text-secondary" v-if="commentsLoading">Loading...</span>
    </header>

    <div class="comments-create" v-if="String(currentUserId || '').trim() && typeof onCreateComment === 'function'">
      <AppTextField
        bare
        class-name="form-control"
        :model-value="commentDraft"
        maxlength="2000"
        placeholder="Write a comment"
        aria-label="Comment message"
        @update:model-value="updateCommentDraft"
      />
      <ActionButton
        class-name="btn btn-outline-secondary"
        icon="bi-chat-dots"
        label="Post"
        :disabled="commentsBusy"
        @click="submitComment"
      />
    </div>
    <div class="comments-create" v-else-if="!String(currentUserId || '').trim()">
      <ActionButton
        class-name="btn btn-outline-primary btn-sm"
        icon="bi-box-arrow-in-right"
        label="Sign in to comment"
        @click="requireAuth"
      />
    </div>

    <div class="comments-empty text-secondary small" v-if="!commentsLoading && !comments.length">
      No comments yet.
    </div>

    <div class="comments-list" v-else>
      <article v-for="comment in comments" :key="comment.id" class="comment-row">
        <div class="d-flex justify-content-between align-items-start gap-2">
          <div class="small text-secondary">
            <i class="bi bi-person-circle me-1"></i>{{ commentAuthorLabel(comment) }}
          </div>
          <div class="small text-secondary">{{ formatCommentDate(comment.updated_at || comment.created_at) }}</div>
        </div>

        <template v-if="editingCommentId === comment.id">
          <AppTextField
            bare
            class-name="form-control"
            v-model="editingCommentDraft"
            maxlength="2000"
            placeholder="Edit comment"
            aria-label="Edit comment"
          />
          <div class="d-flex gap-2 mt-2">
            <ActionButton class-name="btn btn-sm btn-outline-primary" label="Save" :disabled="commentsBusy" @click="saveCommentEdit(comment)" />
            <ActionButton class-name="btn btn-sm btn-outline-secondary" label="Cancel" @click="cancelEditComment" />
          </div>
        </template>
        <p v-else class="mb-2">{{ comment.message }}</p>

        <div class="d-flex flex-wrap gap-2" v-if="editingCommentId !== comment.id">
          <ActionButton class-name="btn btn-sm btn-outline-secondary" label="Edit" @click="beginEditComment(comment)" v-if="isCommentOwner(comment)" />
          <ActionButton class-name="btn btn-sm btn-outline-danger" label="Delete" :disabled="commentsBusy" @click="removeComment(comment)" v-if="isCommentOwner(comment)" />
          <ActionButton class-name="btn btn-sm btn-outline-danger" icon="bi-flag" label="Report" @click="openReportDialog(comment)" v-if="!isCommentOwner(comment) && typeof onReportComment === 'function'" />
        </div>
      </article>
    </div>
  </section>

  <ReportContentModal
    :open="Boolean(reportComment)"
    title="Report comment"
    target-label="this comment"
    :target-description="reportComment?.message || ''"
    :busy="reportBusy"
    :on-close="closeReportDialog"
    :on-submit="submitReport"
  />
</template>
