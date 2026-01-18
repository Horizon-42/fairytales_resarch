import React, { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import CharacterGraph from './pages/CharacterGraph'
import StoryRibbons from './pages/StoryRibbons'
import Segmentation from './pages/Segmentation'
import StoryBrowser from './components/StoryBrowser'
import { organizeFiles } from './utils/fileHandler'
import { saveFolderCache, loadFolderCache, extractFolderPath } from './utils/folderCache'
import './styles/App.css'

function App() {
  const [storyFiles, setStoryFiles] = useState([])
  const [selectedStoryIndex, setSelectedStoryIndex] = useState(-1)
  const [selectedStory, setSelectedStory] = useState(null)
  const [selectedFolderPath, setSelectedFolderPath] = useState(null)
  const [culture, setCulture] = useState("Chinese")
  const [v2JsonFiles, setV2JsonFiles] = useState({})
  const [v3JsonFiles, setV3JsonFiles] = useState({})
  const [isLoadingStory, setIsLoadingStory] = useState(false)
  const location = useLocation()
  
  // Backend URL configuration
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

  // Load cached folder selection on mount
  useEffect(() => {
    const cache = loadFolderCache()
    if (cache && cache.culture) {
      setCulture(cache.culture)
    }
  }, [])

  const loadFilesFromFolderSelection = async (files, folderPathHint = null) => {
    const { texts, v2Jsons, v3Jsons } = organizeFiles(files)
    texts.sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true, sensitivity: 'base' }))

    // Read text content from files
    const withContent = await Promise.all(
      texts.map(async (t) => {
        const textRaw = await t.file.text()
        const text = textRaw.replace(/\r\n/g, '\n')
        return { ...t, name: t.file.name, text, id: t.id, path: t.path }
      })
    )

    setStoryFiles(withContent)
    setV2JsonFiles(v2Jsons)
    setV3JsonFiles(v3Jsons)

    // Extract parent folder path
    let folderPath = extractFolderPath(files, folderPathHint)
    if (!folderPath && folderPathHint) {
      folderPath = folderPathHint
    }

    if (!folderPath) {
      alert("Error: Unable to determine parent folder path. Please ensure the selected folder contains a 'texts' subfolder.")
      return
    }

    // Load cache from the folder
    const cache = loadFolderCache()
    const targetIndex = (cache && cache.selectedIndex >= 0 && cache.selectedIndex < withContent.length)
      ? cache.selectedIndex
      : 0

    // Set culture from cache if available
    if (cache && cache.culture) {
      setCulture(cache.culture)
    }

    // Save folder cache
    saveFolderCache({
      folderPath: folderPath,
      selectedIndex: targetIndex,
      culture: culture
    })

    setSelectedFolderPath(folderPath)

    if (withContent.length > 0) {
      handleSelectStory(targetIndex, withContent, v2Jsons, v3Jsons)
    }
  }

  const handleStoryFilesChange = async (event) => {
    const files = event.target.files
    if (!files) return
    await loadFilesFromFolderSelection(files)
  }

  const handlePickDirectory = async (files, folderName) => {
    await loadFilesFromFolderSelection(files, folderName)
  }

  const handleSelectStory = async (index, texts = storyFiles, v2Map = v2JsonFiles, v3Map = v3JsonFiles) => {
    // Prevent multiple simultaneous selections
    if (isLoadingStory) {
      console.log('Story loading in progress, ignoring selection')
      return
    }

    setSelectedStoryIndex(index)
    const story = texts[index]
    if (!story) return

    // Set loading state
    setIsLoadingStory(true)

    try {
      // Try to load json_v3 annotation if available
      let annotationData = null
      let relationshipData = null
      let ribbonData = null
      
      if (v3Map && v3Map[story.id]) {
        try {
          const jsonFile = v3Map[story.id]
          const jsonText = await jsonFile.text()
          annotationData = JSON.parse(jsonText)
          console.log(`[App] Loaded annotation for ${story.id} from json_v3`)
          
          // Process visualization data via backend API
          try {
            console.log(`[App] Processing visualization data for ${story.id} via API...`)
            const response = await fetch(`${BACKEND_URL}/api/visualization/process`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                story_data: annotationData
              })
            })
            
            if (response.ok) {
              const result = await response.json()
              relationshipData = result.relationship_data
              ribbonData = result.ribbon_data
              console.log(`[App] Successfully processed visualization data for ${story.id}`)
            } else {
              const errorText = await response.text()
              console.error(`[App] Failed to process visualization data for ${story.id}:`, errorText)
            }
          } catch (err) {
            console.error(`[App] Failed to call visualization API for ${story.id}:`, err)
          }
        } catch (err) {
          console.error(`[App] Failed to load annotation for ${story.id}:`, err)
        }
      }

      // Update selected story with annotation and visualization data
      setSelectedStory({
        ...story,
        annotation: annotationData,
        relationshipData: relationshipData,
        ribbonData: ribbonData
      })

      // Save cache
      saveFolderCache({
        folderPath: selectedFolderPath,
        selectedIndex: index,
        culture: culture
      })
    } finally {
      // Clear loading state
      setIsLoadingStory(false)
    }
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
            <Link 
              to="/segmentation" 
              className={`nav-link ${location.pathname === '/segmentation' ? 'active' : ''}`}
            >
              <span className="nav-icon">✂</span>
              Segmentation
            </Link>
          </nav>
        </div>
      </header>

      <div className="app-layout">
        <aside className="app-sidebar">
          <StoryBrowser
            storyFiles={storyFiles}
            selectedIndex={selectedStoryIndex}
            onFilesChange={handleStoryFilesChange}
            onPickDirectory={handlePickDirectory}
            onSelectStory={handleSelectStory}
            culture={culture}
            onCultureChange={setCulture}
            isLoading={isLoadingStory}
          />
        </aside>

        <main className="app-main">
          {isLoadingStory && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              gap: '1rem',
              color: '#64748b'
            }}>
              <div style={{
                width: '40px',
                height: '40px',
                border: '4px solid #e5e7eb',
                borderTop: '4px solid #3b82f6',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              <p>Loading story data...</p>
              <style>{`
                @keyframes spin {
                  0% { transform: rotate(0deg); }
                  100% { transform: rotate(360deg); }
                }
              `}</style>
            </div>
          )}
          {!isLoadingStory && !selectedStory ? (
            <div className="empty-state">
              <p>No story selected. Please open a folder and select a story from the sidebar.</p>
              <p style={{ fontSize: '0.9rem', color: '#64748b', marginTop: '0.5rem' }}>
                The folder should contain a <code>texts</code> subfolder with story files.
              </p>
            </div>
          ) : !isLoadingStory && (
            <Routes>
              <Route 
                path="/" 
                element={<CharacterGraph story={selectedStory} />} 
              />
              <Route 
                path="/ribbons" 
                element={<StoryRibbons story={selectedStory} />} 
              />
              <Route 
                path="/segmentation" 
                element={<Segmentation story={selectedStory} />} 
              />
            </Routes>
          )}
        </main>
      </div>

      <footer className="app-footer">
        <p>Fairytale Research Project • Visualization Framework</p>
      </footer>
    </div>
  )
}

export default App

