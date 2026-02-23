import React from 'react';

const ITEM_LABELS = {
  weather: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  sports:  ['Game 1', 'Game 2', 'Game 3', 'Game 4'],
  stocks:  ['AAPL', 'MSFT', 'GOOG', 'AMZN'],
};

/**
 * Shows item boundaries for multi-item scenarios.
 *
 * - Zone 0: bright green border, fully editable
 * - Zones 1-N: dimmed ghost copies of zone-0 elements + repeat label
 * - Capacity badge: shows if items perfectly fill, overflow, or leave gaps
 */
export default function ItemBoundaryOverlay({
  currentScenario,
  currentMode,
  itemHeight,
  scale,
  totalHeight,
  elements,
}) {
  if (currentScenario === 'one_item') return null;

  const numItems = { two_items: 2, three_items: 3, four_items: 4 }[currentScenario] || 2;
  const labels = ITEM_LABELS[currentMode] || Array.from({ length: numItems }, (_, i) => `Item ${i + 1}`);

  const usedHeight  = itemHeight * numItems;
  const leftover    = totalHeight - usedHeight;
  const capacityFit = Math.floor(totalHeight / itemHeight);

  let capacityMsg, capacityColor;
  if (leftover === 0) {
    capacityMsg   = `✅ ${numItems} items fill canvas exactly`;
    capacityColor = '#4ade80';
  } else if (leftover > 0) {
    capacityMsg   = `⚠️ ${numItems} items leave ${leftover}px unused  (canvas fits ${capacityFit})`;
    capacityColor = '#facc15';
  } else {
    capacityMsg   = `❌ ${numItems} items overflow by ${-leftover}px — reduce item height`;
    capacityColor = '#f87171';
  }

  return (
    <>
      {/* ── Zone 0: editable template ── */}
      <div
        style={{
          position: 'absolute',
          left: 0, top: 0,
          width: '100%',
          height: itemHeight * scale,
          border: '3px dashed #4ade80',
          pointerEvents: 'none',
          zIndex: 3,
          boxShadow: '0 0 15px rgba(74,222,128,0.45)',
        }}
      >
        <div style={{
          position: 'absolute',
          top: 4, left: 4,
          background: 'rgba(74,222,128,0.92)',
          color: '#000',
          padding: '3px 7px',
          borderRadius: 4,
          fontSize: 10,
          fontWeight: 'bold',
        }}>
          ✏️ Template row — e.g. {labels[0]}
        </div>
      </div>

      {/* ── Zones 1-N: ghost copies ── */}
      {Array.from({ length: numItems - 1 }).map((_, i) => {
        const yOff = (i + 1) * itemHeight * scale;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 0, top: yOff,
              width: '100%',
              height: itemHeight * scale,
              border: '2px dashed rgba(74,222,128,0.25)',
              pointerEvents: 'none',
              zIndex: 2,
            }}
          >
            {/* Ghost element copies */}
            {elements.map(elem => (
              <div
                key={elem.id}
                style={{
                  position: 'absolute',
                  left:   elem.x * scale,
                  top:    elem.y * scale,
                  width:  elem.width  * scale,
                  height: elem.height * scale,
                  border: '1px solid rgba(74,222,128,0.35)',
                  background: 'rgba(74,222,128,0.06)',
                  borderRadius: 2,
                  overflow: 'hidden',
                  pointerEvents: 'none',
                }}
              >
                <span style={{
                  fontSize: 7,
                  color: 'rgba(74,222,128,0.55)',
                  padding: '1px 2px',
                  display: 'block',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                }}>
                  {elem.type.replace(/_/g, ' ')}
                </span>
              </div>
            ))}

            {/* Repeat label */}
            <div style={{
              position: 'absolute',
              top: 4, right: 6,
              background: 'rgba(74,222,128,0.45)',
              color: '#000',
              padding: '2px 6px',
              borderRadius: 3,
              fontSize: 9,
              fontWeight: 'bold',
            }}>
              {labels[i + 1] || `Item ${i + 2}`}
            </div>
          </div>
        );
      })}

      {/* ── Capacity indicator ── */}
      <div style={{
        position: 'absolute',
        bottom: -28,
        left: 0,
        right: 0,
        textAlign: 'center',
        fontSize: 11,
        color: capacityColor,
        background: 'rgba(0,0,0,0.75)',
        padding: '3px 0',
        borderRadius: '0 0 4px 4px',
        pointerEvents: 'none',
        zIndex: 10,
      }}>
        {capacityMsg}
      </div>
    </>
  );
}

