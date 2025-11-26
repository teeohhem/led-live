import React from 'react';

export default function PreviewToggle({ showPreview, setShowPreview, previewOpacity, setPreviewOpacity }) {
  return (
    <div style={{
      position: 'absolute',
      top: '10px',
      right: '10px',
      background: '#2a2a2a',
      padding: '10px',
      borderRadius: '6px',
      border: '2px solid #667eea',
      zIndex: 2000
    }}>
      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <input
          type="checkbox"
          checked={showPreview}
          onChange={(e) => setShowPreview(e.target.checked)}
        />
        <span style={{ fontSize: '0.9rem' }}>🎬 Show Live Preview</span>
      </label>
      
      {showPreview && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.85rem', color: '#aaa' }}>Opacity:</span>
          <input
            type="range"
            min="0"
            max="100"
            value={previewOpacity}
            onChange={(e) => setPreviewOpacity(parseInt(e.target.value))}
            style={{ width: '100px' }}
          />
          <span style={{ fontSize: '0.85rem', color: '#aaa' }}>{previewOpacity}%</span>
        </div>
      )}
    </div>
  );
}

