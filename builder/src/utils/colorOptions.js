/**
 * Color options for template elements
 */

export const DYNAMIC_COLORS = {
  sports: [
    { value: 'away_team', label: '🏀 Away Team Color (dynamic)', description: 'Uses away team\'s primary color' },
    { value: 'home_team', label: '🏡 Home Team Color (dynamic)', description: 'Uses home team\'s primary color' },
    { value: 'time', label: '⏱️ Time/Clock (yellow)', description: 'Yellow for periods and clocks' },
  ],
  stocks: [
    { value: 'change_color', label: '📈 Change Color (dynamic)', description: 'Green if up, red if down' },
  ],
  weather: [
    { value: 'temp_color', label: '🌡️ Temperature Color (dynamic)', description: 'Blue/orange/yellow by temp' },
  ]
};

export const STATIC_COLORS = [
  { value: 'white', label: 'White', color: '#ffffff' },
  { value: 'gray', label: 'Gray', color: '#808080' },
  { value: 'red', label: 'Red', color: '#ff0000' },
  { value: 'green', label: 'Green', color: '#00ff00' },
  { value: 'blue', label: 'Blue', color: '#0000ff' },
  { value: 'yellow', label: 'Yellow', color: '#ffff00' },
  { value: 'cyan', label: 'Cyan', color: '#00ffff' },
  { value: 'magenta', label: 'Magenta', color: '#ff00ff' },
];

export function getColorOptions(mode) {
  return [
    ...(DYNAMIC_COLORS[mode] || []),
    ...STATIC_COLORS
  ];
}

