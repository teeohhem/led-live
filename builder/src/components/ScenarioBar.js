import React from 'react';
import './ScenarioBar.css';
import { SCENARIO_DEFINITIONS } from '../utils/elements';

export default function ScenarioBar({
  currentMode,
  currentScenario,
  setCurrentScenario,
  templates,
  displayConfig,
  setItemHeight,
}) {
  const scenarios = SCENARIO_DEFINITIONS[currentMode] || [];
  const isMultiItem = currentScenario !== 'one_item';
  const itemHeight = templates[currentMode][currentScenario]?.item_height || 10;

  const { panel_height, num_panels, orientation } = displayConfig;
  const totalHeight = orientation === 'vertical' ? panel_height * num_panels : panel_height;
  const numItems = { two_items: 2, three_items: 3, four_items: 4 }[currentScenario] || 1;
  const suggestedHeight = Math.floor(totalHeight / numItems);

  return (
    <div className="scenario-bar">
      <span className="scenario-label">Scenario:</span>
      <div className="scenario-buttons">
        {scenarios.map(s => {
          const hasElements = templates[currentMode][s.value]?.elements?.length > 0;
          const isActive = s.value === currentScenario;
          const count = templates[currentMode][s.value]?.elements?.length || 0;

          return (
            <button
              key={s.value}
              className={`scenario-btn ${isActive ? 'active' : ''} ${hasElements ? 'has-elements' : ''}`}
              onClick={() => setCurrentScenario(s.value)}
            >
              {s.icon} {s.label}
              {hasElements && <span className="count-badge">{count}</span>}
            </button>
          );
        })}
      </div>

      {isMultiItem && (
        <div className="item-height-control">
          <span className="item-height-label">Item height (px):</span>
          <input
            type="number"
            className="item-height-input"
            min="4"
            max={totalHeight}
            value={itemHeight}
            onChange={e => {
              const v = parseInt(e.target.value, 10);
              if (!isNaN(v) && v > 0) setItemHeight(v);
            }}
          />
          {itemHeight !== suggestedHeight && (
            <button
              className="item-height-suggest"
              title={`Set to ${suggestedHeight} (canvas height ÷ ${numItems})`}
              onClick={() => setItemHeight(suggestedHeight)}
            >
              → {suggestedHeight}
            </button>
          )}
          <span className="item-height-hint">
            green box = one item template ({totalHeight}px canvas ÷ {numItems} = {suggestedHeight}px each)
          </span>
        </div>
      )}
    </div>
  );
}
