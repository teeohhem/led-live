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
        const data = await loadConfigTemplate();

        if (data.has_templates) {
          // Load display config FIRST, then templates
          if (data.display) {
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

          loadTemplates(data.templates);
        }
      } catch (err) {
        // Silent fail if emulator not running
      }
    };

    setTimeout(autoLoad, 500);
  }, [loadTemplates, setDisplayConfig]);

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
          loadTemplates={loadTemplates}
          scale={scale}
          setScale={setScale}
        />

        <div className="canvas-area">
          <div className="canvas-and-properties">
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

            <div className="properties-panel">
              <h3>Properties</h3>
              {selectedElement ? (
                <>
                  <p className="element-label">
                    {selectedElement.type.replace(/_/g, " ")}
                  </p>

                  <div className="nudge-controls">
                    <button
                      onClick={() =>
                        updateElement(selectedElement.id, {
                          y: selectedElement.y - 1,
                        })
                      }
                    >
                      ↑
                    </button>
                    <div className="nudge-row">
                      <button
                        onClick={() =>
                          updateElement(selectedElement.id, {
                            x: selectedElement.x - 1,
                          })
                        }
                      >
                        ←
                      </button>
                      <button
                        onClick={() =>
                          updateElement(selectedElement.id, {
                            x: selectedElement.x + 1,
                          })
                        }
                      >
                        →
                      </button>
                    </div>
                    <button
                      onClick={() =>
                        updateElement(selectedElement.id, {
                          y: selectedElement.y + 1,
                        })
                      }
                    >
                      ↓
                    </button>
                  </div>

                  <div className="prop-row">
                    <label>X</label>
                    <input
                      type="number"
                      value={selectedElement.x}
                      onChange={(e) =>
                        updateElement(selectedElement.id, {
                          x: parseInt(e.target.value),
                        })
                      }
                    />
                  </div>

                  <div className="prop-row">
                    <label>Y</label>
                    <input
                      type="number"
                      value={selectedElement.y}
                      onChange={(e) =>
                        updateElement(selectedElement.id, {
                          y: parseInt(e.target.value),
                        })
                      }
                    />
                  </div>

                  <div className="prop-row">
                    <label>Font Size</label>
                    <input
                      type="number"
                      value={selectedElement.fontSize}
                      onChange={(e) =>
                        updateElement(selectedElement.id, {
                          fontSize: parseInt(e.target.value),
                        })
                      }
                    />
                  </div>

                  <button
                    className="delete-btn"
                    onClick={() => {
                      deleteElement(selectedElement);
                      setSelectedElement(null);
                    }}
                  >
                    🗑️ Delete
                  </button>
                </>
              ) : (
                <p className="no-selection">Click an element to edit</p>
              )}
            </div>
          </div>

          <ElementPalette currentMode={currentMode} addElement={addElement} />
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
