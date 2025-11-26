import React from 'react';
import './ElementPalette.css';
import { MODE_ELEMENTS } from '../utils/elements';

export default function ElementPalette({ currentMode, addElement }) {
  const elements = MODE_ELEMENTS[currentMode] || [];

  const handleAddElement = (elem) => {
    // Add to center of canvas
    addElement(elem.type, 32, 10, elem.width, elem.height);
  };

  return (
    <div className="element-palette">
      <h3>📦 Drag Elements to Canvas</h3>
      <div className="palette-items">
        {elements.map(elem => (
          <div
            key={elem.type}
            className="palette-item"
            onClick={() => handleAddElement(elem)}
          >
            {elem.icon} {elem.label}
          </div>
        ))}
      </div>
    </div>
  );
}

