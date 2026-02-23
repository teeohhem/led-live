/**
 * Composite template YAML generator.
 * Produces the templates/*.yml format consumed by CompositeRenderer.
 */

function formatConfigValue(value) {
  if (typeof value === "string") return `"${value}"`;
  if (typeof value === "boolean") return value ? "true" : "false";
  return String(value);
}

export function generateCompositeYAML(name, canvasWidth, canvasHeight, components) {
  if (!components.length) {
    return `name: "${name}"\ncanvas_width: ${canvasWidth}\ncanvas_height: ${canvasHeight}\nbackground_color: [0, 0, 0]\n\ncomponents: []\n`;
  }

  let yaml = `name: "${name}"\n`;
  yaml += `canvas_width: ${canvasWidth}\n`;
  yaml += `canvas_height: ${canvasHeight}\n`;
  yaml += `background_color: [0, 0, 0]\n\n`;
  yaml += `components:\n`;

  components.forEach((comp) => {
    yaml += `  - type: "${comp.type}"\n`;
    yaml += `    x: ${comp.x}\n`;
    yaml += `    y: ${comp.y}\n`;
    yaml += `    width: ${comp.width}\n`;
    yaml += `    height: ${comp.height}\n`;

    const configEntries = Object.entries(comp.config || {}).filter(
      ([, v]) => v !== "" && v !== undefined && v !== null
    );

    if (configEntries.length > 0) {
      yaml += `    config:\n`;
      configEntries.forEach(([k, v]) => {
        yaml += `      ${k}: ${formatConfigValue(v)}\n`;
      });
    }
  });

  return yaml;
}
