import React from "react";

export default function StoryBrowser({
  storyFiles,
  selectedIndex,
  onFilesChange,
  onSelectStory,
  culture,
  onCultureChange
}) {
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

      <div style={{ padding: "0 0.5rem 0.5rem 0.5rem", borderBottom: "1px solid #e5e7eb" }}>
        <label style={{ fontSize: "0.8rem", display: "block", marginBottom: "0.25rem" }}>
          Default Culture
        </label>
        <select
          value={culture}
          onChange={(e) => onCultureChange(e.target.value)}
          style={{ width: "100%", padding: "0.25rem" }}
        >
          {["Chinese", "Persian", "Indian", "Japanese"].map((c) => (
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

