const http = require("http");
const url = require("url");
const { readCollection, writeCollection, generateId } = require("./db_client");

const PORT = 3005;

// Seed initial nutrition logs
const SEED_NUTRITION = [
  { id: "n1", recipe_id: "r1", date: "2026-05-25", meal_type: "breakfast", servings: 1, notes: "Delicious crispy dosa" },
  { id: "n2", recipe_id: "r2", date: "2026-05-25", meal_type: "dinner", servings: 1, notes: "With butter naan" },
  { id: "n3", recipe_id: "r5", date: "2026-05-25", meal_type: "snack", servings: 1, notes: "Afternoon refreshment" }
];

// Initialize database with seeds if empty
(async () => {
  try {
    const existing = await readCollection("nutrition");
    if (existing.length === 0) {
      console.log("[Nutrition] Seeding nutrition log datastore...");
      await writeCollection("nutrition", SEED_NUTRITION);
    }
  } catch (err) {
    console.error("[Nutrition] Seeding error:", err);
  }
})();

function sendJSON(res, status, data) {
  const body = JSON.stringify(data);
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(body),
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
  });
  res.end(body);
}

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathParts = parsedUrl.pathname.split("/").filter(Boolean);
  const method = req.method;

  console.log(`  [Nutrition] ${method} ${parsedUrl.pathname}`);

  // CORS preflight
  if (method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    });
    return res.end();
  }

  // Route: /api/nutrition or /api/nutrition/<id>
  if (pathParts[0] === "api" && pathParts[1] === "nutrition") {
    const id = pathParts[2] || null;
    const nutritionLog = await readCollection("nutrition");
    const recipes = await readCollection("recipes");

    if (method === "GET") {
      const dateFilter = parsedUrl.query.date;
      let logs = [...nutritionLog];
      if (dateFilter) {
        logs = logs.filter(l => l.date === dateFilter);
      }

      const enriched = logs.map(l => {
        const recipeDetail = recipes.find(r => r.id === l.recipe_id) || {};
        const calories = (recipeDetail.calories || 0) * l.servings;
        return {
          ...l,
          recipe_name: recipeDetail.name || "Unknown Recipe",
          calories: calories,
          cuisine: recipeDetail.cuisine || "-"
        };
      });

      const totalCalories = enriched.reduce((sum, l) => sum + l.calories, 0);

      const byDate = {};
      enriched.forEach(l => {
        if (!byDate[l.date]) {
          byDate[l.date] = { entries: [], total_calories: 0 };
        }
        byDate[l.date].entries.push(l);
        byDate[l.date].total_calories += l.calories;
      });

      return sendJSON(res, 200, {
        logs: enriched,
        total_entries: enriched.length,
        total_calories: totalCalories,
        avg_calories_per_day: Object.keys(byDate).length ? Math.round(totalCalories / Object.keys(byDate).length) : 0,
        by_date: byDate
      });
    }

    if (method === "POST") {
      let bodyStr = "";
      req.on("data", chunk => { bodyStr += chunk; });
      req.on("end", async () => {
        try {
          const body = JSON.parse(bodyStr || "{}");
          if (!body.recipe_id || body.servings === undefined) {
            return sendJSON(res, 400, { error: "recipe_id and servings are required" });
          }

          const newId = await generateId("nutrition", "n");
          const newLog = {
            id: newId,
            recipe_id: body.recipe_id,
            date: body.date || new Date().toISOString().split("T")[0],
            meal_type: body.meal_type || "lunch",
            servings: parseInt(body.servings) || 1,
            notes: body.notes || ""
          };

          nutritionLog.push(newLog);
          await writeCollection("nutrition", nutritionLog);
          sendJSON(res, 201, newLog);
        } catch (e) {
          sendJSON(res, 400, { error: "Invalid JSON input" });
        }
      });
      return;
    }

    if (method === "DELETE" && id) {
      const idx = nutritionLog.findIndex(l => l.id === id);
      if (idx === -1) {
        return sendJSON(res, 404, { error: "Log entry not found" });
      }
      const deleted = nutritionLog.splice(idx, 1)[0];
      await writeCollection("nutrition", nutritionLog);
      return sendJSON(res, 200, { message: "Log entry removed", deleted });
    }
  }

  // Default fallback
  sendJSON(res, 404, { error: "Endpoint not found" });
});

server.listen(PORT, () => {
  console.log(`[Nutrition] Nutrition Service listening on port ${PORT}...`);
});
