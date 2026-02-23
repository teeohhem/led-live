import React, { useEffect, useRef, useState } from "react";
import interact from "interactjs";
import "./CompositeBuilder.css";
import { useCompositeState } from "../hooks/useCompositeState";
import { COMPONENT_TYPES } from "../utils/compositeTypes";
import { generateCompositeYAML } from "../utils/compositeTemplate";
import {
  listCompositeTemplates,
  loadCompositeTemplate,
  saveCompositeTemplate,
  previewCompositeTemplate,
} from "../utils/api";

// ---------------------------------------------------------------------------
// Draggable + resizable block for a single composite component
// ---------------------------------------------------------------------------

function ComponentBlock({ comp, scale, isSelected, onSelect, onUpdate, onDoubleClick }) {
  const ref = useRef(null);
  const updateRef = useRef(onUpdate);
  const scaleRef = useRef(scale);

  useEffect(() => {
    updateRef.current = onUpdate;
  }, [onUpdate]);

  useEffect(() => {
    scaleRef.current = scale;
  }, [scale]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const interactable = interact(el)
      .draggable({
        listeners: {
          start(event) {
            event.target.setAttribute("data-drag-dx", "0");
            event.target.setAttribute("data-drag-dy", "0");
            event.target.classList.add("dragging");
          },
          move(event) {
            const dx =
              parseFloat(event.target.getAttribute("data-drag-dx")) + event.dx;
            const dy =
              parseFloat(event.target.getAttribute("data-drag-dy")) + event.dy;
            event.target.setAttribute("data-drag-dx", dx);
            event.target.setAttribute("data-drag-dy", dy);
            event.target.style.transform = `translate(${dx}px, ${dy}px)`;
          },
          end(event) {
            event.target.classList.remove("dragging");
            const dx = parseFloat(event.target.getAttribute("data-drag-dx"));
            const dy = parseFloat(event.target.getAttribute("data-drag-dy"));
            event.target.style.transform = "";

            const s = scaleRef.current;
            const current = event.target._compData || { x: 0, y: 0 };
            updateRef.current(event.target.dataset.compId, {
              x: Math.max(0, current.x + Math.round(dx / s)),
              y: Math.max(0, current.y + Math.round(dy / s)),
            });
          },
        },
      })
      .resizable({
        edges: { right: true, bottom: true },
        listeners: {
          move(event) {
            const s = scaleRef.current;
            updateRef.current(event.target.dataset.compId, {
              width: Math.max(8, Math.round(event.rect.width / s)),
              height: Math.max(4, Math.round(event.rect.height / s)),
            });
          },
        },
      });

    return () => interactable.unset();
  }, [comp.id]);

  // Store current position on the DOM element so drag-end can read it without
  // capturing a stale closure.
  useEffect(() => {
    if (ref.current) {
      ref.current._compData = { x: comp.x, y: comp.y };
    }
  });

  const info = COMPONENT_TYPES[comp.type] || {};

  return (
    <div
      ref={ref}
      data-comp-id={String(comp.id)}
      className={`comp-block${isSelected ? " selected" : ""}`}
      style={{
        left: comp.x * scale,
        top: comp.y * scale,
        width: comp.width * scale,
        height: comp.height * scale,
        "--block-color": info.color || "#667eea",
      }}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(comp.id);
      }}
      onDoubleClick={(e) => {
        e.stopPropagation();
        onDoubleClick(comp.type);
      }}
    >
      <span className="comp-block-icon">{info.icon}</span>
      <span className="comp-block-label">{info.label}</span>
      <span className="comp-block-size">
        {comp.width}×{comp.height}
      </span>
      <span className="comp-block-hint">double-click to edit layout</span>
      <div className="resize-handle" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main composite builder view
// ---------------------------------------------------------------------------

