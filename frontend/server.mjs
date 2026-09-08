// Servidor del frontend en App Service (Node, sin dependencias):
// sirve el SPA compilado desde ./dist y hace de proxy inverso de /api y /metrics al backend.
// El backend puede ser privado (se resuelve por DNS privado vía VNet integration).
import http from 'node:http';
import https from 'node:https';
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST = path.join(__dirname, 'dist');
const PORT = Number(process.env.PORT) || 8000;
const BACKEND_URL = process.env.BACKEND_URL || '';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.ico': 'image/x-icon',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.map': 'application/json',
  '.txt': 'text/plain; charset=utf-8',
};

function proxy(req, res) {
  if (!BACKEND_URL) {
    res.writeHead(502, { 'content-type': 'text/plain' });
    res.end('BACKEND_URL no configurado');
    return;
  }
  let target;
  try {
    target = new URL(req.url, BACKEND_URL);
  } catch {
    res.writeHead(400);
    res.end('bad request');
    return;
  }
  const client = target.protocol === 'https:' ? https : http;
  const headers = { ...req.headers, host: target.host };
  const upstream = client.request(
    target,
    { method: req.method, headers },
    (upRes) => {
      res.writeHead(upRes.statusCode || 502, upRes.headers);
      upRes.pipe(res);
    }
  );
  upstream.on('error', (err) => {
    res.writeHead(502, { 'content-type': 'text/plain' });
    res.end('proxy error: ' + err.message);
  });
  req.pipe(upstream);
}

async function serveStatic(req, res) {
  const urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
  let filePath = path.join(DIST, urlPath === '/' ? '/index.html' : urlPath);
  if (!filePath.startsWith(DIST)) {
    res.writeHead(403);
    res.end('forbidden');
    return;
  }
  try {
    const s = await stat(filePath);
    if (s.isDirectory()) filePath = path.join(filePath, 'index.html');
  } catch {
    filePath = path.join(DIST, 'index.html'); // SPA fallback
  }
  const ext = path.extname(filePath).toLowerCase();
  res.writeHead(200, { 'content-type': MIME[ext] || 'application/octet-stream' });
  createReadStream(filePath)
    .on('error', () => {
      res.writeHead(404);
      res.end('not found');
    })
    .pipe(res);
}

http
  .createServer((req, res) => {
    const url = req.url || '/';
    if (url.startsWith('/api') || url.startsWith('/metrics')) return proxy(req, res);
    return serveStatic(req, res);
  })
  .listen(PORT, () => {
    console.log(`frontend en :${PORT} -> backend ${BACKEND_URL || '(sin configurar)'}`);
  });
