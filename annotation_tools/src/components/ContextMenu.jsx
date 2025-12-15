import React, { useEffect, useRef } from "react";

export default function ContextMenu({ visible, x, y, onClose, onCreateCharacter, onCreateNarrative, onCreatePropp }) {
  const menuRef = useRef(null);

  useEffect(() => {
    if (visible && menuRef.current) {
      // Adjust position if menu would go off-screen
      const menu = menuRef.current;
      const rect = menu.getBoundingClientRect();
      const windowWidth = window.innerWidth;
      const windowHeight = window.innerHeight;

      let adjustedX = x;
      let adjustedY = y;

      // Adjust horizontal position
      if (x + rect.width > windowWidth) {
        adjustedX = windowWidth - rect.width - 10;
      }
      if (adjustedX < 10) {
        adjustedX = 10;
      }

      // Adjust vertical position
      if (y + rect.height > windowHeight) {
        adjustedY = windowHeight - rect.height - 10;
      }
      if (adjustedY < 10) {
        adjustedY = 10;
      }

      menu.style.left = `${adjustedX}px`;
      menu.style.top = `${adjustedY}px`;
    }
  }, [visible, x, y]);

  if (!visible) return null;

  return (
    <div
      ref={menuRef}
      style={{
        position: "fixed",
        left: `${x}px`,
        top: `${y}px`,
        backgroundColor: "#fff",
        border: "1px solid #ccc",
        borderRadius: "4px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        zIndex: 10000,
        minWidth: "200px",
        padding: "4px 0"
      }}
      onClick={(e) => e.stopPropagation()}
      onContextMenu={(e) => e.preventDefault()}
    >
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onCreateCharacter();
          onClose();
        }}
        style={{
          width: "100%",
          textAlign: "left",
          padding: "10px 16px",
          border: "none",
          background: "transparent",
          cursor: "pointer",
          fontSize: "0.9rem",
          transition: "background-color 0.15s"
        }}
        onMouseEnter={(e) => e.target.style.backgroundColor = "#f3f4f6"}
        onMouseLeave={(e) => e.target.style.backgroundColor = "transparent"}
      >
        <span style={{ marginRight: "8px" }}>👤</span>
        Create Character
      </button>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onCreateNarrative();
          onClose();
        }}
        style={{
          width: "100%",
          textAlign: "left",
          padding: "10px 16px",
          border: "none",
          background: "transparent",
          cursor: "pointer",
          fontSize: "0.9rem",
          transition: "background-color 0.15s"
        }}
        onMouseEnter={(e) => e.target.style.backgroundColor = "#f3f4f6"}
        onMouseLeave={(e) => e.target.style.backgroundColor = "transparent"}
      >
        <span style={{ marginRight: "8px" }}>📖</span>
        Create Narrative Event
      </button>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onCreatePropp();
          onClose();
        }}
        style={{
          width: "100%",
          textAlign: "left",
          padding: "10px 16px",
          border: "none",
          background: "transparent",
          cursor: "pointer",
          fontSize: "0.9rem",
          transition: "background-color 0.15s"
        }}
        onMouseEnter={(e) => e.target.style.backgroundColor = "#f3f4f6"}
        onMouseLeave={(e) => e.target.style.backgroundColor = "transparent"}
      >
        <span style={{ marginRight: "8px" }}>🔮</span>
        Create Propp Function
      </button>
    </div>
  );
}

