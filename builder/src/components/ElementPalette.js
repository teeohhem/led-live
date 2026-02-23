import React from 'react';
import './ElementPalette.css';
import { MODE_ELEMENTS, ELEMENT_GROUPS } from '../utils/elements';

export default function ElementPalette({ currentMode, currentScenario, addElement, addElements }) {
  const elements = MODE_ELEMENTS[currentMode] || [];

  // Only show groups relevant to the current scenario
  const allGroups = ELEMENT_GROUPS[currentMode] || [];
  const groups = allGroups.filter(
    g => !g.scenarios || g.scenarios.includes(currentScenario)
  );

  const handleAddElement = (elem) => {
    addElement(elem.type, 32, 10, elem.width, elem.height);
  };

  const handleAddGroup = (group) => {
    addElements(group.elements);
  };

  return (
    <div className="element-palette">
      {/* ---- Quick Groups ---- */}
      {groups.length > 0 && (
        <div className="palette-section">
          <div className="palette-section-header">
            <span className="palette-section-title">⚡ Quick Groups</span>
            <span className="palette-section-hint">place a complete set in one click</span>
          </div>
          <div className="group-items">
            {groups.map(group => (
              <button
                key={group.id}
                className="group-item"
                onClick={() => handleAddGroup(group)}
                title={group.description}
              >
                <span className="group-icon">{group.icon}</span>
                <span className="group-label">{group.label}</span>
                <span className="group-count">{group.elements.length} elements</span>
                <span className="group-desc">{group.description}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ---- Individual Elements ---- */}
      <div className="palette-section">
        <div className="palette-section-header">
          <span className="palette-section-title">📦 Individual Elements</span>
          <span className="palette-section-hint">click to add, then drag into position</span>
        </div>
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
    </div>
  );
}
