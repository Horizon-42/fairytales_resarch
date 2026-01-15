# File Browser Integration for Story Visualization

This document describes the file browser integration that allows loading stories directly from folders, similar to the annotation_tools interface.

## Overview

The story visualization now supports:
- Opening folders from the browser (using File System Access API or folder upload)
- Loading story text files from `texts/` subfolder
- Caching folder selections and last used story
- Support for loading annotation JSON files (future feature)

## File Structure

The expected folder structure is:
```
ParentFolder/
├── texts/
│   ├── CH_001_story.txt
│   ├── CH_002_story.txt
│   └── ...
├── json_v2/ (optional, for future annotation loading)
│   └── ...
└── json_v3/ (optional, for future annotation loading)
    └── ...
```

## Usage

1. Click "Open Folder" in the sidebar
2. Select a folder that contains a `texts` subfolder
3. The stories from `texts/` will be loaded and displayed in the sidebar
4. Click on a story to select it
5. The story text will be automatically loaded in the Segmentation page

## Implementation Details

### Components

- **StoryBrowser.jsx**: File browser component (copied from annotation_tools)
- **fileHandler.js**: File organization utilities
- **folderCache.js**: LocalStorage-based folder cache

### Data Flow

1. User opens folder → `handlePickDirectory` or `handleStoryFilesChange`
2. Files are organized using `organizeFiles()` → separates texts and JSON files
3. Text files are read → `file.text()` to get content
4. Story list is populated → displayed in StoryBrowser
5. User selects story → `handleSelectStory` → story object passed to pages
6. Pages read `story.text` directly

## Story Object Structure

After loading, story objects have:
```javascript
{
  id: "CH_001_story",      // Filename without extension
  name: "CH_001_story.txt", // Full filename
  text: "...",              // File content
  path: "texts/CH_001_story.txt", // Relative path
  file: File               // Original file object
}
```

## Testing

Run tests with:
```bash
npm test
```

Test files are in `src/utils/__tests__/`:
- `fileHandler.test.js`: Tests for file organization
- `folderCache.test.js`: Tests for folder caching

## Future Enhancements

- Load annotation JSON files (v2/v3) when available
- Merge annotation data with story text
- Support for multiple annotation versions
