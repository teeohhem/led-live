import React, { useEffect } from 'react';
import './Toolbar.css';
import { generateYAML } from '../utils/template';

export default function Toolbar({ currentMode, setCurrentMode, templates, displayConfig, elements }) {
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

  const handleSaveToConfig = async () => {
    const yaml = generateYAML(templates, displayConfig);
    
    const confirmed = window.confirm(
      '💾 Save Template to config.yml?\n\n' +
      'This will copy the YAML to your clipboard.\n' +
      'You can then paste it into your config.yml file.\n\n' +
      'Hot reload will apply changes automatically!\n\n' +
      'Click OK to copy to clipboard.'
    );
    
    if (!confirmed) return;
    
    try {
      await navigator.clipboard.writeText(yaml);
      alert(
        '✅ Template copied to clipboard!\n\n' +
        'Next steps:\n' +
        '1. Open config.yml\n' +
        '2. Find the layout_templates: section\n' +
        '3. Replace it with clipboard content (Cmd/Ctrl+V)\n' +
        '4. Save config.yml\n' +
        '5. Hot reload applies automatically!'
      );
    } catch (err) {
      alert('❌ Could not copy to clipboard: ' + err.message);
    }
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
        <button className="save-btn" onClick={handleSaveToConfig}>💾 Save to Config</button>
      </div>

      <div className="toolbar-info">
        <span className="dimension-label" id="dimensionLabel">64×20</span>
        <span className="element-count" id="elementCountLabel">0 elements</span>
      </div>
    </div>
  );
}

