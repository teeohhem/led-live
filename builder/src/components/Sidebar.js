import React, { useState, useEffect } from 'react';
import './Sidebar.css';
import { loadConfigTemplate, listTemplates, loadTemplate } from '../utils/api';

export default function Sidebar({ 
  displayConfig, 
  setDisplayConfig, 
  selectedElement, 
  updateElement,
  loadTemplates,
  scale,
  setScale 
}) {
  const [templateList, setTemplateList] = useState([]);
  
  useEffect(() => {
    // Load template list on mount
    listTemplates()
      .then(data => setTemplateList(data.templates || []))
      .catch(err => console.log('Template list not available:', err.message));
  }, []);

  const handleLoadConfig = async () => {
    try {
      console.log('Manual config load triggered');
      const data = await loadConfigTemplate();
      console.log('Config data received:', data);
      
      if (data.has_templates) {
        console.log('Loading templates...');
        loadTemplates(data.templates);
        
        if (data.display) {
          console.log('Setting display config:', data.display);
          // Merge instead of replace to preserve orientation
          setDisplayConfig(prev => ({
            ...prev,
            ...data.display,
            orientation: data.display.orientation || prev.orientation || 'horizontal'
          }));
        }
        
        alert('✅ Loaded from config.yml!');
      } else {
        alert('⚠️ No templates found in config.yml');
      }
    } catch (err) {
      console.error('Load config error:', err);
      alert('⚠️ Could not load config: ' + err.message);
    }
  };

  const handleLoadTemplateFile = async (e) => {
    const filename = e.target.value;
    if (!filename) return;
    
    try {
      const template = await loadTemplate(filename);
      loadTemplates(template);
      alert(`✅ Loaded ${filename}`);
    } catch (err) {
      alert('❌ Error: ' + err.message);
    }
  };

  return (
    <div className="sidebar">
      <h2>⚙️ Configuration</h2>
      
      <div className="control-group">
        <label>Panel Width (px)</label>
        <input
          type="number"
          value={displayConfig.panel_width}
          onChange={(e) => setDisplayConfig({...displayConfig, panel_width: parseInt(e.target.value)})}
          min="16"
          max="256"
        />
      </div>

      <div className="control-group">
        <label>Panel Height (px)</label>
        <input
          type="number"
          value={displayConfig.panel_height}
          onChange={(e) => setDisplayConfig({...displayConfig, panel_height: parseInt(e.target.value)})}
          min="16"
          max="256"
        />
      </div>

      <div className="control-group">
        <label>Number of Panels</label>
        <input
          type="number"
          value={displayConfig.num_panels}
          onChange={(e) => setDisplayConfig({...displayConfig, num_panels: parseInt(e.target.value)})}
          min="1"
          max="8"
        />
      </div>

      <div className="control-group">
        <label>Orientation</label>
        <select
          value={displayConfig.orientation}
          onChange={(e) => setDisplayConfig({...displayConfig, orientation: e.target.value})}
        >
          <option value="horizontal">Horizontal (Side-by-side)</option>
          <option value="vertical">Vertical (Stacked)</option>
        </select>
      </div>

      <div className="control-group">
        <label>Zoom Level</label>
        <select value={scale} onChange={(e) => setScale(parseInt(e.target.value))}>
          <option value="6">6× (Small)</option>
          <option value="8">8× (Medium)</option>
          <option value="10">10× (Large)</option>
          <option value="12">12× (XL)</option>
          <option value="15">15× (XXL)</option>
        </select>
      </div>

      <hr style={{ borderColor: '#3a3a3a', margin: '20px 0' }} />

      <div className="control-group">
        <label>📄 From config.yml</label>
        <button onClick={handleLoadConfig} className="btn-primary">
          📥 Load My Config
        </button>
      </div>

      <div className="control-group">
        <label>📂 Browse Templates</label>
        <select onChange={handleLoadTemplateFile} defaultValue="">
          <option value="">-- Select Template --</option>
          {templateList.map(t => (
            <option key={t.name} value={t.name}>{t.name}</option>
          ))}
        </select>
      </div>

      <hr style={{ borderColor: '#3a3a3a', margin: '20px 0' }} />

      {selectedElement && (
        <div className="properties">
          <h3>Properties: {selectedElement.type}</h3>
          
          {/* Bounds warning */}
          {(() => {
            const totalWidth = displayConfig.orientation === 'horizontal' 
              ? displayConfig.panel_width * displayConfig.num_panels 
              : displayConfig.panel_width;
            const totalHeight = displayConfig.orientation === 'vertical' 
              ? displayConfig.panel_height * displayConfig.num_panels 
              : displayConfig.panel_height;
            
            const exceedsRight = selectedElement.x + selectedElement.width > totalWidth;
            const exceedsBottom = selectedElement.y + selectedElement.height > totalHeight;
            
            if (exceedsRight || exceedsBottom) {
              return (
                <div style={{
                  padding: '10px',
                  background: '#ff4444',
                  color: 'white',
                  borderRadius: '4px',
                  marginBottom: '10px',
                  fontSize: '0.85rem'
                }}>
                  ⚠️ Element exceeds canvas!<br/>
                  {exceedsRight && `Width: ${selectedElement.x + selectedElement.width} > ${totalWidth}`}<br/>
                  {exceedsBottom && `Height: ${selectedElement.y + selectedElement.height} > ${totalHeight}`}
                </div>
              );
            }
            return null;
          })()}
          
          <div className="nudge-controls">
            <div className="nudge-row">
              <button onClick={() => updateElement(selectedElement.id, { y: selectedElement.y - 1 })}>↑</button>
            </div>
            <div className="nudge-row">
              <button onClick={() => updateElement(selectedElement.id, { x: selectedElement.x - 1 })}>←</button>
              <button onClick={() => updateElement(selectedElement.id, { x: selectedElement.x + 1 })}>→</button>
            </div>
            <div className="nudge-row">
              <button onClick={() => updateElement(selectedElement.id, { y: selectedElement.y + 1 })}>↓</button>
            </div>
          </div>
          
          <div className="prop-row">
            <label>X Position (px)</label>
            <input
              type="number"
              value={selectedElement.x}
              onChange={(e) => updateElement(selectedElement.id, { x: parseInt(e.target.value) })}
            />
          </div>

          <div className="prop-row">
            <label>Y Position (px)</label>
            <input
              type="number"
              value={selectedElement.y}
              onChange={(e) => updateElement(selectedElement.id, { y: parseInt(e.target.value) })}
            />
          </div>

          <div className="prop-row">
            <label>Width (px) - Storage only, box auto-fits content</label>
            <input
              type="number"
              value={selectedElement.width}
              onChange={(e) => updateElement(selectedElement.id, { width: parseInt(e.target.value) })}
            />
            <p style={{ fontSize: '0.75rem', color: '#888', marginTop: '4px' }}>
              Note: Bounding box auto-resizes to fit rendered content
            </p>
          </div>

          <div className="prop-row">
            <label>Height (px) - Storage only, box auto-fits content</label>
            <input
              type="number"
              value={selectedElement.height}
              onChange={(e) => updateElement(selectedElement.id, { height: parseInt(e.target.value) })}
            />
          </div>
        </div>
      )}
    </div>
  );
}

