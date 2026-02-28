import json, re
from ai.groq_client import single_response

SYSTEM = """You are a certified nutritionist AI.
Always respond with valid JSON only — no markdown, no extra text."""


def analyze_nutrition(recipe_name: str, ingredients: list[dict], servings: int) -> dict:
    ing_str = "\n".join([f"- {i['qty']} {i['item']}" for i in ingredients])
    prompt = f"""
Analyze the nutritional content for {servings} serving(s) of "{recipe_name}":

Ingredients:
{ing_str}

Return JSON:
{{
  "per_serving": {{
    "calories": 0,
    "protein_g": 0,
    "carbs_g": 0,
    "fat_g": 0,
    "fiber_g": 0,
    "sugar_g": 0,
    "sodium_mg": 0
  }},
  "vitamins": ["Vitamin A", "..."],
  "minerals": ["Iron", "..."],
  "health_score": 0,
  "health_score_reason": "...",
  "tips": ["Tip 1", "Tip 2"]
}}
health_score is 1-10 (10 = very healthy).
"""
    raw   = single_response(SYSTEM, prompt)
    clean = re.sub(r"```(?:json)?|```", "", raw).strip()
    return json.loads(clean)


def analyze_weekly_nutrition(plan: dict) -> dict:
    meals_list = []
    for day, meals in plan.items():
        for meal_type, meal in meals.items():
            meals_list.append(
                f"{day} {meal_type}: {meal.get('name','')} (~{meal.get('calories',0)} kcal)"
            )

    prompt = f"""
Given this weekly meal plan, provide a nutritional summary:

{chr(10).join(meals_list)}

Return JSON:
{{
  "avg_daily_calories": 0,
  "weekly_total_calories": 0,
  "macro_balance": {{
    "protein_pct": 0,
    "carbs_pct": 0,
    "fat_pct": 0
  }},
  "nutritional_highlights": ["..."],
  "improvement_suggestions": ["..."],
  "overall_diet_score": 0
}}
"""
    raw   = single_response(SYSTEM, prompt)
    clean = re.sub(r"```(?:json)?|```", "", raw).strip()
    return json.loads(clean)