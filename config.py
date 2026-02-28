import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_secret(key: str) -> str:
    # First try st.secrets (Streamlit Cloud)
    try:
        val = st.secrets.get(key)
        if val:
            return val
    except Exception:
        pass
    # Then try .env (local)
    return os.getenv(key, "")

GROQ_API_KEY = get_secret("GROQ_API_KEY")
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")

GROQ_MODEL = "llama-3.3-70b-versatile"

DIET_OPTIONS = [
    "None", "Vegetarian", "Vegan", "Keto", "Paleo",
    "Gluten-Free", "Dairy-Free", "Low-Carb", "Mediterranean",
]
CUISINE_OPTIONS = [
    "Any", "Indian", "Italian", "Mexican", "Chinese",
    "Japanese", "American", "Mediterranean", "Thai", "French",
]
MEAL_TYPES      = ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"]
DAYS            = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ALLERGY_OPTIONS = ["Nuts", "Dairy", "Eggs", "Gluten", "Shellfish", "Soy", "Fish", "Sesame"]