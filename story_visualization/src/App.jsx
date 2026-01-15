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
  const location = useLocation()

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
    setSelectedStoryIndex(index)
    const story = texts[index]
    if (!story) return

    // Try to load json_v3 annotation if available
    let annotationData = null
    if (v3Map && v3Map[story.id]) {
      try {
        const jsonFile = v3Map[story.id]
        const jsonText = await jsonFile.text()
        annotationData = JSON.parse(jsonText)
        console.log(`Loaded annotation for ${story.id} from json_v3`)
      } catch (err) {
        console.warn(`Failed to load annotation for ${story.id}:`, err)
      }
    }

    // Update selected story with annotation data
    setSelectedStory({
      ...story,
      annotation: annotationData
    })

    // Save cache
    saveFolderCache({
      folderPath: selectedFolderPath,
      selectedIndex: index,
      culture: culture
    })
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
          />
        </aside>

        <main className="app-main">
          {!selectedStory ? (
            <div className="empty-state">
              <p>No story selected. Please open a folder and select a story from the sidebar.</p>
              <p style={{ fontSize: '0.9rem', color: '#64748b', marginTop: '0.5rem' }}>
                The folder should contain a <code>texts</code> subfolder with story files.
              </p>
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

