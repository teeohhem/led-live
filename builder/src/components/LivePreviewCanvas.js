import React, { useEffect, useRef, useState } from 'react';
import { renderPreview } from '../utils/api';

export default function LivePreviewCanvas({ 
  templates, 
  displayConfig, 
  currentMode, 
  currentScenario,
  scale,
  opacity = 0.8
}) {
  const [previewImage, setPreviewImage] = useState(null);
  const [previewStatus, setPreviewStatus] = useState('idle'); // 'idle' | 'loading' | 'ok' | 'error'
  const canvasRef = useRef(null);

  useEffect(() => {
    const updatePreview = async () => {
      setPreviewStatus('loading');
      try {
        const { panel_width, panel_height, num_panels, orientation } = displayConfig;
        const totalWidth = orientation === 'horizontal' 
          ? panel_width * num_panels 
          : panel_width;
        const totalHeight = orientation === 'vertical' 
          ? panel_height * num_panels 
          : panel_height;

        const templateDict = buildTemplateDict(
          templates[currentMode], 
          currentMode, 
          currentScenario,
          totalWidth, 
          totalHeight
        );

        const blob = await renderPreview(currentMode, templateDict, currentScenario);
        const imageUrl = URL.createObjectURL(blob);
        setPreviewImage(imageUrl);
        setPreviewStatus('ok');
      } catch (err) {
        setPreviewImage(null);
        setPreviewStatus('error');
      }
    };

    updatePreview();
  }, [templates, displayConfig, currentMode, currentScenario]);

  const { panel_width, panel_height, num_panels, orientation } = displayConfig;
  const totalWidth = orientation === 'horizontal' 
    ? panel_width * num_panels 
    : panel_width;
  const totalHeight = orientation === 'vertical' 
    ? panel_height * num_panels 
    : panel_height;

  return (
    <>
      {/* Error banner shown ABOVE the canvas area (not inside it, so it's always visible) */}
      {previewStatus === 'error' && (
        <div style={{
          position: 'absolute',
          top: -26,
          left: 0,
          right: 0,
          background: 'rgba(180, 60, 60, 0.9)',
          color: '#fff',
          fontSize: '11px',
          padding: '3px 8px',
          borderRadius: '4px 4px 0 0',
          zIndex: 20,
          pointerEvents: 'none',
        }}>
          ⚠️ Preview unavailable — restart the builder server (<code>python builder_server.py</code>)
        </div>
      )}

      <div
        ref={canvasRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: `${totalWidth * scale}px`,
          height: `${totalHeight * scale}px`,
          pointerEvents: 'none',
          zIndex: 1,
          opacity: opacity,
          border: '2px solid rgba(74, 222, 128, 0.3)',
        }}
      >
        {previewImage ? (
          <img
            src={previewImage}
            alt="Live Preview"
            style={{
              width: '100%',
              height: '100%',
              imageRendering: 'pixelated'
            }}
          />
        ) : null}
      </div>
    </>
  );
}

function buildTemplateDict(modeData, mode, scenario, width, height) {
  const dict = {
    canvas_width: width,
    canvas_height: height,
    logo_enabled: modeData.logo_enabled || false
  };

  const scenarioData = modeData[scenario];
  
  if (scenarioData && scenarioData.elements && scenarioData.elements.length > 0) {
    if (scenario === 'one_item') {
      dict.one_item = {};
      scenarioData.elements.forEach(elem => {
        const spec = { 
          x: Math.round(elem.x),
          y: Math.round(elem.y)
        };
        
        if (elem.type.includes('logo') || elem.type.includes('icon')) {
          spec.width = Math.round(elem.width);
          spec.height = Math.round(elem.height);
        } else {
          spec.font_size = Math.round(elem.fontSize);
          spec.color = elem.color;
          spec.align = elem.align;
        }
        dict.one_item[elem.type] = spec;
      });
    } else {
      dict[scenario] = {
        item_height: scenarioData.item_height || 10,
        item_template: {}
      };
      
      scenarioData.elements.forEach(elem => {
        const spec = { 
          x: Math.round(elem.x),
          y: Math.round(elem.y)
        };
        
        if (elem.type.includes('logo') || elem.type.includes('icon')) {
          spec.width = Math.round(elem.width);
          spec.height = Math.round(elem.height);
        } else {
          spec.font_size = Math.round(elem.fontSize);
          spec.color = elem.color;
          spec.align = elem.align;
        }
        dict[scenario].item_template[elem.type] = spec;
      });
    }
  }

  return dict;
}

