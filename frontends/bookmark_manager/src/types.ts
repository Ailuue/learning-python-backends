export interface User {
  id: number
  email: string
  username: string
  is_active: boolean
}

export interface Token {
  access_token: string
  token_type: string
}

export interface Tag {
  id: number
  name: string
}

export interface Category {
  id: number
  name: string
  description: string | null
}

export interface Bookmark {
  id: number
  url: string
  title: string
  description: string | null
  favorite: boolean
  click_count: number
  category_id: number | null
  created_at: string
  updated_at: string
  tags: Tag[]
}

export interface BookmarkInput {
  url: string
  title?: string
  description?: string
  favorite?: boolean
  category_id?: number | null
  tags?: string[]
}

export interface CategoryInput {
  name: string
  description?: string
}
