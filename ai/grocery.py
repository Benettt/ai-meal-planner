import json, re
from ai.groq_client import single_response

SYSTEM = """You are a smart grocery planning assistant.
Always respond with valid JSON only — no markdown, no extra text."""


def generate_grocery_list(weekly_plan: dict) -> dict:
    meals_list = []
    for day, meals in weekly_plan.items():
        for meal_type, meal in meals.items():
            meals_list.append(f"{day} {meal_type}: {meal.get('name', '')}")

    prompt = f"""
Generate a consolidated grocery list for this weekly meal plan:

{chr(10).join(meals_list)}

Combine duplicates, estimate quantities for 2 people.
Categorize into sections.

Return JSON:
{{
  "Produce": ["2 lbs spinach", "3 tomatoes", "..."],
  "Proteins": ["500g chicken breast", "..."],
  "Dairy & Eggs": ["1 dozen eggs", "..."],
  "Grains & Bread": ["1 loaf whole wheat bread", "..."],
  "Pantry & Spices": ["olive oil", "cumin", "..."],
  "Frozen": ["..."],
  "Other": ["..."]
}}
"""
    raw   = single_response(SYSTEM, prompt)
    clean = re.sub(r"```(?:json)?|```", "", raw).strip()
    return json.loads(clean)