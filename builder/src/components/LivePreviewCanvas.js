import React, { useEffect, useRef, useState } from 'react';
import { renderPreview } from '../utils/api';
import { generateJSON } from '../utils/template';

export default function LivePreviewCanvas({ 
  templates, 
  displayConfig, 
  currentMode, 
  currentScenario,
  scale 
}) {
  const [previewImage, setPreviewImage] = useState(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    const updatePreview = async () => {
      try {
        // Build template dict for current mode
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

        console.log('Rendering preview for:', currentMode, currentScenario);
        console.log('Template dict:', templateDict);
        console.log('Elements in scenario:', templates[currentMode][currentScenario]?.elements?.length);

        // Render preview using actual renderer
        console.log('Calling renderPreview API...');
        const blob = await renderPreview(currentMode, templateDict, currentScenario);
        console.log('Got blob:', blob.size, 'bytes');
        const imageUrl = URL.createObjectURL(blob);
        console.log('Created image URL:', imageUrl);
        setPreviewImage(imageUrl);
        console.log('✅ Preview image set, should display now');
      } catch (err) {
        console.error('❌ Preview failed:', err);
        console.error('Error message:', err.message);
        setPreviewImage(null);
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
        opacity: 0.8
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
          onLoad={() => console.log('✅ Preview image loaded and displayed')}
          onError={(e) => console.error('❌ Preview image failed to load:', e)}
        />
      ) : (
        <div style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#666',
          fontSize: '12px'
        }}>
          {/* No preview message - will be hidden by low opacity */}
        </div>
      )}
    </div>
  );
}

function buildTemplateDict(modeData, mode, scenario, width, height) {
  const dict = {
    canvas_width: width,
    canvas_height: height,
    logo_enabled: modeData.logo_enabled || false
  };

  const scenarioData = modeData[scenario];
  console.log(`Building template dict for ${mode}.${scenario}:`, scenarioData);
  
  if (scenarioData && scenarioData.elements && scenarioData.elements.length > 0) {
    console.log(`  ${scenarioData.elements.length} elements found`);
    
    if (scenario === 'one_item') {
      dict.one_item = {};
      scenarioData.elements.forEach(elem => {
        console.log(`    Adding ${elem.type} at (${elem.x}, ${elem.y})`);
        const spec = { 
          x: Math.round(elem.x), // Ensure integer
          y: Math.round(elem.y)  // Ensure integer
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
      console.log('  Built one_item dict:', dict.one_item);
    } else {
      dict[scenario] = {
        item_height: scenarioData.item_height || 10,
        item_template: {}
      };
      
      scenarioData.elements.forEach(elem => {
        console.log(`    Adding ${elem.type} at (${elem.x}, ${elem.y})`);
        const spec = { 
          x: Math.round(elem.x), // Ensure integer
          y: Math.round(elem.y)  // Ensure integer
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
      console.log(`  Built ${scenario} dict:`, dict[scenario]);
    }
  } else {
    console.log('  No elements to render');
  }

  return dict;
}

