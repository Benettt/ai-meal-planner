from database.supabase_client import get_client


# ═══════════════════════════════════════════════
#  RECIPES
# ═══════════════════════════════════════════════

def save_recipe(recipe: dict) -> dict:
    db = get_client()
    resp = db.table("recipes").insert(recipe).execute()
    return resp.data[0] if resp.data else {}


def get_all_recipes(filters: dict = None) -> list:
    db = get_client()
    q = db.table("recipes").select("*").order("created_at", desc=True)
    if filters:
        if filters.get("meal_type"):
            q = q.eq("meal_type", filters["meal_type"])
        if filters.get("diet"):
            q = q.eq("diet", filters["diet"])
        if filters.get("cuisine"):
            q = q.eq("cuisine", filters["cuisine"])
    return q.execute().data or []


def get_recipe_by_id(recipe_id: str) -> dict:
    db = get_client()
    resp = db.table("recipes").select("*").eq("id", recipe_id).single().execute()
    return resp.data or {}


def delete_recipe(recipe_id: str):
    db = get_client()
    db.table("recipes").delete().eq("id", recipe_id).execute()


# ═══════════════════════════════════════════════
#  MEAL PLANS
# ═══════════════════════════════════════════════

def save_meal_plan(plan_data: dict) -> dict:
    db = get_client()
    resp = db.table("meal_plans").insert(plan_data).execute()
    return resp.data[0] if resp.data else {}


def get_all_meal_plans() -> list:
    db = get_client()
    return db.table("meal_plans").select("*").order("created_at", desc=True).execute().data or []


def get_meal_plan_by_id(plan_id: str) -> dict:
    db = get_client()
    resp = db.table("meal_plans").select("*").eq("id", plan_id).single().execute()
    return resp.data or {}


# ═══════════════════════════════════════════════
#  GROCERY LISTS
# ═══════════════════════════════════════════════

def save_grocery_list(meal_plan_id: str, items: dict) -> dict:
    db = get_client()
    resp = db.table("grocery_lists").insert({
        "meal_plan_id": meal_plan_id,
        "items": items,
    }).execute()
    return resp.data[0] if resp.data else {}


def get_grocery_list_by_plan(meal_plan_id: str) -> dict:
    db = get_client()
    resp = db.table("grocery_lists").select("*").eq("meal_plan_id", meal_plan_id).execute()
    return resp.data[0] if resp.data else {}