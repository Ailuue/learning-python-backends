import { useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import TopicPanel from './components/TopicPanel.jsx'

export default function App() {
  const [activeTopic, setActiveTopic] = useState(null)

  return (
    <div className="app-layout">
      <header className="app-topbar">
        <div className="topbar-logo">
          ⚡ FastAPI<span>/tutorial</span>
        </div>
        <span className="topbar-badge">playground</span>
        <div className="topbar-links">
          <a
            className="topbar-link"
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
          >
            Swagger UI
          </a>
          <a
            className="topbar-link"
            href="http://localhost:8000/redoc"
            target="_blank"
            rel="noreferrer"
          >
            ReDoc
          </a>
          <a
            className="topbar-link"
            href="https://fastapi.tiangolo.com/tutorial/"
            target="_blank"
            rel="noreferrer"
          >
            Docs ↗
          </a>
        </div>
      </header>

      <Sidebar activeTopic={activeTopic} onSelect={setActiveTopic} />
      <TopicPanel topic={activeTopic} />
    </div>
  )
}
