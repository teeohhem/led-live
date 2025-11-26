import React from 'react';
import './ContextMenu.css';

export default function ContextMenu({ x, y, onDuplicate, onDelete, onOptimize }) {
  return (
    <div 
      className="context-menu" 
      style={{ left: x, top: y }}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="context-menu-item" onClick={onDuplicate}>
        📋 Duplicate
      </div>
      <div className="context-menu-item" onClick={onOptimize}>
        ✨ Optimize Space
      </div>
      <div className="context-menu-divider"></div>
      <div className="context-menu-item danger" onClick={onDelete}>
        🗑️ Delete
      </div>
    </div>
  );
}

