const fs = require("fs");
const path = require("path");

const DATA_DIR = __dirname;

function getFilePath(collectionName) {
  return path.join(DATA_DIR, `db_${collectionName}.json`);
}

/**
 * Thread/Process safe JSON file helper.
 * Reads content of a collection file. If it doesn't exist, returns defaultData.
 */
function readCollection(collectionName, defaultData = []) {
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

/**
 * Writes data atomically to the collection file.
 */
function writeCollection(collectionName, data) {
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

/**
 * Helper to generate a new ID for an item in a collection.
 * Prefix is e.g. "r" for recipes, "p" for pantry.
 */
function generateId(collectionName, prefix) {
  const items = readCollection(collectionName);
  let index = items.length + 1;
  let newId = `${prefix}${index}`;
  
  // Find a unique ID in case items were deleted
  const idSet = new Set(items.map(item => item.id || item._id));
  while (idSet.has(newId)) {
    index++;
    newId = `${prefix}${index}`;
  }
  return newId;
}

module.exports = {
  readCollection,
  writeCollection,
  generateId
};
