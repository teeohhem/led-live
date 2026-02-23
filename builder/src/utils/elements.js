/**
 * Element type definitions for each mode
 * These match the exact field names expected by the templated renderers
 */

export const MODE_ELEMENTS = {
  sports: [
    {
      type: "away_logo",
      icon: "🏀",
      label: "Away Logo",
      width: 16,
      height: 16,
    },
    {
      type: "away_score",
      icon: "🔢",
      label: "Away Score",
      width: 30,
      height: 14,
    },
    {
      type: "away_name",
      icon: "📝",
      label: "Away Name",
      width: 25,
      height: 10,
    },
    {
      type: "away_text",
      icon: "📝",
      label: "Away Text (Name+Score)",
      width: 40,
      height: 10,
    },
    {
      type: "home_logo",
      icon: "🏡",
      label: "Home Logo",
      width: 16,
      height: 16,
    },
    {
      type: "home_score",
      icon: "🔢",
      label: "Home Score",
      width: 30,
      height: 14,
    },
    {
      type: "home_name",
      icon: "📝",
      label: "Home Name",
      width: 25,
      height: 10,
    },
    {
      type: "home_text",
      icon: "📝",
      label: "Home Text (Name+Score)",
      width: 40,
      height: 10,
    },
    {
      type: "period",
      icon: "⏱️",
      label: "Period (Q1, P2)",
      width: 20,
      height: 8,
    },
    { type: "clock", icon: "🕐", label: "Game Clock", width: 40, height: 8 },
    { type: "time", icon: "📅", label: "Game Time", width: 40, height: 8 },
  ],
  stocks: [
    {
      type: "symbol",
      icon: "💼",
      label: "Stock Symbol",
      width: 30,
      height: 10,
    },
    { type: "name", icon: "🏢", label: "Company Name", width: 50, height: 10 },
    { type: "price", icon: "💵", label: "Price", width: 40, height: 10 },
    { type: "change", icon: "📊", label: "Change ($)", width: 35, height: 8 },
    {
      type: "change_percent",
      icon: "📈",
      label: "Change (%)",
      width: 35,
      height: 8,
    },
  ],
  weather: [
    {
      type: "weather_icon",
      icon: "🌤️",
      label: "Weather Icon",
      width: 16,
      height: 16,
    },
    {
      type: "temperature",
      icon: "🌡️",
      label: "Temperature",
      width: 40,
      height: 12,
    },
    {
      type: "feels_like",
      icon: "🥶",
      label: "Feels Like",
      width: 40,
      height: 8,
    },
    { type: "condition", icon: "☁️", label: "Condition", width: 50, height: 8 },
    {
      type: "condition_short",
      icon: "☁️",
      label: "Condition (Short)",
      width: 30,
      height: 8,
    },
    { type: "humidity", icon: "💧", label: "Humidity", width: 30, height: 8 },
    { type: "wind", icon: "💨", label: "Wind Speed", width: 35, height: 8 },
    { type: "high_temp", icon: "🔥", label: "High Temp", width: 30, height: 8 },
    { type: "low_temp", icon: "🧊", label: "Low Temp", width: 30, height: 8 },
    { type: "location", icon: "📍", label: "Location", width: 50, height: 8 },
    {
      type: "forecast_icon",
      icon: "🔮",
      label: "Forecast Icon",
      width: 12,
      height: 12,
    },
    {
      type: "forecast_temp",
      icon: "📅",
      label: "Forecast Temp",
      width: 30,
      height: 8,
    },
    {
      type: "forecast_time",
      icon: "🕐",
      label: "Forecast Time",
      width: 35,
      height: 8,
    },
  ],
};

/**
 * Element groups — place a complete set of elements for a common layout in one click.
 * `scenarios` controls which scenarios show the group (null = all scenarios).
 * Each element spec matches the shape addElement expects.
 */
