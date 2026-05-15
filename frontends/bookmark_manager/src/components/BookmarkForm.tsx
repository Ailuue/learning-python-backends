import { useState, type FormEvent } from 'react'
import { bookmarkApi, categoryApi } from '../lib/api'
import type { Bookmark, Category } from '../types'

interface Props {
  bookmark: Bookmark | null
  categories: Category[]
  onCategoryCreated?: (category: Category) => void
  onSubmit: () => void
  onCancel: () => void
}

export default function BookmarkForm({
  bookmark,
  categories,
  onCategoryCreated,
  onSubmit,
  onCancel,
}: Props) {
  const [url, setUrl] = useState(bookmark?.url ?? '')
  const [title, setTitle] = useState(bookmark?.title ?? '')
  const [description, setDescription] = useState(bookmark?.description ?? '')
  const [favorite, setFavorite] = useState(bookmark?.favorite ?? false)
  const [categoryId, setCategoryId] = useState<string>(
    bookmark?.category_id != null ? String(bookmark.category_id) : ''
  )
  const [tagsInput, setTagsInput] = useState(
    bookmark?.tags.map((t) => t.name).join(', ') ?? ''
  )
  const [showNewCategory, setShowNewCategory] = useState(false)
  const [newCategoryName, setNewCategoryName] = useState('')
  const [creatingCategory, setCreatingCategory] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleCreateCategory() {
    const name = newCategoryName.trim()
    if (!name) return
    setError('')
    setCreatingCategory(true)
    try {
      const created = await categoryApi.create({ name })
      onCategoryCreated?.(created)
      setCategoryId(String(created.id))
      setNewCategoryName('')
      setShowNewCategory(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create category')
    } finally {
      setCreatingCategory(false)
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const tags = tagsInput
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean)
      const payload = {
        url,
        title: title || undefined,
        description: description || undefined,
        favorite,
        category_id: categoryId ? Number(categoryId) : null,
        tags,
      }
      if (bookmark) {
        await bookmarkApi.update(bookmark.id, payload)
      } else {
        await bookmarkApi.create(payload)
      }
      onSubmit()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-xl font-bold text-zinc-900">
        {bookmark ? 'Edit bookmark' : 'New bookmark'}
      </h2>

      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-1">
          URL <span className="text-red-500">*</span>
        </label>
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className="w-full rounded-md border border-zinc-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-1">
          Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Auto-fetched from page if empty"
          className="w-full rounded-md border border-zinc-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-1">
          Description
        </label>
        <textarea
          value={description ?? ''}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="block text-sm font-medium text-zinc-700">Category</label>
          {!showNewCategory && (
            <button
              type="button"
              onClick={() => setShowNewCategory(true)}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
            >
              + New category
            </button>
          )}
        </div>
        {showNewCategory ? (
          <div className="flex gap-2">
            <input
              type="text"
              autoFocus
              value={newCategoryName}
              onChange={(e) => setNewCategoryName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleCreateCategory()
                }
              }}
              placeholder="Category name"
              className="flex-1 rounded-md border border-zinc-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="button"
              onClick={handleCreateCategory}
              disabled={creatingCategory || !newCategoryName.trim()}
              className="px-3 py-2 rounded-md bg-indigo-600 text-white text-sm hover:bg-indigo-700 disabled:opacity-50"
            >
              {creatingCategory ? '…' : 'Add'}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowNewCategory(false)
                setNewCategoryName('')
              }}
              className="px-3 py-2 rounded-md text-zinc-700 text-sm hover:bg-zinc-100"
            >
              Cancel
            </button>
          </div>
        ) : (
          <select
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value)}
            className="w-full rounded-md border border-zinc-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">— None —</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-1">
          Tags
        </label>
        <input
          type="text"
          value={tagsInput}
          onChange={(e) => setTagsInput(e.target.value)}
          placeholder="comma, separated, list"
          className="w-full rounded-md border border-zinc-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={favorite}
          onChange={(e) => setFavorite(e.target.checked)}
          className="rounded"
        />
        <span className="text-sm text-zinc-700">Favorite</span>
      </label>

      <div className="flex gap-2 justify-end pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded-md text-zinc-700 hover:bg-zinc-100"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {submitting ? 'Saving…' : bookmark ? 'Update' : 'Create'}
        </button>
      </div>
    </form>
  )
}
