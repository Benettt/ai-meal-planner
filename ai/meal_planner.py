import json, re
from ai.groq_client import single_response

SYSTEM = """You are an expert meal planning AI and dietitian.
Always respond with valid JSON only — no markdown, no extra text."""


def generate_weekly_plan(
    diet: str,
    cuisine: str,
    allergies: list[str],
    calorie_goal: int,
    meals_per_day: list[str],
) -> dict:
    allergy_str = ", ".join(allergies) if allergies else "None"
    meals_str   = ", ".join(meals_per_day)

    prompt = f"""
Create a full 7-day meal plan with:
- Diet: {diet}
- Preferred cuisine: {cuisine}
- Allergies to avoid: {allergy_str}
- Daily calorie goal: {calorie_goal} kcal
- Meals per day: {meals_str}

Return a JSON object like:
{{
  "Monday": {{
    "Breakfast": {{
      "name": "...",
      "calories": 0,
      "prep_time": "...",
      "brief": "..."
    }},
    "Lunch": {{ ... }},
    "Dinner": {{ ... }}
  }},
  "Tuesday": {{ ... }},
  ... (all 7 days)
}}

Each meal must include: name, calories, prep_time, brief (1-sentence description).
"""
    raw   = single_response(SYSTEM, prompt)
    clean = re.sub(r"```(?:json)?|```", "", raw).strip()
    return json.loads(clean)