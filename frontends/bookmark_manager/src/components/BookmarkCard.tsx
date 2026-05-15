import { bookmarkApi } from '../lib/api'
import type { Bookmark, Category } from '../types'

interface Props {
  bookmark: Bookmark
  category: Category | null
  onEdit: () => void
  onDelete: () => void
  onToggleFavorite: () => void
}

function getHostname(url: string): string {
  try {
    return new URL(url).hostname
  } catch {
    return url
  }
}

function recordClick(id: number) {
  // Fire-and-forget — increments a Redis counter; the DB catches up every 10 minutes.
  bookmarkApi.recordClick(id).catch(() => undefined)
}

export default function BookmarkCard({
  bookmark,
  category,
  onEdit,
  onDelete,
  onToggleFavorite,
}: Props) {
  return (
    <div className="bg-white rounded-lg border border-zinc-200 p-4 hover:shadow-md transition-shadow flex flex-col">
      <div className="flex items-start justify-between gap-2 mb-1">
        <a
          href={bookmark.url}
          target="_blank"
          rel="noreferrer"
          onClick={() => recordClick(bookmark.id)}
          onAuxClick={(e) => {
            if (e.button === 1) recordClick(bookmark.id)
          }}
          className="font-semibold text-zinc-900 hover:text-indigo-600 truncate"
          title={bookmark.title}
        >
          {bookmark.title}
        </a>
        <button
          onClick={onToggleFavorite}
          className="shrink-0 text-lg leading-none hover:scale-110 transition-transform"
          aria-label={bookmark.favorite ? 'Unfavorite' : 'Favorite'}
        >
          {bookmark.favorite ? '⭐' : '☆'}
        </button>
      </div>

      <div className="flex items-center justify-between gap-2 mb-2">
        <a
          href={bookmark.url}
          target="_blank"
          rel="noreferrer"
          onClick={() => recordClick(bookmark.id)}
          className="text-xs text-zinc-500 hover:text-indigo-600 truncate"
          title={bookmark.url}
        >
          {getHostname(bookmark.url)}
        </a>
        {bookmark.click_count > 0 && (
          <span
            className="text-xs text-zinc-400 shrink-0"
            title={`Synced from Redis every 10 min`}
          >
            👁 {bookmark.click_count}
          </span>
        )}
      </div>

      {bookmark.description && (
        <p className="text-sm text-zinc-600 line-clamp-2 mb-3">
          {bookmark.description}
        </p>
      )}

      <div className="flex flex-wrap gap-1 mb-3 mt-auto">
        {category && (
          <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded font-medium">
            {category.name}
          </span>
        )}
        {bookmark.tags.map((t) => (
          <span
            key={t.id}
            className="text-xs px-2 py-0.5 bg-zinc-100 text-zinc-700 rounded"
          >
            #{t.name}
          </span>
        ))}
      </div>

      <div className="flex gap-3 text-sm pt-2 border-t border-zinc-100">
        <button onClick={onEdit} className="text-zinc-600 hover:text-indigo-600">
          Edit
        </button>
        <button onClick={onDelete} className="text-zinc-600 hover:text-red-600">
          Delete
        </button>
      </div>
    </div>
  )
}
