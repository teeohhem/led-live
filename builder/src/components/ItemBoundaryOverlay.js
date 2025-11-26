import React from 'react';

/**
 * Shows item boundaries for multi-item scenarios to help users understand
 * that item_template defines ONE item that repeats
 */
export default function ItemBoundaryOverlay({ 
  currentScenario, 
  itemHeight, 
  scale,
  totalHeight 
}) {
  if (currentScenario === 'one_item') return null;

  const numItems = {
    'two_items': 2,
    'three_items': 3,
    'four_items': 4
  }[currentScenario] || 2;

  return (
    <>
      {/* Show only first item boundary for editing */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: '100%',
          height: itemHeight * scale,
          border: '3px dashed #4ade80',
          pointerEvents: 'none',
          zIndex: 2,
          boxShadow: '0 0 15px rgba(74, 222, 128, 0.5)'
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: '5px',
            left: '5px',
            background: 'rgba(74, 222, 128, 0.9)',
            color: '#000',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '11px',
            fontWeight: 'bold'
          }}
        >
          ✏️ Edit ONE Item (repeats {numItems}×)
        </div>
      </div>

      {/* Show where items repeat */}
      {Array.from({ length: numItems - 1 }).map((_, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: 0,
            top: (i + 1) * itemHeight * scale,
            width: '100%',
            height: itemHeight * scale,
            border: '2px dashed rgba(74, 222, 128, 0.3)',
            pointerEvents: 'none',
            zIndex: 1
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: '5px',
              left: '5px',
              background: 'rgba(74, 222, 128, 0.5)',
              color: '#000',
              padding: '3px 6px',
              borderRadius: '3px',
              fontSize: '9px',
              fontWeight: 'bold'
            }}
          >
            Item {i + 2} (auto-repeats from template)
          </div>
        </div>
      ))}
    </>
  );
}

