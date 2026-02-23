/**
 * Composite component type definitions.
 * Each entry describes a renderable widget that can be placed on a composite canvas.
 */

export const COMPONENT_TYPES = {
  clock: {
    label: "Clock",
    icon: "🕐",
    color: "#667eea",
    defaultWidth: 64,
    defaultHeight: 20,
    defaultConfig: { theme: "stranger_things", hour24: false },
    configSchema: [
      {
        key: "theme",
        label: "Theme",
        type: "select",
        options: ["stranger_things", "classic", "matrix"],
      },
      { key: "hour24", label: "24-hour format", type: "checkbox" },
    ],
  },

  weather_current: {
    label: "Weather (Current)",
    icon: "🌤️",
    color: "#4ade80",
    defaultWidth: 64,
    defaultHeight: 20,
    defaultConfig: { show_icon: true, show_feels_like: false },
    configSchema: [
      { key: "show_icon", label: "Show weather icon", type: "checkbox" },
      { key: "show_feels_like", label: 'Show "feels like"', type: "checkbox" },
    ],
  },

  weather_extended: {
    label: "Weather (Forecast)",
    icon: "🔮",
    color: "#38bdf8",
    defaultWidth: 64,
    defaultHeight: 20,
    defaultConfig: { days: 4 },
    configSchema: [
      { key: "days", label: "Forecast days", type: "number", min: 1, max: 7 },
    ],
  },

  sports_live: {
    label: "Sports (Live)",
    icon: "🏀",
    color: "#f97316",
    defaultWidth: 64,
    defaultHeight: 20,
    defaultConfig: { max_games: 2 },
    configSchema: [
      {
        key: "max_games",
        label: "Max games to show",
        type: "number",
        min: 1,
        max: 4,
      },
    ],
  },

  stocks: {
    label: "Stocks",
    icon: "📈",
    color: "#a78bfa",
    defaultWidth: 64,
    defaultHeight: 20,
    defaultConfig: { limit: 2 },
    configSchema: [
      { key: "limit", label: "Max stocks", type: "number", min: 1, max: 6 },
      {
        key: "screener",
        label: "Screener (optional)",
        type: "select",
        options: ["", "GAINERS", "LOSERS", "MOST_ACTIVE"],
      },
    ],
  },
};
