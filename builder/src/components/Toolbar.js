import React, { useEffect } from 'react';
import './Toolbar.css';

export default function Toolbar({ currentMode, setCurrentMode, templates, generateYAML, displayConfig, elements }) {
  // Update dimension display when config or elements change
  useEffect(() => {
    const dimLabel = document.getElementById('dimensionLabel');
    const countLabel = document.getElementById('elementCountLabel');
    
    if (dimLabel && displayConfig) {
      const { panel_width, panel_height, num_panels, orientation } = displayConfig;
      const totalWidth = orientation === 'horizontal' ? panel_width * num_panels : panel_width;
      const totalHeight = orientation === 'vertical' ? panel_height * num_panels : panel_height;
      dimLabel.textContent = `${totalWidth}×${totalHeight}`;
    }
    
    if (countLabel && elements) {
      countLabel.textContent = `${elements.length} element${elements.length !== 1 ? 's' : ''}`;
    }
  }, [displayConfig, elements]);
  const modes = ['sports', 'stocks', 'weather'];
  
  const getTotalElements = (mode) => {
    let total = 0;
    Object.keys(templates[mode]).forEach(key => {
      if (key !== 'logo_enabled' && templates[mode][key].elements) {
        total += templates[mode][key].elements.length;
      }
    });
    return total;
  };

  const modeIcons = {
    sports: '🏀',
    stocks: '📈',
    weather: '🌤️'
  };

  const modeLabels = {
    sports: 'Sports',
    stocks: 'Stocks',
    weather: 'Weather'
  };

  return (
    <div className="toolbar">
      <div className="mode-tabs">
        {modes.map(mode => {
          const count = getTotalElements(mode);
          const isActive = mode === currentMode;
          
          return (
            <button
              key={mode}
              className={`mode-tab ${isActive ? 'active' : ''}`}
              onClick={() => setCurrentMode(mode)}
            >
              {modeIcons[mode]} {modeLabels[mode]}
              {count > 0 && <span className="badge">{count}</span>}
            </button>
          );
        })}
      </div>

      <div className="toolbar-actions">
        <button onClick={() => window.location.reload()}>🗑️ Clear</button>
        <button onClick={generateYAML}>🔄 Refresh</button>
        <button onClick={() => {/* Copy YAML */}}>📋 Copy</button>
        <button className="save-btn">💾 Save to Config</button>
        <button>⬇️ Download</button>
      </div>

      <div className="toolbar-info">
        <span className="dimension-label" id="dimensionLabel">64×20</span>
        <span className="element-count" id="elementCountLabel">0 elements</span>
      </div>
    </div>
  );
}

