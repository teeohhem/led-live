import React, { useEffect, useRef } from 'react';
import './Canvas.css';
import LivePreviewCanvas from './LivePreviewCanvas';
import ItemBoundaryOverlay from './ItemBoundaryOverlay';
import { getOptimalElementSize } from '../utils/contentSize';
import interact from 'interactjs';

export default function Canvas({ 
  elements, 
  displayConfig, 
  selectedElement, 
  setSelectedElement,
  updateElement,
  onContextMenu,
  currentScenario,
  currentMode,
  templates,
  scale = 10
}) {
  const { panel_width, panel_height, num_panels, orientation } = displayConfig;
  
  const totalWidth = orientation === 'horizontal' 
    ? panel_width * num_panels 
    : panel_width;
  const totalHeight = orientation === 'vertical' 
    ? panel_height * num_panels 
    : panel_height;

  const canvasWidth = totalWidth * scale;
  const canvasHeight = totalHeight * scale;
  const canvasRef = useRef(null);
  const updateElementRef = useRef(updateElement);
  
  // Keep ref updated
  useEffect(() => {
    updateElementRef.current = updateElement;
  }, [updateElement]);
  
  // Setup interact.js for dragging elements
  useEffect(() => {
    if (!canvasRef.current) return;
    
    // Make all elements draggable
    interact('.element').unset(); // Clear previous instances
    
    interact('.element').draggable({
      inertia: false,
      listeners: {
        start(event) {
          event.target.classList.add('dragging');
          event.target.setAttribute('data-total-dx', '0');
          event.target.setAttribute('data-total-dy', '0');
        },
        move(event) {
          // Accumulate total movement
          const totalDx = parseFloat(event.target.getAttribute('data-total-dx')) + event.dx;
          const totalDy = parseFloat(event.target.getAttribute('data-total-dy')) + event.dy;
          
          event.target.setAttribute('data-total-dx', totalDx);
          event.target.setAttribute('data-total-dy', totalDy);
          
          // Update visual position during drag
          event.target.style.transform = `translate(${totalDx}px, ${totalDy}px)`;
        },
        end(event) {
          event.target.classList.remove('dragging');
          
          // Get element data
          const elementId = parseInt(event.target.dataset.elementId);
          const elem = elements.find(e => e.id === elementId);
          if (!elem) {
            event.target.style.transform = '';
            return;
          }
          
          // Calculate final pixel movement
          const totalDx = parseFloat(event.target.getAttribute('data-total-dx'));
          const totalDy = parseFloat(event.target.getAttribute('data-total-dy'));
          
          const pixelDx = Math.round(totalDx / scale);
          const pixelDy = Math.round(totalDy / scale);
          
          // Calculate new position with bounds checking
          const newX = Math.max(0, Math.min(totalWidth - 1, elem.x + pixelDx));
          const newY = Math.max(0, Math.min(totalHeight - 1, elem.y + pixelDy));
          
          // Update element position using the ref
          if (newX !== elem.x || newY !== elem.y) {
            updateElementRef.current(elementId, { x: newX, y: newY });
          }
          
          // Reset transform
          event.target.style.transform = '';
        }
      }
    });
    
    return () => {
      interact('.element').unset();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [elements.length, scale, totalWidth, totalHeight]); // Only recreate when needed
  
  console.log('Canvas render:', { 
    totalWidth, 
    totalHeight, 
    canvasWidth, 
    canvasHeight,
    panel_width, 
    panel_height, 
    num_panels, 
    orientation: orientation || 'undefined!',
    elementCount: elements.length,
    calculation: `${orientation} === 'horizontal' ? ${panel_width} * ${num_panels} : ${panel_width}`
  });

  return (
    <div className="canvas-container">
      <div 
        ref={canvasRef}
        className="canvas-preview"
        style={{
          width: `${canvasWidth}px`,
          height: `${canvasHeight}px`,
          position: 'relative'
        }}
      >
        {/* Live preview as background */}
        <LivePreviewCanvas
          templates={templates}
          displayConfig={displayConfig}
          currentMode={currentMode}
          currentScenario={currentScenario}
          scale={scale}
        />
        
        {/* Item boundary overlay for multi-item scenarios */}
        <ItemBoundaryOverlay
          currentScenario={currentScenario}
          itemHeight={templates[currentMode][currentScenario]?.item_height || 10}
          scale={scale}
          totalHeight={totalHeight}
        />
        
        {/* Panel dividers */}
        {num_panels > 1 && Array.from({ length: num_panels - 1 }).map((_, i) => {
          const pos = (i + 1) * (orientation === 'horizontal' ? panel_width : panel_height) * scale;
          
          return (
            <div
              key={`divider-${i}`}
              className={`panel-divider ${orientation}`}
              style={orientation === 'horizontal' 
                ? { left: pos } 
                : { top: pos }
              }
            >
              <div className="divider-label">
                Panel {i} | Panel {i + 1}
              </div>
            </div>
          );
        })}

        {/* Elements */}
        {elements.map(element => {
          // Get optimal size based on actual content
          const optimalSize = getOptimalElementSize(element, currentMode);
          
          // Use optimal size for display (shows actual content bounds)
          const displayWidth = optimalSize.width;
          const displayHeight = optimalSize.height;
          
          // Check if element exceeds canvas bounds
          const exceedsRight = element.x + displayWidth > totalWidth;
          const exceedsBottom = element.y + displayHeight > totalHeight;
          const outOfBounds = exceedsRight || exceedsBottom;
          
          // Constrain to canvas if out of bounds
          const constrainedWidth = Math.min(displayWidth, totalWidth - element.x);
          const constrainedHeight = Math.min(displayHeight, totalHeight - element.y);
          
          return (
            <div
              key={element.id}
              data-element-id={element.id}
              className={`element ${element.type} ${selectedElement?.id === element.id ? 'selected' : ''} ${outOfBounds ? 'out-of-bounds' : ''}`}
              style={{
                left: element.x * scale,
                top: element.y * scale,
                width: constrainedWidth * scale,
                height: constrainedHeight * scale,
                position: 'absolute'
              }}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedElement(element);
              }}
              onContextMenu={(e) => onContextMenu(e, element)}
              title={`${element.type} (${displayWidth}×${displayHeight})${outOfBounds ? ' ⚠️ OUT OF BOUNDS' : ''}`}
            >
              <span style={{ fontSize: '8px', opacity: 0.8 }}>
                {element.type.replace(/_/g, ' ')}
              </span>
              {outOfBounds && <span className="warning-badge">!</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

