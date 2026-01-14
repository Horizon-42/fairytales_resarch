import React, { useEffect, useState, useRef } from "react";
import { loadFolderCache } from "../utils/folderCache.js";

export default function StoryBrowser({
  storyFiles,
  selectedIndex,
  onFilesChange,
  onPickDirectory,
  onSelectStory,
  culture,
  onCultureChange
}) {
  const [lastFolderPath, setLastFolderPath] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    const cache = loadFolderCache();
    if (cache && cache.folderPath) {
      setLastFolderPath(cache.folderPath);
    }
  }, [storyFiles]); // Update when storyFiles change

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
    const allowed = [".txt", ".md", ".json"];
    let hasTextsFolder = false;

    const walk = async (handle, prefix) => {
      for await (const [entryName, entryHandle] of handle.entries()) {
        if (entryHandle.kind === "directory") {
          const dirNameLower = entryName.toLowerCase();
          
          // Check if this is a texts folder (case insensitive)
          if (dirNameLower === 'texts') {
            hasTextsFolder = true;
            // Only walk into texts folder, not traditional_texts
            await walk(entryHandle, `${prefix}/${entryName}`);
          } else if (dirNameLower === 'traditional_texts') {
            // Skip traditional_texts folder - don't walk into it
            continue;
          } else {
            // Walk into other directories
            await walk(entryHandle, `${prefix}/${entryName}`);
          }
        } else if (entryHandle.kind === "file") {
          // Only collect files that are in the texts folder (not traditional_texts)
          // Check if the path contains traditional_texts
          const fullPath = `${prefix}/${entryName}`;
          if (fullPath.toLowerCase().includes('/traditional_texts/')) {
            continue; // Skip files in traditional_texts folder
          }
          
          const lower = entryName.toLowerCase();
          if (!allowed.some((ext) => lower.endsWith(ext))) continue;

          const f = await entryHandle.getFile();
          const rel = `${prefix}/${entryName}`;
          collected.push(wrapFileWithRelativePath(f, rel));
        }
      }
    };

    await walk(dirHandle, rootName);
    
    return { files: collected, hasTextsFolder };
  };

  const handleOpenFolderClick = async (e) => {
    // Prefer the modern directory picker on Linux Chrome when available.
    if (supportsDirectoryPicker && typeof onPickDirectory === "function") {
      e.preventDefault();
      e.stopPropagation();
      try {
        const dirHandle = await window.showDirectoryPicker();
        
        // Collect files and check if folder contains texts subfolder
        const { files, hasTextsFolder } = await collectFilesFromDirHandle(dirHandle, dirHandle.name || "selected_folder");
        
        // Validate: folder must contain a texts subfolder
        if (!hasTextsFolder) {
          alert(`错误：选择的文件夹必须包含 "texts" 子文件夹。\n\n请选择包含 texts 文件夹的父文件夹（例如：Japanese_test2）。`);
          return;
        }
        
        if (files.length === 0) {
          alert("错误：选择的文件夹中没有找到任何 .txt 文件。");
          return;
        }
        
        // Use the folder name as the parent folder path
        // This is the folder the user selected (which contains texts subfolder)
        onPickDirectory(files, dirHandle.name || "selected_folder");
      } catch (err) {
        // User cancelled
        if (err && err.name === "AbortError") return;
        console.error("Failed to pick directory:", err);
        alert(`选择文件夹失败: ${err.message}`);
      }
      return;
    }

    // Fallback: open the legacy folder upload dialog.
    // (Some environments still block programmatic clicks; label+input will still work.)
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
            // Folder selection (supported in Chromium-based browsers; Firefox support varies)
            webkitdirectory=""
            directory=""
            mozdirectory=""
            // Allow the common story text formats in this repo
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

