import { useEffect, useMemo, useState } from 'react'
import './App.css'

type Memory = {
  id: string
  title: string
  content: string
  project: string
  type: string
  date: string
}

type ApiMemory = {
  id: string
  content: string
  summary?: string | null
  project_name?: string | null
  memory_type?: string
  created_at?: string
}

function mapApiMemory(item: ApiMemory): Memory {
  return {
    id: item.id,
    title: item.summary?.trim() || item.content.slice(0, 60),
    content: item.content,
    project: item.project_name || 'General',
    type: item.memory_type || 'Note',
    date: item.created_at ? new Date(item.created_at).toLocaleString() : 'Saved',
  }
}

const navItems = [
  { name: 'Overview', icon: '◫' },
  { name: 'Memories', icon: '◈' },
  { name: 'Projects', icon: '▦' },
  { name: 'Sessions', icon: '◷' },
]

function App() {
  const [activePage, setActivePage] = useState('Overview')
  const [memories, setMemories] = useState<Memory[]>([])
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [newTitle, setNewTitle] = useState('')
  const [newContent, setNewContent] = useState('')
  const [newProject, setNewProject] = useState('Memora')

  const [apiError, setApiError] = useState('')

  const refreshMemories = async (query = '') => {
    try {
      const endpoint = query.trim()
        ? `/api/v1/memories/search?q=${encodeURIComponent(query)}`
        : '/api/v1/memories'
      const response = await fetch(endpoint)
      if (!response.ok) throw new Error(`API error: ${response.status}`)
      const data = await response.json()
      setMemories((data.results || []).map(mapApiMemory))
      setApiError('')
    } catch (error) {
      setApiError(error instanceof Error ? error.message : 'Cannot connect to Memora API')
    }
  }

  useEffect(() => {
    void refreshMemories()
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshMemories(search)
    }, 300)
    return () => window.clearTimeout(timer)
  }, [search])


  const filteredMemories = useMemo(() => {
    const q = search.toLowerCase()
    return memories.filter(m =>
      `${m.title} ${m.content} ${m.project} ${m.type}`.toLowerCase().includes(q)
    )
  }, [memories, search])

  const addMemory = async () => {
    if (!newTitle.trim() || !newContent.trim()) return

    try {
      const response = await fetch('/api/v1/memories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: newContent.trim(),
          summary: newTitle.trim(),
          project: newProject,
          memory_type: 'note',
          importance: 0.5,
          tags: [],
          source: 'desktop',
        }),
      })

      if (!response.ok) throw new Error(`Save failed: ${response.status}`)

      setNewTitle('')
      setNewContent('')
      setShowModal(false)
      await refreshMemories(search)
    } catch (error) {
      setApiError(error instanceof Error ? error.message : 'Could not save memory')
    }
  }

  const openEditMemory = (memory: Memory) => {
    setEditingMemory(memory)
    setEditTitle(memory.title)
    setEditContent(memory.content)
  }

  const saveEditedMemory = async () => {
    if (!editingMemory || !editTitle.trim() || !editContent.trim()) return

    try {
      const response = await fetch(`/api/v1/memories/${encodeURIComponent(editingMemory.id)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: editContent.trim(),
          summary: editTitle.trim(),
          source: 'desktop',
        }),
      })

      if (!response.ok) throw new Error(`Update failed: ${response.status}`)

      setEditingMemory(null)
      await refreshMemories(search)
    } catch (error) {
      setApiError(error instanceof Error ? error.message : 'Could not update memory')
    }
  }

  const pageDescription: Record<string, string> = {
    Overview: 'Your persistent memory, all in one place.',
    Memories: 'Search, explore and manage your saved memories.',
    Projects: 'Keep your agents and memories organized.',
    Sessions: 'A timeline of your agents activity.',
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">M</div>
          <div>
            <div className="brand-name">memora</div>
            <div className="brand-caption">MEMORY ENGINE</div>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>
        <div className="workspace-card">
          <div className="workspace-avatar">M</div>
          <div className="workspace-info">
            <strong>My Workspace</strong>
            <span>Local environment</span>
          </div>
          <span className="chevron">⌄</span>
        </div>

        <div className="nav-label">MENU</div>
        <nav className="navigation">
          {navItems.map(item => (
            <button
              key={item.name}
              className={`nav-item ${activePage === item.name ? 'active' : ''}`}
              onClick={() => setActivePage(item.name)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.name}
              {item.name === 'Memories' && <span className="nav-count">{memories.length}</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="connection">
            <span className="status-dot" />
            <div><strong>Local engine</strong><small>Connected locally</small></div>
          </div>
          <button className={`nav-item ${activePage === 'Settings' ? 'active' : ''}`} onClick={() => setActivePage('Settings')}>
            <span className="nav-icon">⚙</span> Settings
          </button>
          <div className="user-card">
            <div className="user-avatar">M</div>
            <div><strong>My account</strong><small>Personal workspace</small></div>
            <span className="more">···</span>
          </div>
          <div className="version">MEMORA v0.1.0</div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">Workspace <span>/</span> <strong>{activePage}</strong></div>
          <div className="topbar-actions">
            <div className="engine-badge"><span className="status-dot" /> Engine online</div>
            <button className="icon-button" title="Notifications">♧</button>
            <div className="top-avatar">M</div>
          </div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div>
              <div className="eyebrow">YOUR MEMORY WORKSPACE</div>
              <h1>{activePage === 'Overview' ? 'Good morning.' : activePage}</h1>
              <p>{pageDescription[activePage] || 'Manage your Memora workspace.'}</p>
            </div>
            <button className="primary-button" onClick={() => setShowModal(true)}>
              <span>＋</span> Add memory
            </button>
          </section>

          {activePage === 'Overview' && (
            <>
              <section className="stats-grid">
                <StatCard icon="◈" label="Total memories" value={String(memories.length)} change="Across your workspace" />
                <StatCard icon="▦" label="Active projects" value="03" change="Organized workspaces" />
                <StatCard icon="◷" label="Sessions" value="12" change="Agent activity records" />
                <StatCard icon="⌘" label="Connected agents" value="04" change="Across your tools" />
              </section>

              <section className="content-grid">
                <div className="panel memories-panel">
                  <div className="panel-heading">
                    <div><h2>Recent memories</h2><p>Your latest saved knowledge</p></div>
                    <button className="text-button" onClick={() => setActivePage('Memories')}>View all <span>→</span></button>
                  </div>
                  <MemoryList memories={memories.slice(0, 4)} onEdit={openEditMemory} />
                </div>

                <div className="right-column">
                  <div className="panel projects-panel">
                    <div className="panel-heading"><div><h2>Projects</h2><p>Your workspaces</p></div><button className="subtle-icon" onClick={() => setActivePage('Projects')}>···</button></div>
                    <ProjectRow color="purple" initials="M" name="Memora" detail="12 memories" />
                    <ProjectRow color="blue" initials="C" name="Core Platform" detail="8 memories" />
                    <ProjectRow color="orange" initials="P" name="Product" detail="5 memories" />
                    <button className="add-project" onClick={() => setActivePage('Projects')}>＋ Explore projects</button>
                  </div>

                  <div className="tip-card">
                    <div className="tip-icon">✳</div>
                    <div className="tip-label">MEMORA INSIGHT</div>
                    <h3>Knowledge that stays with you.</h3>
                    <p>Your agents can share a persistent memory across sessions and projects.</p>
                    <button onClick={() => setActivePage('Sessions')}>Explore activity <span>→</span></button>
                    <div className="tip-decoration">✳</div>
                  </div>
                </div>
              </section>
            </>
          )}

          {activePage === 'Memories' && (
            <section className="panel full-panel">
              <div className="panel-heading">
                <div><h2>All memories</h2><p>{memories.length} memories in your local workspace</p></div>
                <div className="search-box"><span>⌕</span><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search memories..." /></div>
              </div>
              <MemoryList memories={filteredMemories} onEdit={openEditMemory} />
              {filteredMemories.length === 0 && <div className="empty-state">No memories match your search.</div>}
            </section>
          )}

          {activePage === 'Projects' && (
            <section className="panel full-panel">
              <div className="panel-heading"><div><h2>Your projects</h2><p>Memories grouped by workspace</p></div></div>
              <ProjectRow color="purple" initials="M" name="Memora" detail="12 memories · Local project" />
              <ProjectRow color="blue" initials="C" name="Core Platform" detail="8 memories · Development" />
              <ProjectRow color="orange" initials="P" name="Product" detail="5 memories · Planning" />
            </section>
          )}

          {activePage === 'Sessions' && (
            <section className="panel full-panel">
              <div className="panel-heading"><div><h2>Recent sessions</h2><p>Agent activity in your workspace</p></div></div>
              {['Codex · Memora development', 'Cursor · API integration', 'OpenCode · Project review', 'Antigravity · Architecture notes'].map((s, i) => (
                <div className="session-row" key={s}><div className="session-icon">⌘</div><div><strong>{s}</strong><small>{i === 0 ? 'Today · Active session' : `Yesterday · Session ${i + 1}`}</small></div><span className="session-state">{i === 0 ? 'Active' : 'Completed'}</span></div>
              ))}
            </section>
          )}

          {activePage === 'Settings' && (
            <section className="panel full-panel">
              <div className="panel-heading"><div><h2>Settings</h2><p>Your local Memora environment</p></div></div>
              <div className="setting-row"><div><strong>Memory engine</strong><small>Local SQLite database</small></div><span className="engine-badge"><span className="status-dot" /> Connected</span></div>
              <div className="setting-row"><div><strong>API endpoint</strong><small>http://127.0.0.1:8765</small></div><span className="setting-value">Local</span></div>
              <div className="setting-row"><div><strong>Application version</strong><small>Memora desktop interface</small></div><span className="setting-value">0.1.0</span></div>
            </section>
          )}

          {apiError && <div className="empty-state">{apiError}</div>}
          <footer className="footer"><span>Memora <b>·</b> Persistent memory for AI agents</span><span>LOCAL FIRST <i /> YOUR DATA, YOUR CONTROL</span></footer>
        </div>
      </main>

      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-heading"><div><div className="eyebrow">SAVE KNOWLEDGE</div><h2>New memory</h2><p>Capture something worth remembering.</p></div><button className="close-button" onClick={() => setShowModal(false)}>×</button></div>
            <label>Memory title</label>
            <input className="form-input" value={newTitle} onChange={e => setNewTitle(e.target.value)} placeholder="e.g. Database architecture decision" autoFocus />
            <label>Content</label>
            <textarea className="form-input textarea" value={newContent} onChange={e => setNewContent(e.target.value)} placeholder="Write down the important details..." />
            <label>Project</label>
            <select className="form-input" value={newProject} onChange={e => setNewProject(e.target.value)}>
              <option>Memora</option><option>Core Platform</option><option>Product</option>
            </select>
            <div className="modal-actions"><button className="cancel-button" onClick={() => setShowModal(false)}>Cancel</button><button className="primary-button" onClick={addMemory} disabled={!newTitle.trim() || !newContent.trim()}>Save memory</button></div>
            <p className="modal-note">Prototype only · Not yet saved to the Memora database</p>
          </div>
        </div>
      )}

      {editingMemory && (
        <div className="modal-backdrop" onClick={() => setEditingMemory(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-heading">
              <div>
                <div className="eyebrow">UPDATE KNOWLEDGE</div>
                <h2>Edit memory</h2>
                <p>Make changes to your saved knowledge.</p>
              </div>
              <button className="close-button" onClick={() => setEditingMemory(null)}>×</button>
            </div>
            <label>Memory title</label>
            <input className="form-input" value={editTitle} onChange={e => setEditTitle(e.target.value)} autoFocus />
            <label>Content</label>
            <textarea className="form-input textarea" value={editContent} onChange={e => setEditContent(e.target.value)} />
            <div className="modal-actions">
              <button className="cancel-button" onClick={() => setEditingMemory(null)}>Cancel</button>
              <button className="save-edit-button" onClick={saveEditedMemory} disabled={!editTitle.trim() || !editContent.trim()}>Save changes</button>
            </div>
            <p className="modal-note">Changes are saved to the Memora database.</p>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon, label, value, change }: { icon: string; label: string; value: string; change: string }) {
  return <div className="stat-card"><div className="stat-top"><span className="stat-icon">{icon}</span><span className="stat-menu">···</span></div><div className="stat-value">{value}</div><div className="stat-label">{label}</div><div className="stat-change">{change}</div></div>
}

function MemoryList({ memories, onEdit }: { memories: Memory[]; onEdit: (memory: Memory) => void }) {
  return <div className="memory-list">{memories.map(m => (
    <div className="memory-row" key={m.id}>
      <div className="memory-symbol">◈</div>
      <div className="memory-main">
        <strong>{m.title}</strong>
        <p>{m.content}</p>
        <div className="memory-meta"><span>{m.project}</span><span className="meta-dot">·</span><span>{m.type}</span></div>
      </div>
      <span className="memory-date">{m.date}</span>
      <button className="edit-memory-button" onClick={() => onEdit(m)}>Edit Memory</button>
    </div>
  ))}</div>
}

function ProjectRow({ color, initials, name, detail }: { color: string; initials: string; name: string; detail: string }) {
  return <div className="project-row"><div className={`project-avatar ${color}`}>{initials}</div><div className="project-info"><strong>{name}</strong><small>{detail}</small></div><span className="project-arrow">→</span></div>
}

export default App

