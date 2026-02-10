const fs = require('fs');
const path = require('path');

// Mock window object
const window = {};

// Read data.js content
const dataJsPath = path.join(__dirname, 'data.js');
const dataJsContent = fs.readFileSync(dataJsPath, 'utf8');

// Execute data.js content
// We wrap it in a function to avoid global scope pollution issues if any
try {
    eval(dataJsContent);

    // Output the standards as JSON
    if (window.initialStandards) {
        console.log(JSON.stringify(window.initialStandards, null, 2));
    } else {
        console.error("Error: window.initialStandards not found after eval.");
        process.exit(1);
    }
} catch (e) {
    console.error("Error evaluating data.js:", e);
    process.exit(1);
}
