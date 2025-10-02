const express = require('express');

const path = require('path');

const fs = require('fs');



const app = express();

const port = 3000;



app.get(/.*\.js\.br$/, (req, res) => {

  const filePath = path.join(__dirname, req.url);

  if (fs.existsSync(filePath)) {

    res.setHeader('Content-Encoding', 'br');

    res.setHeader('Content-Type', 'application/javascript');

    fs.createReadStream(filePath).pipe(res);

  } else {

    res.status(404).send('File not found');

  }

});



app.get(/.*\.wasm\.br$/, (req, res) => {

  const filePath = path.join(__dirname, req.url);

  if (fs.existsSync(filePath)) {

    res.setHeader('Content-Encoding', 'br');

    res.setHeader('Content-Type', 'application/wasm');

    fs.createReadStream(filePath).pipe(res);

  } else {

    res.status(404).send('File not found');

  }

});



app.get(/.*\.data\.br$/, (req, res) => {

  const filePath = path.join(__dirname, req.url);

  if (fs.existsSync(filePath)) {

    res.setHeader('Content-Encoding', 'br');

    res.setHeader('Content-Type', 'application/octet-stream');

    fs.createReadStream(filePath).pipe(res);

  } else {

    res.status(404).send('File not found');

  }

});



app.use(express.static(path.join(__dirname)));



app.listen(port, () => {

  console.log(`[OK] Сервер запущен: http://localhost:${port}`);

});
