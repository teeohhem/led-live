import React from 'react';
import './ScenarioBar.css';
import { SCENARIO_DEFINITIONS } from '../utils/elements';

export default function ScenarioBar({ currentMode, currentScenario, setCurrentScenario, templates }) {
  const scenarios = SCENARIO_DEFINITIONS[currentMode] || [];

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
    </div>
  );
}

