const { spawn } = require('child_process');
const path = require('path');

console.log('[BACKEND] Starting Python backend...');

const backendPath = path.join(__dirname, 'backend');
const pythonScript = path.join(backendPath, 'web_api.py');

console.log('[BACKEND] Backend directory:', backendPath);
console.log('[BACKEND] Python script:', pythonScript);

// Start the Python process
const python = spawn('python', [pythonScript], {
  cwd: backendPath,
  stdio: 'inherit'
});

python.on('error', (error) => {
  console.error('[BACKEND] Failed to start backend:', error);
});

python.on('close', (code) => {
  console.log(`[BACKEND] Backend process exited with code ${code}`);
});

process.on('SIGINT', () => {
  console.log('[BACKEND] Shutting down backend...');
  python.kill('SIGINT');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('[BACKEND] Shutting down backend...');
  python.kill('SIGTERM');
  process.exit(0);
});
