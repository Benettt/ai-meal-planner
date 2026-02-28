import json, re
from ai.groq_client import stream_response, single_response

SYSTEM = """You are a professional chef and nutritionist AI.
Always respond in valid JSON only — no markdown fences, no prose outside JSON."""


def generate_recipe(
    meal_type: str, cuisine: str, diet: str,
    allergies: list, ingredients: str,
    servings: int, placeholder=None,
) -> dict:
    allergy_str = ", ".join(allergies) if allergies else "None"
    prompt = f"""
Generate a detailed recipe with:
- Meal type: {meal_type}
- Cuisine: {cuisine}
- Diet: {diet}
- Allergies to avoid: {allergy_str}
- Ingredients user has: {ingredients or 'any'}
- Servings: {servings}

Return JSON in EXACTLY this structure:
{{
  "name": "...",
  "meal_type": "{meal_type}",
  "cuisine": "{cuisine}",
  "diet": "{diet}",
  "servings": {servings},
  "prep_time": "...",
  "cook_time": "...",
  "tags": ["tag1", "tag2"],
  "ingredients": [
    {{"item": "...", "qty": "..."}}
  ],
  "instructions": ["Step 1 ...", "Step 2 ..."],
  "nutrition": {{
    "calories": 0,
    "protein_g": 0,
    "carbs_g": 0,
    "fat_g": 0,
    "fiber_g": 0
  }}
}}
"""
    raw   = stream_response(SYSTEM, prompt, placeholder)
    # Clear the streaming placeholder
    if placeholder:
        placeholder.empty()
    # Strip markdown fences and any leading/trailing whitespace
    clean = re.sub(r"```(?:json)?|```", "", raw).strip()
    # Find JSON object in case there's extra text around it
    match = re.search(r"\{.*\}", clean, re.DOTALL)
    if match:
        clean = match.group()
    return json.loads(clean)


def suggest_recipes_from_ingredients(ingredients: str, diet: str = "None") -> list:
    prompt = f"""
Given these pantry ingredients: {ingredients}
Diet preference: {diet}

Suggest 3 quick recipes. Return JSON array:
[
  {{
    "name": "...",
    "meal_type": "...",
    "prep_time": "...",
    "cook_time": "...",
    "missing_ingredients": ["..."],
    "difficulty": "Easy|Medium|Hard",
    "brief_description": "..."
  }}
]
"""
    raw   = single_response(SYSTEM, prompt)
    clean = re.sub(r"```(?:json)?|```", "", raw).strip()
    return json.loads(clean)