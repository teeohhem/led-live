import React, { useState, useEffect } from 'react';
import './Sidebar.css';
import { loadConfigTemplate, listTemplates, loadTemplate } from '../utils/api';

export default function Sidebar({ 
  displayConfig, 
  setDisplayConfig, 
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
      
      // Auto-detect display config from template
      const firstMode = ['sports', 'stocks', 'weather'].find(m => template[m]);
      if (firstMode && template[firstMode]) {
        const canvasWidth = template[firstMode].canvas_width;
        const canvasHeight = template[firstMode].canvas_height;
        
        if (canvasWidth && canvasHeight) {
          // Infer panel configuration from canvas dimensions
          let panelWidth, panelHeight, numPanels, orientation;
          
          // Try common patterns
          if (canvasWidth === 128 && canvasHeight === 20) {
            // Dual 64×20 horizontal
            panelWidth = 64; panelHeight = 20; numPanels = 2; orientation = 'horizontal';
          } else if (canvasWidth === 64 && canvasHeight === 40) {
            // Dual 64×20 vertical
            panelWidth = 64; panelHeight = 20; numPanels = 2; orientation = 'vertical';
          } else if (canvasWidth === 64 && canvasHeight === 20) {
            // Single 64×20
            panelWidth = 64; panelHeight = 20; numPanels = 1; orientation = 'horizontal';
          } else if (canvasWidth === 64 && canvasHeight === 32) {
            // Single 64×32
            panelWidth = 64; panelHeight = 32; numPanels = 1; orientation = 'horizontal';
          } else if (canvasWidth === 32 && canvasHeight === 32) {
            // Single 32×32
            panelWidth = 32; panelHeight = 32; numPanels = 1; orientation = 'horizontal';
          } else {
            // Fallback: assume single panel
            panelWidth = canvasWidth; panelHeight = canvasHeight; numPanels = 1; orientation = 'horizontal';
          }
          
          setDisplayConfig({
            panel_width: panelWidth,
            panel_height: panelHeight,
            num_panels: numPanels,
            orientation: orientation
          });
        }
      }
      
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

    </div>
  );
}

