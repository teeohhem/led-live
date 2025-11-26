/**
 * Template generation utilities
 */

export function generateYAML(templates, displayConfig) {
  const { panel_width, panel_height, num_panels, orientation } = displayConfig;

  const totalWidth =
    orientation === "horizontal" ? panel_width * num_panels : panel_width;
  const totalHeight =
    orientation === "vertical" ? panel_height * num_panels : panel_height;

  let yaml = `# ${totalWidth}×${totalHeight} Unified Layout Template\n`;
  yaml += `# Contains layouts for all modes\n\n`;

  ["sports", "stocks", "weather"].forEach((mode) => {
    const modeData = templates[mode];
    yaml += `# === ${mode.toUpperCase()} MODE ===\n`;
    yaml += `${mode}:\n`;
    yaml += `  canvas_width: ${totalWidth}\n`;
    yaml += `  canvas_height: ${totalHeight}\n`;

    // Check if any scenario has logos
    let hasLogos = false;
    Object.keys(modeData).forEach((scenario) => {
      if (scenario !== "logo_enabled" && modeData[scenario]?.elements) {
        hasLogos =
          hasLogos ||
          modeData[scenario].elements.some(
            (e) => e.type.includes("logo") || e.type.includes("icon")
          );
      }
    });
    yaml += `  logo_enabled: ${hasLogos}\n`;

    // Output all scenarios
    ["one_item", "two_items", "three_items", "four_items"].forEach(
      (scenario) => {
        if (modeData[scenario]?.elements?.length > 0) {
          yaml += `  ${scenario}:\n`;

          if (scenario !== "one_item") {
            // Multi-item layouts need item_height
            yaml += `    item_height: ${
              modeData[scenario].item_height || 10
            }\n`;
            yaml += `    item_template:\n`;
            const indent = "      ";

            modeData[scenario].elements.forEach((element) => {
              const key = element.type;
              yaml += `${indent}${key}:\n`;
              yaml += `${indent}  x: ${element.x}\n`;
              yaml += `${indent}  y: ${element.y}\n`;

              if (
                element.type.includes("logo") ||
                element.type.includes("icon")
              ) {
                yaml += `${indent}  width: ${element.width}\n`;
                yaml += `${indent}  height: ${element.height}\n`;
              } else {
                yaml += `${indent}  font_size: ${element.fontSize}\n`;
                yaml += `${indent}  color: "${element.color}"\n`;
                yaml += `${indent}  align: ${element.align}\n`;
              }
            });
          } else {
            // one_item layout
            modeData[scenario].elements.forEach((element) => {
              const key = element.type;
              yaml += `    ${key}:\n`;
              yaml += `      x: ${element.x}\n`;
              yaml += `      y: ${element.y}\n`;

              if (
                element.type.includes("logo") ||
                element.type.includes("icon")
              ) {
                yaml += `      width: ${element.width}\n`;
                yaml += `      height: ${element.height}\n`;
              } else {
                yaml += `      font_size: ${element.fontSize}\n`;
                yaml += `      color: "${element.color}"\n`;
                yaml += `      align: ${element.align}\n`;
              }
            });
          }
        }
      }
    );

    yaml += `\n`;
  });

  return yaml;
}

export function generateJSON(templates, displayConfig) {
  const { panel_width, panel_height, num_panels, orientation } = displayConfig;

  const totalWidth =
    orientation === "horizontal" ? panel_width * num_panels : panel_width;
  const totalHeight =
    orientation === "vertical" ? panel_height * num_panels : panel_height;

  const output = {};

  ["sports", "stocks", "weather"].forEach((mode) => {
    const modeData = templates[mode];
    const modeTemplate = {
      canvas_width: totalWidth,
      canvas_height: totalHeight,
      logo_enabled: modeData.logo_enabled || false,
    };

    ["one_item", "two_items", "three_items", "four_items"].forEach(
      (scenario) => {
        if (modeData[scenario]?.elements?.length > 0) {
          if (scenario === "one_item") {
            modeTemplate.one_item = {};
            modeData[scenario].elements.forEach((element) => {
              const spec = { x: element.x, y: element.y };

              if (
                element.type.includes("logo") ||
                element.type.includes("icon")
              ) {
                spec.width = element.width;
                spec.height = element.height;
              } else {
                spec.font_size = element.fontSize;
                spec.color = element.color;
                spec.align = element.align;
              }

              modeTemplate.one_item[element.type] = spec;
            });
          } else {
            modeTemplate[scenario] = {
              item_height: modeData[scenario].item_height || 10,
              item_template: {},
            };

            modeData[scenario].elements.forEach((element) => {
              const spec = { x: element.x, y: element.y };

              if (
                element.type.includes("logo") ||
                element.type.includes("icon")
              ) {
                spec.width = element.width;
                spec.height = element.height;
              } else {
                spec.font_size = element.fontSize;
                spec.color = element.color;
                spec.align = element.align;
              }

              modeTemplate[scenario].item_template[element.type] = spec;
            });
          }
        }
      }
    );

    output[mode] = modeTemplate;
  });

  return JSON.stringify(output, null, 2);
}
