"""
Streamlit app for Excalidraw whiteboard.
Uses components.html to render in an iframe (supports ES modules and importmaps).
"""
import streamlit as st
from streamlit.components.v1 import html as components_html

st.set_page_config(
    page_title="Excalidraw Whiteboard",
    page_icon="🎨",
    layout="wide",
)

st.title("Excalidraw Whiteboard")

excalidraw_html = """
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Excalidraw Test</title>
    <link
      rel="stylesheet"
      href="https://esm.sh/@excalidraw/excalidraw@0.18.0/dist/dev/index.css"
    />
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
        }
        #container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            margin-top: 0;
            color: #333;
        }
        #app {
            height: 600px;
            width: 100%;
            border: 2px solid #ddd;
            border-radius: 5px;
            margin-top: 20px;
        }
        #status {
            padding: 15px;
            background: #e3f2fd;
            border-radius: 5px;
            margin-top: 20px;
            font-family: monospace;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
    <script>
        window.EXCALIDRAW_ASSET_PATH = "https://esm.sh/@excalidraw/excalidraw@0.18.0/dist/prod/";
    </script>
    <script type="importmap">
    {
        "imports": {
            "react": "https://esm.sh/react@19.0.0",
            "react/jsx-runtime": "https://esm.sh/react@19.0.0/jsx-runtime",
            "react-dom": "https://esm.sh/react-dom@19.0.0",
            "react-dom/client": "https://esm.sh/react-dom@19.0.0/client"
        }
    }
    </script>
</head>
<body>
    <div id="container">
        <h1>Excalidraw Standalone Test</h1>

        <div id="app"></div>

        <div id="status">Loading Excalidraw...</div>
    </div>

    <script type="module">
        const statusEl = document.getElementById('status');

        function log(message) {
            console.log(message);
            statusEl.textContent += message + '\\n';
        }

        log('===== EXCALIDRAW: Starting initialization =====');

        try {
            log('Importing modules from esm.sh...');

            // Import React first (will use import map)
            const React = await import("react");
            log('✓ React loaded');

            const ReactDOM = await import("react-dom/client");
            log('✓ ReactDOM loaded');

            // Import Excalidraw from the dev build path (as per official example)
            const ExcalidrawLib = await import('https://esm.sh/@excalidraw/excalidraw@0.18.0/dist/dev/index.js?external=react,react-dom');
            log('✓ ExcalidrawLib loaded');

            log('\\n===== EXCALIDRAW: All modules loaded successfully =====\\n');
            log('ExcalidrawLib keys: ' + Object.keys(ExcalidrawLib).join(', '));

            window.ExcalidrawLib = ExcalidrawLib;
            window.React = React;
            window.ReactDOM = ReactDOM;

            log('\\nCreating Excalidraw app...');

            const App = () => {
                return React.createElement(
                    React.Fragment,
                    null,
                    React.createElement(
                        "div",
                        { style: { height: "600px" } },
                        React.createElement(ExcalidrawLib.Excalidraw),
                    ),
                );
            };

            const excalidrawWrapper = document.getElementById("app");
            if (excalidrawWrapper) {
                log('Rendering to DOM...');
                const root = ReactDOM.createRoot(excalidrawWrapper);
                root.render(React.createElement(App));
                log('\\n===== EXCALIDRAW: Successfully initialized! =====');
                log('You should see the Excalidraw interface above.');
            } else {
                log('ERROR: Container element not found!');
            }
        } catch (error) {
            log('\\n===== EXCALIDRAW: Error during initialization =====');
            log('Error: ' + error.message);
            log('Stack: ' + error.stack);

            const container = document.getElementById('app');
            if (container) {
                container.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #fff3cd; border-radius: 5px; padding: 20px; text-align: center;">
                        <div>
                            <h3 style="color: #856404;">⚠️ Excalidraw Failed to Load</h3>
                            <p style="color: #856404;">Error: ${error.message}</p>
                            <p style="color: #666; font-size: 14px;">Check the console and status box below for details</p>
                        </div>
                    </div>
                `;
            }
        }
    </script>
</body>
"""

components_html(excalidraw_html, height=800)


st.html(excalidraw_html, unsafe_allow_javascript=True)
