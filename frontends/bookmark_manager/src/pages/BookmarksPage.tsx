import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { bookmarkApi, categoryApi, tagApi } from '../lib/api'
import type { Bookmark, Category, Tag } from '../types'
import BookmarkCard from '../components/BookmarkCard'
import BookmarkForm from '../components/BookmarkForm'
import CategoryForm from '../components/CategoryForm'
import Modal from '../components/Modal'

type CategoryFilter = 'all' | 'favorites' | number

export default function BookmarksPage() {
  const { user, logout } = useAuth()
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [tags, setTags] = useState<Tag[]>([])
  const [activeFilter, setActiveFilter] = useState<CategoryFilter>('all')
  const [activeTag, setActiveTag] = useState<string | null>(null)
  const [showBookmarkForm, setShowBookmarkForm] = useState(false)
  const [showCategoryForm, setShowCategoryForm] = useState(false)
  const [editingBookmark, setEditingBookmark] = useState<Bookmark | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setError('')
    try {
      const params: { category_id?: number; favorite?: boolean; tag?: string } = {}
      if (activeFilter === 'favorites') params.favorite = true
      else if (typeof activeFilter === 'number') params.category_id = activeFilter
      if (activeTag) params.tag = activeTag

      const [bms, cats, tgs] = await Promise.all([
        bookmarkApi.list(params),
        categoryApi.list(),
        tagApi.list(),
      ])
      setBookmarks(bms)
      setCategories(cats)
      setTags(tgs)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [activeFilter, activeTag])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function handleDelete(id: number) {
    if (!confirm('Delete this bookmark?')) return
    try {
      await bookmarkApi.delete(id)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  async function handleToggleFavorite(bm: Bookmark) {
    try {
      await bookmarkApi.update(bm.id, { favorite: !bm.favorite })
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    }
  }

  function headingText(): string {
    if (activeFilter === 'all') return 'All Bookmarks'
    if (activeFilter === 'favorites') return '⭐ Favorites'
    return categories.find((c) => c.id === activeFilter)?.name ?? 'Bookmarks'
  }

  return (
    <div className="min-h-screen flex flex-col bg-zinc-50">
      <header className="bg-white border-b border-zinc-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-zinc-900">📚 Bookmark Manager</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-zinc-600">{user?.username}</span>
          <button
            onClick={logout}
            className="text-sm text-zinc-600 hover:text-zinc-900"
          >
            Logout
          </button>
        </div>
      </header>

      <div className="flex flex-1">
        <aside className="w-64 bg-white border-r border-zinc-200 p-4 space-y-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-xs font-semibold uppercase text-zinc-500 tracking-wider">
                Categories
              </h2>
              <button
                onClick={() => setShowCategoryForm(true)}
                className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
              >
                + New
              </button>
            </div>
            <nav className="space-y-1">
              <button
                onClick={() => setActiveFilter('all')}
                className={`w-full text-left px-3 py-1.5 rounded-md text-sm ${
                  activeFilter === 'all'
                    ? 'bg-indigo-50 text-indigo-700 font-medium'
                    : 'text-zinc-700 hover:bg-zinc-100'
                }`}
              >
                All bookmarks
              </button>
              <button
                onClick={() => setActiveFilter('favorites')}
                className={`w-full text-left px-3 py-1.5 rounded-md text-sm ${
                  activeFilter === 'favorites'
                    ? 'bg-indigo-50 text-indigo-700 font-medium'
                    : 'text-zinc-700 hover:bg-zinc-100'
                }`}
              >
                ⭐ Favorites
              </button>
              {categories.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveFilter(c.id)}
                  className={`w-full text-left px-3 py-1.5 rounded-md text-sm ${
                    activeFilter === c.id
                      ? 'bg-indigo-50 text-indigo-700 font-medium'
                      : 'text-zinc-700 hover:bg-zinc-100'
                  }`}
                >
                  {c.name}
                </button>
              ))}
            </nav>
          </div>

          {tags.length > 0 && (
            <div>
              <h2 className="text-xs font-semibold uppercase text-zinc-500 tracking-wider mb-2">
                Tags
              </h2>
              <div className="flex flex-wrap gap-1">
                {tags.map((t) => (
                  <button
                    key={t.id}
                    onClick={() =>
                      setActiveTag(activeTag === t.name ? null : t.name)
                    }
                    className={`text-xs px-2 py-1 rounded-full transition-colors ${
                      activeTag === t.name
                        ? 'bg-indigo-600 text-white'
                        : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
                    }`}
                  >
                    {t.name}
                  </button>
                ))}
              </div>
              {activeTag && (
                <button
                  onClick={() => setActiveTag(null)}
                  className="mt-2 text-xs text-zinc-500 hover:text-zinc-700"
                >
                  Clear tag filter
                </button>
              )}
            </div>
          )}
        </aside>

        <main className="flex-1 p-6">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-zinc-900">
              {headingText()}
              {activeTag && (
                <span className="text-base font-normal text-zinc-500 ml-2">
                  · #{activeTag}
                </span>
              )}
            </h2>
            <button
              onClick={() => {
                setEditingBookmark(null)
                setShowBookmarkForm(true)
              }}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md font-medium hover:bg-indigo-700"
            >
              + Add Bookmark
            </button>
          </div>

          {error && (
            <div className="mb-4 rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-zinc-500">Loading…</div>
          ) : bookmarks.length === 0 ? (
            <div className="text-center py-16 text-zinc-500">
              <p className="mb-2">No bookmarks here yet.</p>
              <button
                onClick={() => {
                  setEditingBookmark(null)
                  setShowBookmarkForm(true)
                }}
                className="text-indigo-600 hover:underline"
              >
                Add your first one
              </button>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {bookmarks.map((bm) => (
                <BookmarkCard
                  key={bm.id}
                  bookmark={bm}
                  category={categories.find((c) => c.id === bm.category_id) ?? null}
                  onEdit={() => {
                    setEditingBookmark(bm)
                    setShowBookmarkForm(true)
                  }}
                  onDelete={() => handleDelete(bm.id)}
                  onToggleFavorite={() => handleToggleFavorite(bm)}
                />
              ))}
            </div>
          )}
        </main>
      </div>

      {showBookmarkForm && (
        <Modal onClose={() => setShowBookmarkForm(false)}>
          <BookmarkForm
            bookmark={editingBookmark}
            categories={categories}
            onCategoryCreated={(c) => setCategories((prev) => [...prev, c])}
            onSubmit={async () => {
              setShowBookmarkForm(false)
              await refresh()
            }}
            onCancel={() => setShowBookmarkForm(false)}
          />
        </Modal>
      )}

      {showCategoryForm && (
        <Modal onClose={() => setShowCategoryForm(false)}>
          <CategoryForm
            onSubmit={async () => {
              setShowCategoryForm(false)
              await refresh()
            }}
            onCancel={() => setShowCategoryForm(false)}
          />
        </Modal>
      )}
    </div>
  )
}