export default function CompositeBuilder({ displayConfig, onEditComponent }) {
  const {
    templateName,
    setTemplateName,
    components,
    selectedId,
    setSelectedId,
    selectedComponent,
    addComponent,
    updateComponent,
    updateComponentConfig,
    deleteComponent,
    loadTemplate,
    clearTemplate,
  } = useCompositeState();

  const [scale, setScale] = useState(8);
  const [savedTemplates, setSavedTemplates] = useState([]);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const { panel_width, panel_height, num_panels, orientation } = displayConfig;
  const canvasWidth =
    orientation === "horizontal" ? panel_width * num_panels : panel_width;
  const canvasHeight =
    orientation === "vertical" ? panel_height * num_panels : panel_height;

  const yamlOutput = generateCompositeYAML(
    templateName,
    canvasWidth,
    canvasHeight,
    components
  );

  // Load saved template list on mount
  useEffect(() => {
    listCompositeTemplates()
      .then((data) => setSavedTemplates(data.templates || []))
      .catch(() => {});
  }, []);

  const showStatus = (msg, isError = false) => {
    setStatus({ msg, isError });
    setTimeout(() => setStatus(null), 3000);
  };

  const handleAdd = (type) => {
    addComponent(type, canvasWidth, canvasHeight);
  };

  const handleLoad = async (filename) => {
    if (!filename) return;
    try {
      const data = await loadCompositeTemplate(filename);
      loadTemplate(data);
      showStatus(`Loaded ${filename}`);
    } catch (err) {
      showStatus("Load failed: " + err.message, true);
    }
  };

  const handleNew = () => {
    if (
      components.length > 0 &&
      !window.confirm("Discard current template and start fresh?")
    )
      return;
    clearTemplate();
    setPreviewUrl(null);
  };

  const handleSave = async () => {
    try {
      const filename = templateName.replace(/[^a-z0-9_-]/gi, "_") + ".yml";
      await saveCompositeTemplate(filename, yamlOutput);
      const data = await listCompositeTemplates();
      setSavedTemplates(data.templates || []);
      showStatus(`Saved ${filename}`);
    } catch (err) {
      showStatus("Save failed: " + err.message, true);
    }
  };

  const handlePreview = async () => {
    if (components.length === 0) {
      showStatus("Add at least one component first", true);
      return;
    }
    setPreviewLoading(true);
    try {
      const blob = await previewCompositeTemplate({
        name: templateName,
        canvas_width: canvasWidth,
        canvas_height: canvasHeight,
        background_color: [0, 0, 0],
        components: components.map((c) => ({
          type: c.type,
          x: c.x,
          y: c.y,
          width: c.width,
          height: c.height,
          config: c.config,
        })),
      });
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(URL.createObjectURL(blob));
    } catch (err) {
      showStatus("Preview failed: " + err.message, true);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleCopyYAML = async () => {
    try {
      await navigator.clipboard.writeText(yamlOutput);
      showStatus("YAML copied to clipboard!");
    } catch (err) {
      showStatus("Copy failed: " + err.message, true);
    }
  };

  // Numeric field update helper
  const numericUpdate = (id, field, rawValue) => {
    const v = parseInt(rawValue, 10);
    if (!isNaN(v)) updateComponent(id, { [field]: v });
  };

  return (
    <div className="cb-root" onClick={() => setSelectedId(null)}>
      {/* ---- Header bar ---- */}
      <div className="cb-header" onClick={(e) => e.stopPropagation()}>
        <input
          className="cb-name-input"
          type="text"
          value={templateName}
          onChange={(e) => setTemplateName(e.target.value)}
          placeholder="template name"
        />
        <span className="cb-canvas-size">
          {canvasWidth}×{canvasHeight}
        </span>

        <select
          className="cb-load-select"
          value=""
          onChange={(e) => handleLoad(e.target.value)}
        >
          <option value="">Load template…</option>
          {savedTemplates.map((t) => (
            <option key={t.name} value={t.name}>
              {t.name}
            </option>
          ))}
        </select>

        <button className="cb-btn" onClick={handleNew}>
          ✨ New
        </button>
        <button className="cb-btn cb-btn-save" onClick={handleSave}>
          💾 Save
        </button>
        <button
          className="cb-btn cb-btn-preview"
          onClick={handlePreview}
          disabled={previewLoading}
        >
          {previewLoading ? "⏳ Rendering…" : "🖥️ Preview"}
        </button>
        <button className="cb-btn" onClick={handleCopyYAML}>
          📋 Copy YAML
        </button>

        <div className="cb-scale-row">
          <label>Zoom</label>
          <input
            type="range"
            min="4"
            max="16"
            step="1"
            value={scale}
            onChange={(e) => setScale(parseInt(e.target.value, 10))}
          />
          <span>{scale}×</span>
        </div>

        {status && (
          <span className={`cb-status${status.isError ? " error" : ""}`}>
            {status.msg}
          </span>
        )}
      </div>

      {/* ---- Component palette ---- */}
      <div className="cb-palette" onClick={(e) => e.stopPropagation()}>
        <span className="cb-palette-label">Add component:</span>
        {Object.entries(COMPONENT_TYPES).map(([type, info]) => (
          <button
            key={type}
            className="cb-palette-btn"
            style={{ "--accent": info.color }}
            onClick={() => handleAdd(type)}
          >
            {info.icon} {info.label}
          </button>
        ))}
      </div>

      {/* ---- Main workspace ---- */}
      <div className="cb-workspace">
        {/* Canvas + optional preview overlay */}
        <div className="cb-canvas-wrap">
          {previewUrl && (
            <div className="cb-preview-overlay" onClick={(e) => e.stopPropagation()}>
              <img
                src={previewUrl}
                alt="Rendered preview"
                style={{
                  width: canvasWidth * scale,
                  height: canvasHeight * scale,
                  imageRendering: "pixelated",
                  display: "block",
                }}
              />
              <button
                className="cb-btn cb-close-preview"
                onClick={() => setPreviewUrl(null)}
              >
                ✕ Close Preview
              </button>
            </div>
          )}

          {!previewUrl && (
            <div
              className="cb-canvas"
              style={{
                width: canvasWidth * scale,
                height: canvasHeight * scale,
              }}
            >
              {/* Panel dividers */}
              {num_panels > 1 &&
                Array.from({ length: num_panels - 1 }, (_, i) => {
                  if (orientation === "vertical") {
                    const y = (i + 1) * panel_height * scale;
                    return (
                      <div
                        key={i}
                        className="cb-divider cb-divider-h"
                        style={{ top: y }}
                      />
                    );
                  } else {
                    const x = (i + 1) * panel_width * scale;
                    return (
                      <div
                        key={i}
                        className="cb-divider cb-divider-v"
                        style={{ left: x }}
                      />
                    );
                  }
                })}

              {/* Component blocks */}
              {components.map((comp) => (
                <ComponentBlock
                  key={comp.id}
                  comp={comp}
                  scale={scale}
                  isSelected={comp.id === selectedId}
                  onSelect={setSelectedId}
                  onUpdate={updateComponent}
                  onDoubleClick={onEditComponent || (() => {})}
                />
              ))}

              {components.length === 0 && (
                <div className="cb-canvas-empty">
                  Click a component above to add it to the canvas
                </div>
              )}
            </div>
          )}
        </div>

        {/* ---- Properties panel ---- */}
        <div
          className="cb-properties"
          onClick={(e) => e.stopPropagation()}
        >
          <h3>Properties</h3>
          {selectedComponent ? (
            <>
              <div
                className="cb-comp-badge"
                style={{
                  "--accent":
                    COMPONENT_TYPES[selectedComponent.type]?.color || "#667eea",
                }}
              >
                {COMPONENT_TYPES[selectedComponent.type]?.icon}{" "}
                {COMPONENT_TYPES[selectedComponent.type]?.label}
              </div>

              <div className="cb-prop-section">
                <div className="cb-prop-row">
                  <label>X</label>
                  <input
                    type="number"
                    value={selectedComponent.x}
                    onChange={(e) =>
                      numericUpdate(selectedComponent.id, "x", e.target.value)
                    }
                  />
                </div>
                <div className="cb-prop-row">
                  <label>Y</label>
                  <input
                    type="number"
                    value={selectedComponent.y}
                    onChange={(e) =>
                      numericUpdate(selectedComponent.id, "y", e.target.value)
                    }
                  />
                </div>
                <div className="cb-prop-row">
                  <label>Width</label>
                  <input
                    type="number"
                    value={selectedComponent.width}
                    onChange={(e) =>
                      numericUpdate(
                        selectedComponent.id,
                        "width",
                        e.target.value
                      )
                    }
                  />
                </div>
                <div className="cb-prop-row">
                  <label>Height</label>
                  <input
                    type="number"
                    value={selectedComponent.height}
                    onChange={(e) =>
                      numericUpdate(
                        selectedComponent.id,
                        "height",
                        e.target.value
                      )
                    }
                  />
                </div>
              </div>

              {(
                COMPONENT_TYPES[selectedComponent.type]?.configSchema || []
              ).length > 0 && (
                <div className="cb-prop-section">
                  <div className="cb-prop-section-title">Config</div>
                  {COMPONENT_TYPES[selectedComponent.type].configSchema.map(
                    (field) => (
                      <div key={field.key} className="cb-prop-row">
                        <label>{field.label}</label>
                        {field.type === "select" ? (
                          <select
                            value={
                              selectedComponent.config[field.key] ?? ""
                            }
                            onChange={(e) =>
                              updateComponentConfig(
                                selectedComponent.id,
                                field.key,
                                e.target.value || undefined
                              )
                            }
                          >
                            {field.options.map((opt) => (
                              <option key={opt} value={opt}>
                                {opt || "(default)"}
                              </option>
                            ))}
                          </select>
                        ) : field.type === "checkbox" ? (
                          <label className="cb-checkbox-label">
                            <input
                              type="checkbox"
                              checked={
                                !!selectedComponent.config[field.key]
                              }
                              onChange={(e) =>
                                updateComponentConfig(
                                  selectedComponent.id,
                                  field.key,
                                  e.target.checked
                                )
                              }
                            />
                            <span>enabled</span>
                          </label>
                        ) : (
                          <input
                            type="number"
                            min={field.min}
                            max={field.max}
                            value={
                              selectedComponent.config[field.key] ?? ""
                            }
                            onChange={(e) =>
                              updateComponentConfig(
                                selectedComponent.id,
                                field.key,
                                parseInt(e.target.value, 10)
                              )
                            }
                          />
                        )}
                      </div>
                    )
                  )}
                </div>
              )}

              <button
                className="cb-delete-btn"
                onClick={() => deleteComponent(selectedComponent.id)}
              >
                🗑️ Remove component
              </button>
            </>
          ) : (
            <p className="cb-no-selection">Click a component to edit</p>
          )}
        </div>
      </div>

      {/* ---- YAML output ---- */}
      <div className="cb-yaml-panel" onClick={(e) => e.stopPropagation()}>
        <div className="cb-yaml-header">
          <span>YAML — paste into templates/ to use this layout</span>
          <button className="cb-btn-sm" onClick={handleCopyYAML}>
            📋 Copy
          </button>
        </div>
        <pre className="cb-yaml-pre">{yamlOutput}</pre>
      </div>
    </div>
  );
}
