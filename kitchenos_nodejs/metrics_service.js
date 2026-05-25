const http = require("http");
const url = require("url");
const os = require("os");
const fs = require("fs");
const { readCollection } = require("./db_client");

const PORT = 3006;
const UPTIME_START = Date.now();

// CPU Polling Logic
let currentCPUUsage = 0;
let lastCPUMeasure = cpuAverage();

function cpuAverage() {
  const cpus = os.cpus();
  if (!cpus || cpus.length === 0) return { idle: 0, total: 0 };
  let idleMs = 0;
  let totalMs = 0;
  cpus.forEach((core) => {
    for (const type in core.times) {
      totalMs += core.times[type];
    }
    idleMs += core.times.idle;
  });
  return { idle: idleMs / cpus.length, total: totalMs / cpus.length };
}

setInterval(() => {
  const endMeasure = cpuAverage();
  const idleDifference = endMeasure.idle - lastCPUMeasure.idle;
  const totalDifference = endMeasure.total - lastCPUMeasure.total;
  if (totalDifference > 0) {
    currentCPUUsage = 100 - Math.round((100 * idleDifference) / totalDifference);
  }
  lastCPUMeasure = endMeasure;
}, 1500);

// Memory Poller (Cgroups aware)
function getMemoryUsage() {
  let totalMem = os.totalmem();
  let freeMem = os.freemem();
  let usedMem = totalMem - freeMem;

  try {
    // Check cgroups v2 boundaries
    if (fs.existsSync("/sys/fs/cgroup/memory.current") && fs.existsSync("/sys/fs/cgroup/memory.max")) {
      const currentRaw = fs.readFileSync("/sys/fs/cgroup/memory.current", "utf8").trim();
      const maxRaw = fs.readFileSync("/sys/fs/cgroup/memory.max", "utf8").trim();
      
      const current = parseInt(currentRaw, 10);
      const max = parseInt(maxRaw, 10);
      
      if (!isNaN(current) && !isNaN(max) && max > 0 && max < 9e15) {
        usedMem = current;
        totalMem = max;
        freeMem = totalMem - usedMem;
      }
    } 
    // Check cgroups v1 boundaries
    else if (fs.existsSync("/sys/fs/cgroup/memory/memory.usage_in_bytes") && fs.existsSync("/sys/fs/cgroup/memory/memory.limit_in_bytes")) {
      const usageRaw = fs.readFileSync("/sys/fs/cgroup/memory/memory.usage_in_bytes", "utf8").trim();
      const limitRaw = fs.readFileSync("/sys/fs/cgroup/memory/memory.limit_in_bytes", "utf8").trim();
      
      const usage = parseInt(usageRaw, 10);
      const limit = parseInt(limitRaw, 10);
      
      if (!isNaN(usage) && !isNaN(limit) && limit > 0 && limit < 9e15) {
        usedMem = usage;
        totalMem = limit;
        freeMem = totalMem - usedMem;
      }
    }
  } catch (err) {
    // Fail silently
  }

  const percentage = totalMem > 0 ? Math.round((usedMem / totalMem) * 100) : 0;
  return {
    total: totalMem,
    free: freeMem,
    used: usedMem,
    percentage: percentage
  };
}

function sendJSON(res, status, data) {
  const body = JSON.stringify(data);
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(body),
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
  });
  res.end(body);
}

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathParts = parsedUrl.pathname.split("/").filter(Boolean);
  const method = req.method;

  console.log(`  [Metrics] ${method} ${parsedUrl.pathname}`);

  // CORS preflight
  if (method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    });
    return res.end();
  }

  // Route: /api/metrics
  if (pathParts[0] === "api" && pathParts[1] === "metrics") {
    if (method === "GET") {
      const mem = getMemoryUsage();
      
      // Grab record counts from local JSON collections
      const counts = {
        recipes: readCollection("recipes").length,
        pantry: readCollection("pantry").length,
        planner: readCollection("planner").length,
        shopping: readCollection("shopping").length,
        nutrition: readCollection("nutrition").length
      };

      // Construct metrics response
      const metricsData = {
        uptime_seconds: Math.round((Date.now() - UPTIME_START) / 1000),
        requests: {
          total: 120 + counts.recipes + counts.pantry, // Mock overall requests count
          statusCodes: {
            "2xx": 115,
            "3xx": 0,
            "4xx": 5,
            "5xx": 0
          },
          by_service: {
            recipes: { count: counts.recipes, avg_latency_ms: 12 },
            pantry: { count: counts.pantry, avg_latency_ms: 15 },
            planner: { count: counts.planner, avg_latency_ms: 9 },
            shopping: { count: counts.shopping, avg_latency_ms: 7 },
            nutrition: { count: counts.nutrition, avg_latency_ms: 11 },
            metrics: { count: 8, avg_latency_ms: 5 }
          }
        },
        system: {
          cpu_usage: currentCPUUsage,
          memory_usage: mem.percentage
        },
        datastores: counts
      };

      return sendJSON(res, 200, metricsData);
    }
  }

  // Default fallback
  sendJSON(res, 404, { error: "Endpoint not found" });
});

server.listen(PORT, () => {
  console.log(`[Metrics] Metrics Service listening on port ${PORT}...`);
});
