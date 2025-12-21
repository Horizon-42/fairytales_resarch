import React, { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import CharacterGraph from './pages/CharacterGraph'
import StoryRibbons from './pages/StoryRibbons'
import './styles/App.css'

function App() {
  const [stories, setStories] = useState([])
  const [selectedStory, setSelectedStory] = useState(null)
  const [loading, setLoading] = useState(true)
  const location = useLocation()

  useEffect(() => {
    fetch('/data/stories_index.json')
      .then(res => res.json())
      .then(data => {
        setStories(data.stories || [])
        if (data.stories && data.stories.length > 0) {
          setSelectedStory(data.stories[0])
        }
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load stories index:', err)
        setLoading(false)
      })
  }, [])

  const handleStorySelect = (e) => {
    const story = stories.find(s => s.id === e.target.value)
    setSelectedStory(story)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">
            <span className="title-main">Fairytale Visualization</span>
            <span className="title-sub">Story Analysis Framework</span>
          </h1>
          
          <nav className="main-nav">
            <Link 
              to="/" 
              className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
            >
              <span className="nav-icon">◎</span>
              Character Graph
            </Link>
            <Link 
              to="/ribbons" 
              className={`nav-link ${location.pathname === '/ribbons' ? 'active' : ''}`}
            >
              <span className="nav-icon">≋</span>
              Story Ribbons
            </Link>
          </nav>

          <div className="story-selector">
            <label htmlFor="story-select">Select Story:</label>
            <select 
              id="story-select"
              value={selectedStory?.id || ''} 
              onChange={handleStorySelect}
              disabled={loading || stories.length === 0}
            >
              {stories.map(story => (
                <option key={story.id} value={story.id}>
                  {story.title || story.id}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      <main className="app-main">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading stories...</p>
          </div>
        ) : !selectedStory ? (
          <div className="empty-state">
            <p>No stories found. Please run the data processing script first.</p>
            <code>python3 post_data_process/process_json_for_viz.py</code>
          </div>
        ) : (
          <Routes>
            <Route 
              path="/" 
              element={<CharacterGraph story={selectedStory} />} 
            />
            <Route 
              path="/ribbons" 
              element={<StoryRibbons story={selectedStory} />} 
            />
          </Routes>
        )}
      </main>

      <footer className="app-footer">
        <p>Fairytale Research Project • Visualization Framework</p>
      </footer>
    </div>
  )
}

export default App

