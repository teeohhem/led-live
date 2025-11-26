import React, { useState } from "react";
import "./OutputPanel.css";
import { generateYAML, generateJSON } from "../utils/template";

export default function OutputPanel({
  templates,
  displayConfig,
  currentMode,
  currentScenario,
}) {
  const [activeTab, setActiveTab] = useState("yaml");

  const copyYAML = () => {
    const yaml = generateYAML(templates, displayConfig);
    navigator.clipboard
      .writeText(yaml)
      .then(() => alert("✅ YAML copied to clipboard!"))
      .catch((err) => alert("❌ Could not copy: " + err.message));
  };

  return (
    <div className="output-panel">
      <div className="tabs">
        <button
          className={activeTab === "yaml" ? "active" : ""}
          onClick={() => setActiveTab("yaml")}
        >
          YAML (config.yml)
        </button>
        <button
          className={activeTab === "json" ? "active" : ""}
          onClick={() => setActiveTab("json")}
        >
          JSON
        </button>

        {activeTab === "yaml" && (
          <button onClick={copyYAML} className="copy-btn">
            📋 Copy
          </button>
        )}
      </div>

      <div className="tab-content">
        {activeTab === "yaml" && (
          <pre className="code-output">
            {generateYAML(templates, displayConfig)}
          </pre>
        )}
        {activeTab === "json" && (
          <pre className="code-output">
            {generateJSON(templates, displayConfig)}
          </pre>
        )}
      </div>
    </div>
  );
}
