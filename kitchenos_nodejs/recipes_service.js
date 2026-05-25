const http = require("http");
const url = require("url");
const { readCollection, writeCollection, generateId } = require("./db_client");

const PORT = 3001;

// Seed Indian vegetarian recipes
const SEED_RECIPES = [
  {
    id: "r1",
    name: "Classic Masala Dosa",
    category: "Breakfast",
    cuisine: "Indian (South)",
    prep: 15,
    cook: 20,
    servings: 2,
    difficulty: "Medium",
    calories: 380,
    ingredients: ["rice batter", "potatoes", "onions", "mustard seeds", "curry leaves", "turmeric", "ghee"],
    tags: ["breakfast", "south-indian", "veg", "crispy"],
    image_url: "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=600&q=80"
  },
  {
    id: "r2",
    name: "Paneer Butter Masala",
    category: "Curry",
    cuisine: "Indian (North)",
    prep: 15,
    cook: 25,
    servings: 4,
    difficulty: "Medium",
    calories: 450,
    ingredients: ["paneer", "butter", "tomatoes", "cashews", "cream", "garam masala", "kasuri methi"],
    tags: ["curry", "north-indian", "veg", "rich"],
    image_url: "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=600&q=80"
  },
  {
    id: "r3",
    name: "Dal Makhani",
    category: "Curry",
    cuisine: "Indian (North)",
    prep: 10,
    cook: 60,
    servings: 6,
    difficulty: "Hard",
    calories: 390,
    ingredients: ["black lentils", "kidney beans", "butter", "heavy cream", "ginger", "garlic", "tomato puree"],
    tags: ["curry", "slow-cook", "veg", "creamy"],
    image_url: "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80"
  },
  {
    id: "r4",
    name: "Aloo Gobi Matar",
    category: "Dry Curry",
    cuisine: "Indian",
    prep: 10,
    cook: 20,
    servings: 4,
    difficulty: "Easy",
    calories: 210,
    ingredients: ["potatoes", "cauliflower", "green peas", "ginger", "turmeric", "coriander powder"],
    tags: ["dry-curry", "veg", "quick", "healthy"],
    image_url: "https://images.unsplash.com/photo-1601050690597-df056fb4ce78?auto=format&fit=crop&w=600&q=80"
  },
  {
    id: "r5",
    name: "Chocolate Milkshake",
    category: "Beverage",
    cuisine: "Global",
    prep: 5,
    cook: 5,
    servings: 1,
    difficulty: "Easy",
    calories: 320,
    ingredients: ["milk", "chocolate syrup", "cocoa powder", "chocolate ice cream", "sugar"],
    tags: ["beverage", "sweet", "cold", "chocolate"],
    image_url: "https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=600&q=80"
  }
];

// Initialize database with seeds if empty
(async () => {
  try {
    const existing = await readCollection("recipes");
    if (existing.length === 0) {
      console.log("[Recipes] Seeding Indian vegetarian recipes datastore...");
      await writeCollection("recipes", SEED_RECIPES);
    }
  } catch (err) {
    console.error("[Recipes] Seeding error:", err);
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

  console.log(`  [Recipes] ${method} ${parsedUrl.pathname}`);

  // CORS preflight
  if (method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization"
    });
    return res.end();
  }

  // Route: /api/recipes or /api/recipes/<id>
  if (pathParts[0] === "api" && pathParts[1] === "recipes") {
    const id = pathParts[2] || null;
    const recipes = await readCollection("recipes");

    if (method === "GET") {
      if (id) {
        const recipe = recipes.find(r => r.id === id);
        return recipe
          ? sendJSON(res, 200, recipe)
          : sendJSON(res, 404, { error: "Recipe not found" });
      }

      let filtered = [...recipes];
      const category = parsedUrl.query.category;
      const tag = parsedUrl.query.tag;

      if (category) {
        filtered = filtered.filter(r => r.category.toLowerCase() === category.toLowerCase());
      }
      if (tag) {
        filtered = filtered.filter(r => r.tags.includes(tag));
      }

      const categories = [...new Set(filtered.map(r => r.category))];
      return sendJSON(res, 200, { recipes: filtered, total: filtered.length, categories });
    }

    if (method === "POST") {
      let bodyStr = "";
      req.on("data", chunk => { bodyStr += chunk; });
      req.on("end", async () => {
        try {
          const body = JSON.parse(bodyStr || "{}");
          if (!body.name || !body.category) {
            return sendJSON(res, 400, { error: "Name and Category are required" });
          }

          const newId = await generateId("recipes", "r");
          const newRecipe = {
            id: newId,
            name: body.name,
            category: body.category,
            cuisine: body.cuisine || "Indian",
            prep: parseInt(body.prep) || 10,
            cook: parseInt(body.cook) || 10,
            servings: parseInt(body.servings) || 2,
            difficulty: body.difficulty || "Easy",
            calories: parseInt(body.calories) || 200,
            ingredients: Array.isArray(body.ingredients) ? body.ingredients : [],
            tags: Array.isArray(body.tags) ? body.tags : ["veg"],
            image_url: body.image_url || "https://images.unsplash.com/photo-1495521821757-a1efb6729352?auto=format&fit=crop&w=600&q=80"
          };

          recipes.push(newRecipe);
          await writeCollection("recipes", recipes);
          sendJSON(res, 201, newRecipe);
        } catch (e) {
          sendJSON(res, 400, { error: "Invalid JSON input" });
        }
      });
      return;
    }

    if (method === "DELETE" && id) {
      const idx = recipes.findIndex(r => r.id === id);
      if (idx === -1) {
        return sendJSON(res, 404, { error: "Recipe not found" });
      }
      const deleted = recipes.splice(idx, 1)[0];
      await writeCollection("recipes", recipes);
      return sendJSON(res, 200, { message: "Recipe removed", deleted });
    }
  }

  // Default fallback
  sendJSON(res, 404, { error: "Endpoint not found" });
});

server.listen(PORT, () => {
  console.log(`[Recipes] Recipes Service listening on port ${PORT}...`);
});
