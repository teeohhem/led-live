import { useState, useCallback } from 'react';

/**
 * Central state management for template builder
 */
export function useTemplateState() {
  const [templates, setTemplates] = useState({
    sports: {
      one_item: { elements: [] },
      two_items: { elements: [], item_height: 10 },
      three_items: { elements: [], item_height: 10 },
      four_items: { elements: [], item_height: 10 },
      logo_enabled: true
    },
    stocks: {
      one_item: { elements: [] },
      two_items: { elements: [], item_height: 10 },
      four_items: { elements: [], item_height: 10 },
      logo_enabled: false
    },
    weather: {
      one_item: { elements: [] },
      two_items: { elements: [], item_height: 10 },
      logo_enabled: false
    }
  });

  const [currentMode, setCurrentMode] = useState('sports');
  const [currentScenario, setCurrentScenario] = useState('one_item');
  
  const [displayConfig, setDisplayConfig] = useState({
    panel_width: 64,
    panel_height: 20,
    num_panels: 2,
    orientation: 'vertical' // Changed to match your actual template (64x40)
  });

  const elements = templates[currentMode][currentScenario]?.elements || [];

  const addElement = useCallback((type, x, y, width, height) => {
    const newElement = {
      id: Date.now(),
      type,
      x,
      y,
      width,
      height,
      text: type.replace(/_/g, ' '),
      color: '#ffffff',
      fontSize: 10,
      align: 'left'
    };

    setTemplates(prev => ({
      ...prev,
      [currentMode]: {
        ...prev[currentMode],
        [currentScenario]: {
          ...prev[currentMode][currentScenario],
          elements: [...prev[currentMode][currentScenario].elements, newElement]
        }
      }
    }));

    return newElement;
  }, [currentMode, currentScenario]);

  const updateElement = useCallback((elementId, updates) => {
    setTemplates(prev => ({
      ...prev,
      [currentMode]: {
        ...prev[currentMode],
        [currentScenario]: {
          ...prev[currentMode][currentScenario],
          elements: prev[currentMode][currentScenario].elements.map(el =>
            el.id === elementId ? { ...el, ...updates } : el
          )
        }
      }
    }));
  }, [currentMode, currentScenario]);

  const deleteElement = useCallback((element) => {
    if (!element) return;
    
    setTemplates(prev => ({
      ...prev,
      [currentMode]: {
        ...prev[currentMode],
        [currentScenario]: {
          ...prev[currentMode][currentScenario],
          elements: prev[currentMode][currentScenario].elements.filter(el => el.id !== element.id)
        }
      }
    }));
  }, [currentMode, currentScenario]);

  const duplicateElement = useCallback((element) => {
    if (!element) return;
    
    const duplicate = {
      ...element,
      id: Date.now(),
      x: element.x + 5,
      y: element.y + 5
    };

    setTemplates(prev => ({
      ...prev,
      [currentMode]: {
        ...prev[currentMode],
        [currentScenario]: {
          ...prev[currentMode][currentScenario],
          elements: [...prev[currentMode][currentScenario].elements, duplicate]
        }
      }
    }));

    return duplicate;
  }, [currentMode, currentScenario]);

  const optimizeSpace = useCallback(() => {
    const sorted = [...elements].sort((a, b) => {
      if (a.y !== b.y) return a.y - b.y;
      return a.x - b.x;
    });

    let currentY = 2;
    let currentX = 2;
    const spacing = 2;
    const totalWidth = displayConfig.orientation === 'horizontal' 
      ? displayConfig.panel_width * displayConfig.num_panels 
      : displayConfig.panel_width;

    sorted.forEach(elem => {
      if (currentX + elem.width > totalWidth) {
        currentX = 2;
        currentY += 12;
      }

      elem.x = currentX;
      elem.y = currentY;
      currentX += elem.width + spacing;
    });

    setTemplates(prev => ({
      ...prev,
      [currentMode]: {
        ...prev[currentMode],
        [currentScenario]: {
          ...prev[currentMode][currentScenario],
          elements: sorted
        }
      }
    }));
  }, [currentMode, currentScenario, elements, displayConfig]);

  const loadTemplates = useCallback((templateData) => {
    console.log('=== loadTemplates called ===');
    console.log('Template data:', templateData);
    
    // Parse template data and convert to builder format
    const parsed = {};
    
    ['sports', 'stocks', 'weather'].forEach(mode => {
      if (!templateData[mode]) {
        // Use default empty structure if not in loaded data
        parsed[mode] = {
          one_item: { elements: [] },
          two_items: { elements: [], item_height: 10 },
          three_items: { elements: [], item_height: 10 },
          four_items: { elements: [], item_height: 10 },
          logo_enabled: false
        };
        return;
      }
      
      const modeData = templateData[mode];
      parsed[mode] = {
        logo_enabled: modeData.logo_enabled !== undefined ? modeData.logo_enabled : false,
        one_item: { elements: [] },
        two_items: { elements: [], item_height: 10 },
        three_items: { elements: [], item_height: 10 },
        four_items: { elements: [], item_height: 10 }
      };
      
      // Parse each scenario
      ['one_item', 'two_items', 'three_items', 'four_items'].forEach(scenario => {
        if (modeData[scenario]) {
          const scenarioData = modeData[scenario];
          const elements = [];
          let idCounter = Date.now() + Math.random() * 1000;
          
          // For one_item, elements are directly in scenario
          // For multi-item, elements are in item_template
          const elementSource = scenario === 'one_item' 
            ? scenarioData 
            : scenarioData.item_template || {};
          
          Object.entries(elementSource).forEach(([key, spec]) => {
            // Skip non-element properties
            if (key === 'item_height' || key === 'item_template') return;
            
            const element = {
              id: idCounter++,
              type: key,
              x: Math.round(spec.x || 0), // Round to integer
              y: Math.round(spec.y || 0), // Round to integer
              width: Math.round(spec.width || (key.includes('icon') || key.includes('logo') ? 16 : 40)),
              height: Math.round(spec.height || (key.includes('icon') || key.includes('logo') ? 16 : 10)),
              text: key.replace(/_/g, ' '),
              color: spec.color || '#ffffff',
              fontSize: Math.round(spec.font_size || 10),
              align: spec.align || 'left'
            };
            
            elements.push(element);
          });
          
          parsed[mode][scenario] = {
            elements,
            item_height: scenarioData.item_height || 10
          };
          
          console.log(`  Loaded ${mode}.${scenario}: ${elements.length} elements`);
        }
      });
    });
    
    console.log('Parsed templates:', parsed);
    console.log('=== Setting templates state ===');
    setTemplates(parsed);
    console.log('=== Templates state updated ===');
  }, []); // Remove dependencies to prevent re-creation

  const generateYAML = useCallback(() => {
    // Generate YAML from current template state
    // Implementation similar to existing generateTemplate()
    return '# Generated YAML here';
  }, []); // templates not needed in closure

  return {
    templates,
    currentMode,
    currentScenario,
    elements,
    displayConfig,
    setCurrentMode,
    setCurrentScenario,
    addElement,
    updateElement,
    deleteElement,
    duplicateElement,
    optimizeSpace,
    loadTemplates,
    setDisplayConfig,
    generateYAML
  };
}

