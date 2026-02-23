import React from 'react';
import './PreviewToggle.css';

export default function PreviewToggle({ showPreview, setShowPreview, previewOpacity, setPreviewOpacity }) {
  return (
    <div className="preview-toggle-bar">
      <label className="preview-toggle-check">
        <input
          type="checkbox"
          checked={showPreview}
          onChange={(e) => setShowPreview(e.target.checked)}
        />
        <span>🎬 Live preview</span>
      </label>

      {showPreview && (
        <>
          <span className="preview-toggle-sep">|</span>
          <span className="preview-toggle-label">Opacity</span>
          <input
            type="range"
            className="preview-toggle-slider"
            min="0"
            max="100"
            value={previewOpacity}
            onChange={(e) => setPreviewOpacity(parseInt(e.target.value))}
          />
          <span className="preview-toggle-pct">{previewOpacity}%</span>

          <div className="preview-toggle-presets">
            {[0, 20, 50, 80].map(v => (
              <button
                key={v}
                className={`preset-btn${previewOpacity === v ? ' active' : ''}`}
                onClick={() => setPreviewOpacity(v)}
              >
                {v}%
              </button>
            ))}
          </div>
        </>
      )}

      <span className="preview-toggle-hint">
        {showPreview
          ? 'Preview shows actual rendered output behind your elements'
          : 'Turn on preview to see rendered output behind your elements'}
      </span>
    </div>
  );
}
