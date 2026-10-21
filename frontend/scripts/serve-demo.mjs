// Minimal static server for demo/index.html (browsers refuse ES modules over file://).
import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve } from "node:path";

// The repository root: the demo loads the built card from the integration's folder.
const root = resolve(import.meta.dirname, "../..");
const port = Number(process.env.PORT ?? 5000);
const types = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".map": "application/json",
};

createServer((req, res) => {
  const path = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
  const file = normalize(join(root, path === "/" ? "frontend/demo/index.html" : path));
  if (!file.startsWith(root) || !existsSync(file) || !statSync(file).isFile()) {
    res.writeHead(404).end("Not found");
    return;
  }
  res.writeHead(200, {
    "Content-Type": types[extname(file)] ?? "application/octet-stream",
  });
  createReadStream(file).pipe(res);
}).listen(port, () => console.log(`Demo: http://localhost:${port}/`));
