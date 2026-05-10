import { useState } from 'react'
import { GROUPS } from '../topics.js'

const METHOD_COLORS = {
  GET: '#3fb950', POST: '#58a6ff', PUT: '#d29922',
  PATCH: '#bc8cff', DELETE: '#f85149',
}

export default function Sidebar({ activeTopic, onSelect }) {
  const [collapsed, setCollapsed] = useState({})

  function toggle(id) {
    setCollapsed(c => ({ ...c, [id]: !c[id] }))
  }

  return (
    <nav className="sidebar">
      {GROUPS.map(group => {
        const isOpen = !collapsed[group.id]
        return (
          <div key={group.id} className="sidebar-group">
            <div
              className="sidebar-group-header"
              onClick={() => toggle(group.id)}
            >
              {group.label}
              <span className={`sidebar-chevron ${isOpen ? 'open' : ''}`}>▶</span>
            </div>
            {isOpen && (
              <div className="sidebar-items">
                {group.topics.map(topic => {
                  const firstMethod = topic.endpoints[0]?.method ?? 'GET'
                  return (
                    <div
                      key={topic.id}
                      className={`sidebar-item ${activeTopic?.id === topic.id ? 'active' : ''}`}
                      onClick={() => onSelect(topic)}
                    >
                      <span
                        className="method-badge"
                        style={{
                          background: `${METHOD_COLORS[firstMethod]}22`,
                          color: METHOD_COLORS[firstMethod],
                        }}
                      >
                        {firstMethod}
                      </span>
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {topic.number}. {topic.title}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </nav>
  )
}
