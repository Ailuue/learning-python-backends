import { useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import TopicPanel from './components/TopicPanel.jsx'
import { ALL_TOPICS } from './topics.js'

export default function App() {
  const [activeTopicId, setActiveTopicId] = useState(null)
  const activeTopic = ALL_TOPICS.find(t => t.id === activeTopicId) ?? null

  return (
    <div className="app-layout">
      <header className="app-topbar">
        <div className="topbar-logo">
          ⚡ FastAPI<span>/advanced</span>
        </div>
        <span className="topbar-badge">playground</span>
        <div className="topbar-links">
          <a
            className="topbar-link"
            href="http://localhost:8001/docs"
            target="_blank"
            rel="noreferrer"
          >
            Swagger UI
          </a>
          <a
            className="topbar-link"
            href="http://localhost:8001/redoc"
            target="_blank"
            rel="noreferrer"
          >
            ReDoc
          </a>
          <a
            className="topbar-link"
            href="https://fastapi.tiangolo.com/advanced/"
            target="_blank"
            rel="noreferrer"
          >
            Docs ↗
          </a>
        </div>
      </header>

      <Sidebar activeTopic={activeTopic} onSelect={t => setActiveTopicId(t.id)} />
      <TopicPanel topic={activeTopic} />
    </div>
  )
}
