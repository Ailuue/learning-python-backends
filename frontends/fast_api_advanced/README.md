# FastAPI Advanced — Frontend

React UI that pairs with the [advanced FastAPI backend](../../backends/learning/fast-api-tutorial/advanced/).

Same sidebar-driven reference layout as `fast_api_tutorial`, focused on advanced FastAPI patterns.

## Stack

React + Vite (JSX, no TypeScript)

## Structure

```
src/
  App.jsx           — sidebar + topic panel layout
  main.jsx          — React entry point
  topics.js         — advanced topic data
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
