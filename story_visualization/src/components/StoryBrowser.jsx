import React, { useEffect, useState, useRef } from "react";
import { loadFolderCache } from "../utils/folderCache.js";
import "../styles/StoryBrowser.css";

export default function StoryBrowser({
  storyFiles,
  selectedIndex,
  onFilesChange,
  onPickDirectory,
  onSelectStory,
  culture,
  onCultureChange,
  isLoading = false
}) {
  const [lastFolderPath, setLastFolderPath] = useState(null);
  const fileInputRef = useRef(null);
  const isPickingDirectoryRef = useRef(false);

  useEffect(() => {
    const cache = loadFolderCache();
    if (cache && cache.folderPath) {
      setLastFolderPath(cache.folderPath);
    }
  }, [storyFiles]);

  const supportsDirectoryPicker = typeof window !== "undefined" && typeof window.showDirectoryPicker === "function";

  const wrapFileWithRelativePath = (file, relativePath) => {
    // Provide the subset of the File API this app relies on.
    return {
      name: file.name,
      webkitRelativePath: relativePath,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified,
      text: () => file.text(),
      arrayBuffer: () => file.arrayBuffer(),
      stream: () => file.stream(),
      slice: (...args) => file.slice(...args)
    };
  };

  const collectFilesFromDirHandle = async (dirHandle, rootName) => {
    const collected = [];
    let hasTextsFolder = false;

    const walk = async (handle, prefix) => {
      for await (const [entryName, entryHandle] of handle.entries()) {
        if (entryHandle.kind === "directory") {
          const dirNameLower = entryName.toLowerCase();
          
          // Walk into "texts" folder to collect story files (.txt)
          if (dirNameLower === 'texts') {
            hasTextsFolder = true;
            await walk(entryHandle, `${prefix}/${entryName}`);
          }
          // Also walk into json folders to collect annotation files
          else if (dirNameLower === 'json' || dirNameLower === 'json_v2' || dirNameLower === 'json_v3') {
            await walk(entryHandle, `${prefix}/${entryName}`);
          }
          // Skip all other directories
        } else if (entryHandle.kind === "file") {
          const fullPath = `${prefix}/${entryName}`;
          const fullPathLower = fullPath.toLowerCase();
          const lower = entryName.toLowerCase();
          
          // Collect .txt and .md files from texts folder
          if ((lower.endsWith('.txt') || lower.endsWith('.md')) && 
              (fullPathLower.includes('/texts/') || fullPathLower.endsWith('/texts'))) {
            const f = await entryHandle.getFile();
            const rel = `${prefix}/${entryName}`;
            collected.push(wrapFileWithRelativePath(f, rel));
          }
          // Collect .json files from json/json_v2/json_v3 folders (for annotation loading)
          else if (lower.endsWith('.json') && 
                   (fullPathLower.includes('/json/') || fullPathLower.includes('/json_v2/') || fullPathLower.includes('/json_v3/'))) {
            const f = await entryHandle.getFile();
            const rel = `${prefix}/${entryName}`;
            collected.push(wrapFileWithRelativePath(f, rel));
          }
        }
      }
    };

    await walk(dirHandle, rootName);
    
    return { files: collected, hasTextsFolder };
  };

  const handleOpenFolderClick = async (e) => {
    // Prevent multiple simultaneous directory picker calls
    if (isPickingDirectoryRef.current) {
      return;
    }

    // Prefer the modern directory picker when available.
    if (supportsDirectoryPicker && typeof onPickDirectory === "function") {
      e.preventDefault();
      e.stopPropagation();
      
      isPickingDirectoryRef.current = true;
      try {
        const dirHandle = await window.showDirectoryPicker();
        
        // Collect files and check if folder contains texts subfolder
        const { files, hasTextsFolder } = await collectFilesFromDirHandle(dirHandle, dirHandle.name || "selected_folder");
        
        // Validate: folder must contain a texts subfolder
        if (!hasTextsFolder) {
          alert(`Error: The selected folder must contain a 'texts' subfolder.\n\nPlease select the parent folder that contains the 'texts' folder (e.g., ChineseTales).`);
          return;
        }
        
        if (files.length === 0) {
          alert("Error: No .txt files found in the selected folder.");
          return;
        }
        
        // Use the folder name as the parent folder path
        onPickDirectory(files, dirHandle.name || "selected_folder");
      } catch (err) {
        // User cancelled
        if (err && err.name === "AbortError") {
          return;
        }
        console.error("Failed to pick directory:", err);
        alert(`Failed to select folder: ${err.message}`);
      } finally {
        isPickingDirectoryRef.current = false;
      }
      return;
    }

    // Fallback: open the legacy folder upload dialog.
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="story-browser">
      <div className="story-browser-header">
        <h2>Stories</h2>
        <label className="file-input-btn" onClick={handleOpenFolderClick}>
          Open Folder
          <input
            ref={fileInputRef}
            type="file"
            multiple
            webkitdirectory=""
            directory=""
            mozdirectory=""
            accept=".txt,.md"
            onChange={onFilesChange}
          />
        </label>
      </div>
      {lastFolderPath && storyFiles.length === 0 && (
        <div style={{
          padding: "0.5rem",
          fontSize: "0.75rem",
          color: "#64748b",
          fontStyle: "italic",
          borderBottom: "1px solid #e5e7eb"
        }}>
          Last used: {lastFolderPath}
        </div>
      )}

      <div style={{ padding: "0 0.5rem 0.5rem 0.5rem", borderBottom: "1px solid #e5e7eb" }}>
        <label style={{ fontSize: "0.8rem", display: "block", marginBottom: "0.25rem" }}>
          Default Culture
        </label>
        <select
          value={culture}
          onChange={(e) => onCultureChange(e.target.value)}
          style={{ width: "100%", padding: "0.25rem" }}
        >
          {["Chinese", "Persian", "Indian", "Japanese", "English"].map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <div className="story-list">
        {storyFiles.length === 0 && (
          <div className="empty-list-state">
            No stories loaded. Click "Open Folder" to load text files.
          </div>
        )}
        {storyFiles.map((s, idx) => (
          <button
            key={s.path || s.name + idx}
            type="button"
            className={`story-item ${idx === selectedIndex ? "active" : ""}`}
            onClick={() => onSelectStory(idx)}
            disabled={isLoading}
            style={{
              opacity: isLoading && idx !== selectedIndex ? 0.5 : 1,
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            <span className="story-item-name">{s.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
