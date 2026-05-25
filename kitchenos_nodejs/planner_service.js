const http = require("http");
const url = require("url");
const { readCollection, writeCollection, generateId } = require("./db_client");

const PORT = 3003;

// Seed initial meal plans matching our Indian veg recipes
const SEED_MEAL_PLANS = [
  { id: "m1", recipe_id: "r1", date: "2026-05-25", meal_type: "breakfast", servings: 2, notes: "South Indian breakfast" },
  { id: "m2", recipe_id: "r2", date: "2026-05-25", meal_type: "dinner", servings: 4, notes: "Special Paneer dinner" },
  { id: "m3", recipe_id: "r4", date: "2026-05-26", meal_type: "lunch", servings: 4, notes: "Quick Aloo Gobi lunch" }
];

// Initialize database with seeds if empty
(async () => {
  try {
    const existing = await readCollection("planner");
    if (existing.length === 0) {
      console.log("[Planner] Seeding meal planner datastore...");
      await writeCollection("planner", SEED_MEAL_PLANS);
    }
  } catch (err) {
    console.error("[Planner] Seeding error:", err);
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

  console.log(`  [Planner] ${method} ${parsedUrl.pathname}`);

  // CORS preflight
  if (method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    });
    return res.end();
  }

  // Route: /api/planner or /api/planner/<id>
  if (pathParts[0] === "api" && pathParts[1] === "planner") {
    const id = pathParts[2] || null;
    const plans = await readCollection("planner");
    const recipes = await readCollection("recipes");

    if (method === "GET") {
      if (id) {
        const m = plans.find(p => p.id === id);
        if (!m) {
          return sendJSON(res, 404, { error: "Meal plan entry not found" });
        }
        const recipeDetail = recipes.find(r => r.id === m.recipe_id) || null;
        return sendJSON(res, 200, { ...m, recipe: recipeDetail });
      }

      // Filter by date
      const dateFilter = parsedUrl.query.date;
      let filtered = [...plans];
      if (dateFilter) {
        filtered = filtered.filter(p => p.date === dateFilter);
      }

      // Enrich with recipe details
      const enriched = filtered.map(p => {
        const recipeDetail = recipes.find(r => r.id === p.recipe_id) || null;
        return { ...p, recipe: recipeDetail };
      });

      // Group by date
      const byDate = {};
      enriched.forEach(p => {
        if (!byDate[p.date]) byDate[p.date] = [];
        byDate[p.date].push(p);
      });

      const totalCalories = enriched.reduce((sum, p) => {
        const kcal = p.recipe ? (p.recipe.calories || 0) : 0;
        return sum + (kcal * p.servings);
      }, 0);

      return sendJSON(res, 200, {
        plans: enriched,
        total: enriched.length,
        by_date: byDate,
        total_calories_planned: totalCalories
      });
    }

    if (method === "POST") {
      let bodyStr = "";
      req.on("data", chunk => { bodyStr += chunk; });
      req.on("end", async () => {
        try {
          const body = JSON.parse(bodyStr || "{}");
          if (!body.recipe_id || !body.date || !body.meal_type || body.servings === undefined) {
            return sendJSON(res, 400, { error: "recipe_id, date, meal_type and servings are required" });
          }

          const newId = await generateId("planner", "m");
          const newPlan = {
            id: newId,
            recipe_id: body.recipe_id,
            date: body.date,
            meal_type: body.meal_type,
            servings: parseInt(body.servings) || 1,
            notes: body.notes || ""
          };

          plans.push(newPlan);
          await writeCollection("planner", plans);

          const recipeDetail = recipes.find(r => r.id === newPlan.recipe_id) || null;
          sendJSON(res, 201, { ...newPlan, recipe: recipeDetail });
        } catch (e) {
          sendJSON(res, 400, { error: "Invalid JSON input" });
        }
      });
      return;
    }

    if (method === "DELETE" && id) {
      const idx = plans.findIndex(p => p.id === id);
      if (idx === -1) {
        return sendJSON(res, 404, { error: "Meal plan entry not found" });
      }
      const deleted = plans.splice(idx, 1)[0];
      await writeCollection("planner", plans);
      return sendJSON(res, 200, { message: "Plan entry removed", deleted });
    }
  }

  // Default fallback
  sendJSON(res, 404, { error: "Endpoint not found" });
});

server.listen(PORT, () => {
  console.log(`[Planner] Planner Service listening on port ${PORT}...`);
});
