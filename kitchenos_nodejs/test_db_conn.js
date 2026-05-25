const { MongoClient } = require("mongodb");
const net = require("net");
const url = require("url");

const mongoUri = process.env.MONGO_URI;

if (!mongoUri) {
  console.error("❌ ERROR: MONGO_URI environment variable is not set!");
  console.log("Please run: export MONGO_URI=\"mongodb://kitchenos_user:KitchenOSPassword@192.16.0.244:27017/kitchenos?authSource=kitchenos\"");
  process.exit(1);
}

console.log("==========================================");
console.log("   MongoDB Connection Diagnostic Tool     ");
console.log("==========================================");
console.log(`Connection String: ${mongoUri.replace(/:([^:@]+)@/, ":******@")}\n`); // Mask password

// Parse connection details
let host = "127.0.0.1";
let port = 27017;
let dbName = "kitchenos";
let authSource = "kitchenos";

try {
  // Simple parsing of mongodb:// connection string
  const cleanUri = mongoUri.replace("mongodb://", "");
  const credentialPart = cleanUri.substring(0, cleanUri.lastIndexOf("@"));
  const connectionPart = cleanUri.substring(cleanUri.lastIndexOf("@") + 1);
  
  const [hostPort, queryParams] = connectionPart.split("?");
  const [h, p] = hostPort.split(":");
  host = h;
  port = p ? parseInt(p) : 27017;
  
  if (queryParams) {
    const params = new URLSearchParams(queryParams);
    if (params.has("authSource")) {
      authSource = params.get("authSource");
    }
  }
} catch (e) {
  console.warn("⚠️ Warning: Could not fully parse URI manually, using defaults for socket check.");
}

async function runDiagnostics() {
  // Step 1: Raw TCP Socket Check
  console.log(`Step 1: Testing raw TCP socket connection to ${host}:${port}...`);
  const socketCheck = new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(2500);
    
    socket.on("connect", () => {
      console.log("✅ Socket check: Successfully established TCP connection to port " + port + "!");
      socket.destroy();
      resolve(true);
    });
    
    socket.on("error", (err) => {
      console.error(`❌ Socket check: Failed to connect to ${host}:${port}`);
      console.error(`   Error details: ${err.message}`);
      resolve(false);
    });
    
    socket.on("timeout", () => {
      console.error(`❌ Socket check: Connection to ${host}:${port} timed out.`);
      socket.destroy();
      resolve(false);
    });
    
    socket.connect(port, host);
  });

  const tcpSuccess = await socketCheck;
  if (!tcpSuccess) {
    console.log("\n❌ DIAGNOSIS: Network blockage. Check VPN tunnel status, AWS route tables, and Security Groups/NSGs.");
    return;
  }

  // Step 2: MongoDB Client Connection and Auth Check
  console.log(`\nStep 2: Connecting via MongoClient and checking credentials...`);
  const client = new MongoClient(mongoUri, { serverSelectionTimeoutMS: 3000 });
  
  try {
    await client.connect();
    console.log("✅ MongoClient: Connected successfully to database server.");
    
    console.log(`\nStep 3: Checking authentication on database/authSource...`);
    const db = client.db(dbName);
    
    // Execute a simple command that requires auth
    const result = await db.command({ ping: 1 });
    console.log("✅ Auth check: Ping command completed successfully!");
    
    // List collections to verify read/write roles
    const collections = await db.listCollections().toArray();
    console.log(`✅ Auth check: Retrieved ${collections.length} collections from "${dbName}" database.`);
    
    console.log("\n🎉 SUCCESS: Your database connection is 100% working and authenticated!");
  } catch (err) {
    console.error("❌ MongoClient error encountered:");
    console.error(`   Message: ${err.message}`);
    console.error(`   Code: ${err.code}`);
    
    if (err.message.includes("Authentication failed") || err.code === 18) {
      console.log("\n❌ DIAGNOSIS: Authentication Failed.");
      console.log(`   Check if 'kitchenos_user' exists in the database '${dbName}' with 'authSource=${authSource}'.`);
      console.log("   Make sure the password matches 'KitchenOSPassword'.");
    } else {
      console.log("\n❌ DIAGNOSIS: Unknown MongoDB Server error. See the error details above.");
    }
  } finally {
    await client.close();
  }
}

runDiagnostics();