export const ELEMENT_GROUPS = {
  sports: [
    {
      id: 'live_game',
      icon: '🏀',
      label: 'Live Game',
      description: 'Logos + scores + period + clock',
      scenarios: ['one_item'],
      elements: [
        { type: 'away_logo',  x: 1,  y: 2,  width: 16, height: 16, fontSize: 10, color: 'white',     align: 'left' },
        { type: 'away_score', x: 19, y: 5,  width: 12, height: 10, fontSize: 10, color: 'away_team', align: 'left' },
        { type: 'period',     x: 28, y: 0,  width: 8,  height: 7,  fontSize: 7,  color: 'time',      align: 'center' },
        { type: 'clock',      x: 26, y: 13, width: 12, height: 7,  fontSize: 7,  color: 'time',      align: 'center' },
        { type: 'home_score', x: 33, y: 5,  width: 12, height: 10, fontSize: 10, color: 'home_team', align: 'left' },
        { type: 'home_logo',  x: 47, y: 2,  width: 16, height: 16, fontSize: 10, color: 'white',     align: 'left' },
      ],
    },
    {
      id: 'compact_game',
      icon: '⚡',
      label: 'Compact Game Row',
      description: 'Away abbr + scores + home abbr (for multi-game)',
      scenarios: ['two_items', 'three_items', 'four_items'],
      elements: [
        { type: 'away_text',  x: 0,  y: 1,  width: 28, height: 8,  fontSize: 8,  color: 'away_team', align: 'left' },
        { type: 'home_text',  x: 36, y: 1,  width: 28, height: 8,  fontSize: 8,  color: 'home_team', align: 'right' },
        { type: 'period',     x: 27, y: 1,  width: 10, height: 7,  fontSize: 7,  color: 'time',      align: 'center' },
      ],
    },
  ],

  stocks: [
    {
      id: 'stock_quote',
      icon: '📈',
      label: 'Stock Quote',
      description: 'Symbol + price + change',
      scenarios: ['one_item'],
      elements: [
        { type: 'symbol',         x: 1,  y: 2,  width: 28, height: 9,  fontSize: 9,  color: 'white',        align: 'left' },
        { type: 'price',          x: 1,  y: 11, width: 36, height: 8,  fontSize: 8,  color: 'white',        align: 'left' },
        { type: 'change_percent', x: 40, y: 11, width: 24, height: 8,  fontSize: 7,  color: 'change_color', align: 'right' },
      ],
    },
    {
      id: 'compact_stock',
      icon: '💹',
      label: 'Compact Stock Row',
      description: 'Symbol + price + change% (for multi-stock)',
      scenarios: ['two_items', 'four_items'],
      elements: [
        { type: 'symbol',         x: 0,  y: 1,  width: 20, height: 8, fontSize: 8, color: 'white',        align: 'left' },
        { type: 'price',          x: 20, y: 1,  width: 24, height: 8, fontSize: 8, color: 'white',        align: 'left' },
        { type: 'change_percent', x: 44, y: 1,  width: 20, height: 8, fontSize: 7, color: 'change_color', align: 'right' },
      ],
    },
  ],

  weather: [
    {
      id: 'current_weather',
      icon: '🌤️',
      label: 'Current Weather',
      description: 'Icon + temperature + condition',
      scenarios: ['one_item'],
      elements: [
        { type: 'weather_icon', x: 1,  y: 2,  width: 16, height: 16, fontSize: 10, color: 'white',      align: 'left' },
        { type: 'temperature',  x: 19, y: 3,  width: 30, height: 11, fontSize: 11, color: 'temp_color', align: 'left' },
        { type: 'condition',    x: 19, y: 14, width: 45, height: 7,  fontSize: 7,  color: 'gray',       align: 'left' },
      ],
    },
    {
      id: 'forecast_day',
      icon: '🗓️',
      label: 'Forecast Day',
      description: 'Day name + icon + high/low — one row per day',
      scenarios: ['two_items', 'three_items', 'four_items'],
      elements: [
        { type: 'forecast_time', x: 0,  y: 0,  width: 64, height: 7,  fontSize: 7, color: 'gray',   align: 'center' },
        { type: 'forecast_icon', x: 26, y: 7,  width: 12, height: 12, fontSize: 8, color: 'white',  align: 'left' },
        { type: 'high_temp',     x: 40, y: 10, width: 14, height: 7,  fontSize: 7, color: 'yellow', align: 'left' },
        { type: 'low_temp',      x: 10, y: 10, width: 14, height: 7,  fontSize: 7, color: 'cyan',   align: 'left' },
      ],
    },
  ],
};

export const SCENARIO_DEFINITIONS = {
  sports: [
    { value: "one_item", label: "1 Game", icon: "📺" },
    { value: "two_items", label: "2 Games", icon: "⚡" },
    { value: "three_items", label: "3 Games", icon: "📊" },
    { value: "four_items", label: "4 Games", icon: "📋" },
  ],
  stocks: [
    { value: "one_item", label: "1 Stock", icon: "💎" },
    { value: "two_items", label: "2 Stocks", icon: "📊" },
    { value: "four_items", label: "4 Stocks", icon: "📋" },
  ],
  weather: [
    { value: "one_item", label: "Current", icon: "🌤️" },
    { value: "two_items", label: "With Forecast", icon: "🔮" },
  ],
};
