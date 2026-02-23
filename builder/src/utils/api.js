/**
 * API utilities for communicating with emulator
 */

export async function loadConfigTemplate() {
  const response = await fetch("/api/config_template");
  if (!response.ok) throw new Error("Failed to load config template");
  return response.json();
}

export async function saveTemplate(filename, template) {
  const response = await fetch("/templates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename, template }),
  });
  return response.json();
}

export async function listTemplates() {
  const response = await fetch("/templates");
  return response.json();
}

export async function loadTemplate(filename) {
  const response = await fetch(`/templates/${filename}`);
  return response.json();
}

export async function renderPreview(mode, template, scenario) {
  const response = await fetch("/api/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, template, scenario }),
  });

  if (!response.ok) {
    // Try to get error details
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      const error = await response.json();
      console.error("Server error:", error);
      throw new Error(
        error.error || error.traceback || "Preview render failed"
      );
    } else {
      const text = await response.text();
      console.error("Server response:", text);
      throw new Error(`Preview render failed: ${response.status}`);
    }
  }

  return response.blob();
}

export async function getSportsData() {
  try {
    const response = await fetch("/api/sports");
    return response.json();
  } catch {
    return { games: [] };
  }
}

export async function getStocksData() {
  try {
    const response = await fetch("/api/stocks");
    return response.json();
  } catch {
    return { quotes: [] };
  }
}

export async function getWeatherData() {
  try {
    const response = await fetch("/api/weather");
    return response.json();
  } catch {
    return { weather: {} };
  }
}

export async function listCompositeTemplates() {
  try {
    const response = await fetch("/api/composite_templates");
    return response.json();
  } catch {
    return { templates: [] };
  }
}

export async function loadCompositeTemplate(filename) {
  const response = await fetch(`/api/composite_templates/${filename}`);
  if (!response.ok) throw new Error(`Failed to load ${filename}`);
  return response.json();
}

export async function saveCompositeTemplate(filename, content) {
  const response = await fetch("/api/composite_templates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename, content }),
  });
  if (!response.ok) throw new Error("Failed to save template");
  return response.json();
}

export async function previewCompositeTemplate(template) {
  const response = await fetch("/api/composite_preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template }),
  });
  if (!response.ok) {
    const ct = response.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const err = await response.json();
      throw new Error(err.error || "Preview failed");
    }
    throw new Error(`Preview failed: ${response.status}`);
  }
  return response.blob();
}
