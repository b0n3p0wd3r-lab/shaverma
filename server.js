const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const port = process.env.PORT || 3000;

const publicRoot = path.join(__dirname, 'frontend');

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




