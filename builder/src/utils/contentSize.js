/**
 * Calculate actual rendered size of content
 */

// Approximate character widths for PixelOperator font
const CHAR_WIDTH_RATIO = 0.6; // Width is ~60% of font size for monospace

export function estimateTextSize(text, fontSize, align = 'left') {
  if (!text) return { width: 10, height: fontSize };
  
  // Estimate width based on character count and font size
  const charWidth = fontSize * CHAR_WIDTH_RATIO;
  const width = Math.ceil(text.length * charWidth) + 4; // +4 for padding
  const height = fontSize + 2; // +2 for vertical clearance
  
  return { width, height };
}

export function getSampleContent(elementType, mode) {
  const samples = {
    sports: {
      away_score: '102',
      home_score: '95',
      away_name: 'BOS',
      home_name: 'DET',
      away_text: 'BOS 102',
      home_text: 'DET 95',
      period: 'Q4',
      clock: '2:45',
      time: '7:00 PM'
    },
    stocks: {
      symbol: 'AAPL',
      name: 'Apple Inc',
      price: '$195.50',
      change: '+$4.25',
      change_percent: '▲2.3%'
    },
    weather: {
      temperature: '45°F',
      feels_like: 'Feels 42°',
      condition: 'Cloudy',
      condition_short: 'CLOU',
      humidity: '65%',
      wind: '10mph',
      location: 'Brighton',
      high_temp: 'H50°',
      low_temp: 'L38°'
    }
  };
  
  return samples[mode]?.[elementType] || elementType;
}

export function getOptimalElementSize(element, mode) {
  // For logos/icons, use specified dimensions
  if (element.type.includes('logo') || element.type.includes('icon')) {
    return {
      width: element.width,
      height: element.height
    };
  }
  
  // For text elements, estimate based on content
  const sampleText = getSampleContent(element.type, mode);
  const { width, height } = estimateTextSize(sampleText, element.fontSize, element.align);
  
  return {
    width: Math.max(element.width, width), // Show at least specified width
    height: Math.max(element.height, height)
  };
}

