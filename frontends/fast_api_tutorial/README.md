# FastAPI Tutorial — Frontend

React UI that pairs with the [fast-api-tutorial backend](../../backends/learning/fast-api-tutorial/).

A sidebar-driven reference app: browse FastAPI topics on the left, see details and examples on the right.

## Stack

React + Vite (JSX, no TypeScript)

## Structure

```
src/
  App.jsx           — sidebar + topic panel layout
  main.jsx          — React entry point
  topics.js         — topic data (titles, descriptions, code examples)
  groups.json       — sidebar grouping/ordering
  components/
    Sidebar.jsx     — topic navigation list
    TopicPanel.jsx  — detail view for the selected topic
```

## Setup

```bash
npm install
npm run dev
```

App runs at http://localhost:5173.
