const { spawn } = require("child_process");
const path = require("path");

const SERVICES = [
  { name: "Metrics", script: "metrics_service.js" },
  { name: "Recipes", script: "recipes_service.js" },
  { name: "Pantry", script: "pantry_service.js" },
  { name: "Planner", script: "planner_service.js" },
  { name: "Shopping", script: "shopping_service.js" },
  { name: "Nutrition", script: "nutrition_service.js" },
  { name: "FrontendServer", script: "frontend_server.js" }
];

const children = [];
let isShuttingDown = false;

function streamLogs(name, stream) {
  stream.on("data", (data) => {
    const lines = data.toString("utf8").split("\n");
    lines.forEach((line) => {
      if (line.trim()) {
        console.log(`[${name}] ${line.trim()}`);
      }
    });
  });
}

function shutdown() {
  if (isShuttingDown) return;
  isShuttingDown = true;
  console.log("\nStopping all Node.js microservices...");
  
  children.forEach(({ name, proc }) => {
    if (proc.exitCode === null) {
      console.log(`  Killing ${name} (PID: ${proc.pid})...`);
      proc.kill("SIGTERM");
    }
  });
  console.log("All KitchenOS services stopped.\n");
  process.exit(0);
}

function main() {
  console.log("====================================================");
  console.log("     KitchenOS Node.js Platform Launcher            ");
  console.log("====================================================");
  console.log("Offline Mode: Persistent File-Based DB Client Active\n");
  console.log("Starting services...");

  SERVICES.forEach(({ name, script }) => {
    console.log(`  -> Starting ${name} (${script})...`);
    
    const scriptPath = path.join(__dirname, script);
    const proc = spawn("node", [scriptPath], {
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      stdio: ["ignore", "pipe", "pipe"]
    });

    children.push({ name, proc });

    streamLogs(name, proc.stdout);
    streamLogs(name + " [Err]", proc.stderr);

    proc.on("exit", (code) => {
      if (!isShuttingDown) {
        console.log(`\n[Warning] ${name} service terminated with exit code ${code}!`);
        shutdown();
      }
    });
  });

  console.log("\nAll microservices and local frontend server initialized successfully.");
  console.log("Central Access Endpoint: http://localhost:3000");
  console.log("Press Ctrl+C to terminate all services.\n");

  // Keep process alive and handle termination signals
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
  
  setInterval(() => {}, 1000); // keep event loop busy
}

main();
