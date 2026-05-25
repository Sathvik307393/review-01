const http = require("http");
const url = require("url");
const { readCollection, writeCollection, generateId } = require("./db_client");

const PORT = 3004;

// Seed initial shopping list matching our Indian recipes
const SEED_SHOPPING = [
  { id: "sh1", item: "Fresh Paneer", category: "Dairy", quantity: 400, unit: "g", checked: false, recipe_id: "r2", priority: "high" },
  { id: "sh2", item: "Heavy Cream", category: "Dairy", quantity: 200, unit: "ml", checked: false, recipe_id: "r2", priority: "high" },
  { id: "sh3", item: "Basmati Rice", category: "Grains", quantity: 1, unit: "kg", checked: true, recipe_id: "r1", priority: "medium" },
  { id: "sh4", item: "Green Peas", category: "Produce", quantity: 250, unit: "g", checked: false, recipe_id: "r4", priority: "low" },
  { id: "sh5", item: "Kasuri Methi", category: "Spices", quantity: 50, unit: "g", checked: false, recipe_id: "r2", priority: "medium" }
];

// Initialize database with seeds if empty
if (readCollection("shopping").length === 0) {
  console.log("[Shopping] Seeding shopping list datastore...");
  writeCollection("shopping", SEED_SHOPPING);
}

function sendJSON(res, status, data) {
  const body = JSON.stringify(data);
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(body),
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
  });
  res.end(body);
}

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathParts = parsedUrl.pathname.split("/").filter(Boolean);
  const method = req.method;

  console.log(`  [Shopping] ${method} ${parsedUrl.pathname}`);

  // CORS preflight
  if (method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    });
    return res.end();
  }

  // Route: /api/shopping or /api/shopping/<id>
  if (pathParts[0] === "api" && pathParts[1] === "shopping") {
    const id = pathParts[2] || null;
    const shoppingList = readCollection("shopping");
    const recipes = readCollection("recipes");

    if (method === "GET") {
      const unchecked = shoppingList.filter(i => !i.checked).length;
      
      const enriched = shoppingList.map(item => {
        const recipeDetail = item.recipe_id ? recipes.find(r => r.id === item.recipe_id) || null : null;
        return { ...item, recipe: recipeDetail };
      });

      const byCategory = {};
      enriched.forEach(item => {
        if (!byCategory[item.category]) byCategory[item.category] = [];
        byCategory[item.category].push(item);
      });

      return sendJSON(res, 200, {
        items: enriched,
        total: shoppingList.length,
        unchecked: unchecked,
        checked: shoppingList.length - unchecked,
        by_category: byCategory
      });
    }

    if (method === "POST") {
      let bodyStr = "";
      req.on("data", chunk => { bodyStr += chunk; });
      req.on("end", () => {
        try {
          const body = JSON.parse(bodyStr || "{}");
          if (!body.item || !body.category || body.quantity === undefined) {
            return sendJSON(res, 400, { error: "item, category and quantity are required" });
          }

          const newId = generateId("shopping", "sh");
          const newItem = {
            id: newId,
            item: body.item,
            category: body.category,
            quantity: parseFloat(body.quantity) || 1,
            unit: body.unit || "pcs",
            checked: false,
            recipe_id: body.recipe_id || null,
            priority: body.priority || "medium"
          };

          shoppingList.push(newItem);
          writeCollection("shopping", shoppingList);
          sendJSON(res, 201, newItem);
        } catch (e) {
          sendJSON(res, 400, { error: "Invalid JSON input" });
        }
      });
      return;
    }

    if (method === "PUT" && id) {
      let bodyStr = "";
      req.on("data", chunk => { bodyStr += chunk; });
      req.on("end", () => {
        try {
          const body = JSON.parse(bodyStr || "{}");
          const idx = shoppingList.findIndex(i => i.id === id);
          if (idx === -1) {
            return sendJSON(res, 404, { error: "Item not found" });
          }

          const updatedItem = { ...shoppingList[idx], ...body };
          shoppingList[idx] = updatedItem;
          writeCollection("shopping", shoppingList);
          sendJSON(res, 200, updatedItem);
        } catch (e) {
          sendJSON(res, 400, { error: "Invalid JSON input" });
        }
      });
      return;
    }

    if (method === "DELETE" && id) {
      const idx = shoppingList.findIndex(i => i.id === id);
      if (idx === -1) {
        return sendJSON(res, 404, { error: "Item not found" });
      }
      const deleted = shoppingList.splice(idx, 1)[0];
      writeCollection("shopping", shoppingList);
      return sendJSON(res, 200, { message: "Item removed", deleted });
    }
  }

  // Default fallback
  sendJSON(res, 404, { error: "Endpoint not found" });
});

server.listen(PORT, () => {
  console.log(`[Shopping] Shopping Service listening on port ${PORT}...`);
});
