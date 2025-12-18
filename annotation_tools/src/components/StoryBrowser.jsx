import React, { useEffect, useState } from "react";
import { loadFolderCache } from "../utils/folderCache.js";

export default function StoryBrowser({
  storyFiles,
  selectedIndex,
  onFilesChange,
  onSelectStory,
  culture,
  onCultureChange
}) {
  const [lastFolderPath, setLastFolderPath] = useState(null);

  useEffect(() => {
    const cache = loadFolderCache();
    if (cache && cache.folderPath) {
      setLastFolderPath(cache.folderPath);
    }
  }, [storyFiles]); // Update when storyFiles change

  return (
    <div className="story-browser">
      <div className="story-browser-header">
        <h2>Stories</h2>
        <label className="file-input-btn">
          Open Folder
          <input
            type="file"
            multiple
            webkitdirectory="true"
            directory="true"
            accept=".txt"
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
          <br />
          <span style={{ fontSize: "0.7rem" }}>
            Re-select this folder to auto-restore your last selection
          </span>
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
          >
            <span className="story-item-name">{s.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

