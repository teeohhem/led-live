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
