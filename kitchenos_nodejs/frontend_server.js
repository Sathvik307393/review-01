const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = 3000;
const HTML_FILE = path.join(__dirname, "index.html");

const server = http.createServer((req, res) => {
  console.log(`  [FrontendServer] ${req.method} ${req.url}`);

  if (req.method === "GET" || req.method === "HEAD") {
    if (fs.existsSync(HTML_FILE)) {
      const html = fs.readFileSync(HTML_FILE, "utf8");
      res.writeHead(200, {
        "Content-Type": "text/html",
        "Content-Length": Buffer.byteLength(html)
      });
      if (req.method === "GET") {
        res.end(html);
      } else {
        res.end();
      }
    } else {
      const msg = "<h1>index.html not found!</h1>";
      res.writeHead(404, {
        "Content-Type": "text/html",
        "Content-Length": Buffer.byteLength(msg)
      });
      res.end(msg);
    }
  } else {
    const msg = "Method not allowed";
    res.writeHead(405, {
      "Content-Type": "text/plain",
      "Content-Length": Buffer.byteLength(msg)
    });
    res.end(msg);
  }
});

server.listen(PORT, () => {
  console.log(`[FrontendServer] Frontend Server listening on port ${PORT}...`);
  console.log(`Local Access URL: http://localhost:${PORT}`);
});
