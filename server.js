const express = require('express');
const path = require('path');
const fs = require('fs');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const port = process.env.PORT || 3000;

const publicRoot = path.join(__dirname, 'frontend');

// Proxy API requests to backend
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:8080',
  changeOrigin: true,
  logLevel: 'debug'
}));

// Serve Brotli-compressed Unity files with proper headers
app.get(/.*\.js\.br$/, (req, res) => {
  const filePath = path.join(publicRoot, req.url);
  if (fs.existsSync(filePath)) {
    res.setHeader('Content-Encoding', 'br');
    res.setHeader('Content-Type', 'application/javascript');
    return fs.createReadStream(filePath).pipe(res);
  }
  return res.status(404).send('File not found');
});

app.get(/.*\.wasm\.br$/, (req, res) => {
  const filePath = path.join(publicRoot, req.url);
  if (fs.existsSync(filePath)) {
    res.setHeader('Content-Encoding', 'br');
    res.setHeader('Content-Type', 'application/wasm');
    return fs.createReadStream(filePath).pipe(res);
  }
  return res.status(404).send('File not found');
});

app.get(/.*\.data\.br$/, (req, res) => {
  const filePath = path.join(publicRoot, req.url);
  if (fs.existsSync(filePath)) {
    res.setHeader('Content-Encoding', 'br');
    res.setHeader('Content-Type', 'application/octet-stream');
    return fs.createReadStream(filePath).pipe(res);
  }
  return res.status(404).send('File not found');
});

// Serve everything else statically from frontend
app.use(express.static(publicRoot));

// Fallback to frontend index.html (Express 5 catch-all via regex)
app.get(/.*/, (_req, res) => {
  res.sendFile(path.join(publicRoot, 'index.html'));
});

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});

// Add error handling and process monitoring
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

process.on('SIGINT', () => {
  console.log('Received SIGINT, gracefully shutting down...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('Received SIGTERM, gracefully shutting down...');
  process.exit(0);
});

console.log('Server process started with PID:', process.pid);

// Keep the process alive
setInterval(() => {
  // This prevents the process from exiting unexpectedly
}, 60000); // Check every minute




