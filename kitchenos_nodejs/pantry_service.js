const http = require("http");
const url = require("url");
const { readCollection, writeCollection, generateId } = require("./db_client");

const PORT = 3002;

// Seed Indian pantry items
const SEED_PANTRY = [
  { id: "p1", name: "Basmati Rice", category: "Grains", quantity: 1500, unit: "g", min_quantity: 500, expiry: "2026-12-31" },
  { id: "p2", name: "Paneer Block", category: "Dairy", quantity: 400, unit: "g", min_quantity: 200, expiry: "2026-06-15" },
  { id: "p3", name: "Toor Dal", category: "Lentils", quantity: 1000, unit: "g", min_quantity: 400, expiry: "2026-12-31" },
  { id: "p4", name: "Mustard Seeds", category: "Spices", quantity: 150, unit: "g", min_quantity: 50, expiry: "2027-01-01" },
  { id: "p5", name: "Pure Ghee", category: "Fats", quantity: 500, unit: "ml", min_quantity: 200, expiry: "2026-09-30" },
  { id: "p6", name: "Fresh Tomatoes", category: "Produce", quantity: 800, unit: "g", min_quantity: 400, expiry: "2026-05-30" },
  { id: "p7", name: "Ginger-Garlic Paste", category: "Condiments", quantity: 150, unit: "g", min_quantity: 50, expiry: "2026-08-15" }
];

// Initialize database with seeds if empty
(async () => {
  try {
    const existing = await readCollection("pantry");
    if (existing.length === 0) {
      console.log("[Pantry] Seeding Indian pantry items datastore...");
      await writeCollection("pantry", SEED_PANTRY);
    }
  } catch (err) {
    console.error("[Pantry] Seeding error:", err);
  }
})();

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

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathParts = parsedUrl.pathname.split("/").filter(Boolean);
  const method = req.method;

  console.log(`  [Pantry] ${method} ${parsedUrl.pathname}`);

  // CORS preflight
  if (method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    });
    return res.end();
  }

  // Route: /api/pantry or /api/pantry/<id>
  if (pathParts[0] === "api" && pathParts[1] === "pantry") {
    const id = pathParts[2] || null;
    const pantry = await readCollection("pantry");

    if (method === "GET") {
      if (id) {
        const item = pantry.find(i => i.id === id);
        return item
          ? sendJSON(res, 200, item)
          : sendJSON(res, 404, { error: "Pantry item not found" });
      }

      const today = new Date().toISOString().split("T")[0];
      const expiryWarningDate = new Date(Date.now() + 7 * 86400000).toISOString().split("T")[0]; // 7 days from now

      const enriched = pantry.map(item => ({
        ...item,
        low_stock: item.quantity <= item.min_quantity,
        expired: item.expiry < today,
        expiring_soon: item.expiry >= today && item.expiry <= expiryWarningDate
      }));

      return sendJSON(res, 200, {
        items: enriched,
        total: enriched.length,
        low_stock: enriched.filter(i => i.low_stock).length,
        expiring_soon: enriched.filter(i => i.expiring_soon).length,
        expired: enriched.filter(i => i.expired).length
      });
    }

    if (method === "POST") {
      let bodyStr = "";
      req.on("data", chunk => { bodyStr += chunk; });
      req.on("end", async () => {
        try {
          const body = JSON.parse(bodyStr || "{}");
          if (!body.name || !body.category || body.quantity === undefined) {
            return sendJSON(res, 400, { error: "Name, Category and Quantity are required" });
          }

          const newId = await generateId("pantry", "p");
          const newItem = {
            id: newId,
            name: body.name,
            category: body.category,
            quantity: parseFloat(body.quantity) || 0,
            unit: body.unit || "units",
            min_quantity: parseFloat(body.min_quantity) || 0,
            expiry: body.expiry || new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0] // default 30 days
          };

          pantry.push(newItem);
          await writeCollection("pantry", pantry);
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
      req.on("end", async () => {
        try {
          const body = JSON.parse(bodyStr || "{}");
          const idx = pantry.findIndex(i => i.id === id);
          if (idx === -1) {
            return sendJSON(res, 404, { error: "Item not found" });
          }

          const updatedItem = { ...pantry[idx], ...body };
          pantry[idx] = updatedItem;
          await writeCollection("pantry", pantry);
          sendJSON(res, 200, updatedItem);
        } catch (e) {
          sendJSON(res, 400, { error: "Invalid JSON input" });
        }
      });
      return;
    }

    if (method === "DELETE" && id) {
      const idx = pantry.findIndex(i => i.id === id);
      if (idx === -1) {
        return sendJSON(res, 404, { error: "Item not found" });
      }
      const deleted = pantry.splice(idx, 1)[0];
      await writeCollection("pantry", pantry);
      return sendJSON(res, 200, { message: "Item removed", deleted });
    }
  }

  // Default fallback
  sendJSON(res, 404, { error: "Endpoint not found" });
});

server.listen(PORT, () => {
  console.log(`[Pantry] Pantry Service listening on port ${PORT}...`);
});
