import React, { useState, useEffect } from "react";
import "./App.css";
import Sidebar from "./components/Sidebar";
import Toolbar from "./components/Toolbar";
import ScenarioBar from "./components/ScenarioBar";
import Canvas from "./components/Canvas";
import ElementPalette from "./components/ElementPalette";
import OutputPanel from "./components/OutputPanel";
import ContextMenu from "./components/ContextMenu";
import { useTemplateState } from "./hooks/useTemplateState";
import { loadConfigTemplate } from "./utils/api";

function App() {
  const {
    templates,
    currentMode,
    currentScenario,
    elements,
    displayConfig,
    setCurrentMode,
    setCurrentScenario,
    addElement,
    updateElement,
    deleteElement,
    duplicateElement,
    optimizeSpace,
    loadTemplates,
    setDisplayConfig,
    generateYAML,
  } = useTemplateState();

  const [contextMenu, setContextMenu] = useState({ show: false, x: 0, y: 0 });
  const [selectedElement, setSelectedElement] = useState(null);
  const [scale, setScale] = useState(10);

  // Auto-load config on mount
  useEffect(() => {
    const autoLoad = async () => {
      try {
        console.log("Auto-loading config template...");
        const data = await loadConfigTemplate();
        console.log("Config template response:", data);

        if (data.has_templates) {
          // Load display config FIRST, then templates
          if (data.display) {
            console.log("Setting display config:", data.display);
            // MERGE with existing config instead of replacing
            setDisplayConfig((prev) => ({
              ...prev,
              ...data.display,
              // Ensure orientation is set
              orientation:
                data.display.orientation || prev.orientation || "horizontal",
            }));
            // Wait for state to update
            await new Promise((resolve) => setTimeout(resolve, 100));
          }

          console.log("Loading templates...");
          loadTemplates(data.templates);
          console.log("✅ Config template loaded successfully");
        } else {
          console.log("No templates in config");
        }
      } catch (err) {
        console.log(
          "Auto-load failed (emulator not running or config empty):",
          err.message
        );
      }
    };

    setTimeout(autoLoad, 500);
  }, [loadTemplates, setDisplayConfig]); // Added dependencies

  const handleContextMenu = (e, element) => {
    e.preventDefault();
    setSelectedElement(element);
    setContextMenu({ show: true, x: e.clientX, y: e.clientY });
  };

  const hideContextMenu = () => {
    setContextMenu({ show: false, x: 0, y: 0 });
  };

  return (
    <div className="app" onClick={hideContextMenu}>
      <Toolbar
        currentMode={currentMode}
        setCurrentMode={setCurrentMode}
        templates={templates}
        generateYAML={generateYAML}
        displayConfig={displayConfig}
        elements={elements}
      />

      <ScenarioBar
        currentMode={currentMode}
        currentScenario={currentScenario}
        setCurrentScenario={setCurrentScenario}
        templates={templates}
        displayConfig={displayConfig}
      />

      <div className="main-content">
        <Sidebar
          displayConfig={displayConfig}
          setDisplayConfig={setDisplayConfig}
          selectedElement={selectedElement}
          updateElement={updateElement}
          loadTemplates={loadTemplates}
          scale={scale}
          setScale={setScale}
        />

        <div className="canvas-area">
          <Canvas
            elements={elements}
            displayConfig={displayConfig}
            selectedElement={selectedElement}
            setSelectedElement={setSelectedElement}
            updateElement={updateElement}
            onContextMenu={handleContextMenu}
            currentScenario={currentScenario}
            currentMode={currentMode}
            templates={templates}
            scale={scale}
          />

          <ElementPalette currentMode={currentMode} addElement={addElement} />

          <OutputPanel
            templates={templates}
            displayConfig={displayConfig}
            currentMode={currentMode}
            currentScenario={currentScenario}
          />
        </div>
      </div>

      {contextMenu.show && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          onDuplicate={() => {
            duplicateElement(selectedElement);
            hideContextMenu();
          }}
          onDelete={() => {
            deleteElement(selectedElement);
            hideContextMenu();
          }}
          onOptimize={() => {
            optimizeSpace();
            hideContextMenu();
          }}
        />
      )}
    </div>
  );
}

export default App;
