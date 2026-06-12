# Bookmark Manager — Frontend

React frontend for the [bookmark_manager backend](../../backends/bookmark_manager/).

## Features

- Auth flow (register, login, logout) with JWT stored in context
- Browse, create, edit, and delete bookmarks
- Filter by category and tag
- Responsive layout with Tailwind CSS

## Stack

| Tool | Role |
|---|---|
| React 19 | UI framework |
| React Router | Client-side routing |
| Tailwind CSS | Styling |
| Vite | Dev server and bundler |

## Structure

```
src/
  App.tsx           — router and layout
  main.tsx          — React entry point
  types.ts          — shared TypeScript types
  context/          — AuthContext (user state + JWT)
  lib/              — API client (fetch wrappers)
  components/       — reusable UI components
  pages/            — route-level page components
```

## Setup

```bash
# Start the backend first
cd ../../backends/bookmark_manager && docker compose up -d

# Then start the frontend
npm install
npm run dev
```

App runs at http://localhost:5173.
