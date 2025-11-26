# LED Panel Layout Builder (React)

Modern React-based visual template designer for LED panels.

## Structure

```
builder/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Sidebar.js           # Config controls & properties
│   │   ├── Toolbar.js           # Mode tabs & actions
│   │   ├── ScenarioBar.js       # Scenario selector
│   │   ├── Canvas.js            # Main editing canvas
│   │   ├── Element.js           # Draggable element
│   │   ├── ElementPalette.js    # Element library
│   │   ├── OutputPanel.js       # YAML/JSON/Preview
│   │   └── ContextMenu.js       # Right-click menu
│   ├── hooks/
│   │   └── useTemplateState.js  # Template state management
│   ├── utils/
│   │   ├── api.js               # API calls
│   │   ├── template.js          # Template generation
│   │   └── elements.js          # Element definitions
│   ├── App.js                   # Main app
│   ├── App.css
│   ├── index.js
│   └── index.css
└── package.json

## Benefits

✅ **Component-based** - Clean, reusable code
✅ **State management** - React hooks
✅ **Type safety** - Can add TypeScript later
✅ **Hot reload** - Fast development
✅ **Testable** - Unit test components
✅ **Maintainable** - 100-200 line files vs 2500 line monolith

## Development

```bash
cd builder
npm install
npm start
```

Runs on `http://localhost:3000` (proxies to emulator on 8080)

## Build for Production

```bash
npm run build
```

Outputs to `build/` - serve from emulator

## Migration

The old `layout_builder.html` is preserved but the React version is:
- Easier to maintain
- Better organized
- More extensible
- Professional architecture

## Next Steps

1. Install dependencies: `npm install`
2. Start dev server: `npm start`
3. Build components one by one
4. Test and iterate
5. Deploy when ready

