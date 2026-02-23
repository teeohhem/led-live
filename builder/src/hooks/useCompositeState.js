import { useState, useCallback } from "react";
import { COMPONENT_TYPES } from "../utils/compositeTypes";

/**
 * State management for the composite template builder.
 * Components are full-canvas widgets (clock, weather, sports, stocks)
 * placed at absolute positions on a canvas.
 */
export function useCompositeState() {
  const [templateName, setTemplateName] = useState("my_template");
  const [components, setComponents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  const selectedComponent = components.find((c) => c.id === selectedId) || null;

  const addComponent = useCallback((type, canvasWidth, canvasHeight) => {
    const info = COMPONENT_TYPES[type] || {};
    const newComp = {
      id: Date.now(),
      type,
      x: 0,
      y: 0,
      width: info.defaultWidth || canvasWidth,
      height: info.defaultHeight || Math.round(canvasHeight / 2),
      config: { ...(info.defaultConfig || {}) },
    };
    setComponents((prev) => [...prev, newComp]);
    setSelectedId(newComp.id);
    return newComp;
  }, []);

  const updateComponent = useCallback((id, updates) => {
    setComponents((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...updates } : c))
    );
  }, []);

  const updateComponentConfig = useCallback((id, key, value) => {
    setComponents((prev) =>
      prev.map((c) =>
        c.id === id ? { ...c, config: { ...c.config, [key]: value } } : c
      )
    );
  }, []);

  const deleteComponent = useCallback(
    (id) => {
      setComponents((prev) => prev.filter((c) => c.id !== id));
      if (selectedId === id) setSelectedId(null);
    },
    [selectedId]
  );

  const loadTemplate = useCallback((data) => {
    setTemplateName(data.name || "untitled");
    const loaded = (data.components || []).map((comp, i) => ({
      id: Date.now() + i,
      type: comp.type,
      x: comp.x ?? 0,
      y: comp.y ?? 0,
      width: comp.width ?? 64,
      height: comp.height ?? 20,
      config: {
        ...(COMPONENT_TYPES[comp.type]?.defaultConfig || {}),
        ...(comp.config || {}),
      },
    }));
    setComponents(loaded);
    setSelectedId(null);
  }, []);

  const clearTemplate = useCallback(() => {
    setComponents([]);
    setSelectedId(null);
    setTemplateName("my_template");
  }, []);

  return {
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
  };
}
