const { MongoClient } = require("mongodb");
const fs = require("fs");
const path = require("path");

const DATA_DIR = __dirname;
const mongoUri = process.env.MONGO_URI;

let mongoClient = null;
let mongoDb = null;
let useMongo = false;
let isConnecting = false;

function getFilePath(collectionName) {
  return path.join(DATA_DIR, `db_${collectionName}.json`);
}

async function connectDB() {
  if (!mongoUri) {
    return;
  }
  if (useMongo || isConnecting) return;
  isConnecting = true;
  try {
    mongoClient = new MongoClient(mongoUri, { serverSelectionTimeoutMS: 3000 });
    await mongoClient.connect();
    mongoDb = mongoClient.db("kitchenos");
    useMongo = true;
    console.log("[DB] Connected to remote AWS MongoDB successfully.");
  } catch (err) {
    console.error("[DB] MongoDB connection failed. Falling back to local JSON files.", err.message);
    useMongo = false;
  } finally {
    isConnecting = false;
  }
}

// Immediately attempt connection on load
connectDB();

async function readCollection(collectionName, defaultData = []) {
  await connectDB();
  if (useMongo) {
    try {
      const items = await mongoDb.collection(collectionName).find({}).toArray();
      // Remove MongoDB native _id if it exists to keep compatible API
      return items.map(item => {
        const { _id, ...rest } = item;
        return rest;
      });
    } catch (err) {
      console.error(`[DB] MongoDB error reading "${collectionName}":`, err);
      return defaultData;
    }
  } else {
    // Local JSON fallback
    const filePath = getFilePath(collectionName);
    if (!fs.existsSync(filePath)) {
      return defaultData;
    }
    try {
      const data = fs.readFileSync(filePath, "utf8");
      return JSON.parse(data || "[]");
    } catch (err) {
      console.error(`[DB] Error reading collection "${collectionName}":`, err);
      return defaultData;
    }
  }
}

async function writeCollection(collectionName, data) {
  await connectDB();
  if (useMongo) {
    try {
      const col = mongoDb.collection(collectionName);
      await col.deleteMany({});
      if (data && data.length > 0) {
        await col.insertMany(data);
      }
      return true;
    } catch (err) {
      console.error(`[DB] MongoDB error writing "${collectionName}":`, err);
      return false;
    }
  } else {
    // Local JSON fallback
    const filePath = getFilePath(collectionName);
    const tempPath = filePath + ".tmp";
    try {
      fs.writeFileSync(tempPath, JSON.stringify(data, null, 2), "utf8");
      fs.renameSync(tempPath, filePath);
      return true;
    } catch (err) {
      console.error(`[DB] Error writing collection "${collectionName}":`, err);
      if (fs.existsSync(tempPath)) {
        try { fs.unlinkSync(tempPath); } catch (_) {}
      }
      return false;
    }
  }
}

async function generateId(collectionName, prefix) {
  const items = await readCollection(collectionName);
  let index = items.length + 1;
  let newId = `${prefix}${index}`;
  
  const idSet = new Set(items.map(item => item.id));
  while (idSet.has(newId)) {
    index++;
    newId = `${prefix}${index}`;
  }
  return newId;
}

module.exports = {
  readCollection,
  writeCollection,
  generateId,
  connectDB
};
