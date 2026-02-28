import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="AI Meal Planner",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  footer {visibility: hidden;}
  #MainMenu {visibility: hidden;}
  header {visibility: hidden;}
  [data-testid="stToolbar"] {visibility: hidden;}
  .viewerBadge_container__1QSob {display: none;}
  .styles_viewerBadge__1yB5_ {display: none;}
  #stDecoration {display: none;}
</style>
""", unsafe_allow_html=True)

from config import GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY, DIET_OPTIONS, CUISINE_OPTIONS, MEAL_TYPES, DAYS, ALLERGY_OPTIONS
from ai.recipe_agent import generate_recipe, suggest_recipes_from_ingredients
from ai.meal_planner import generate_weekly_plan
from ai.nutrition    import analyze_nutrition, analyze_weekly_nutrition
from ai.grocery      import generate_grocery_list
from database.models import (
    save_recipe, get_all_recipes, delete_recipe,
    save_meal_plan, get_all_meal_plans,
    save_grocery_list,
)

CATEGORY_ICONS = {
    "Produce": "🥦", "Proteins": "🥩", "Dairy & Eggs": "🥛",
    "Grains & Bread": "🌾", "Pantry & Spices": "🧂",
    "Frozen": "🧊", "Other": "📦",
}


# ════════════════════════════════════════════════════════════
#  CONFIG GUARD
# ════════════════════════════════════════════════════════════
def check_config():
    missing = []
    if not GROQ_API_KEY: missing.append("GROQ_API_KEY")
    if not SUPABASE_URL: missing.append("SUPABASE_URL")
    if not SUPABASE_KEY: missing.append("SUPABASE_KEY")
    if missing:
        st.error(f"⚠️ Missing environment variables: {', '.join(missing)}")
        st.code("\n".join([f"{k}=your_value_here" for k in missing]))
        if "GROQ_API_KEY" in missing:
            st.info("🔑 Get a free Groq API key at → https://console.groq.com")
        st.stop()


# ════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════
def render_sidebar() -> dict:
    st.sidebar.image("https://img.icons8.com/fluency/96/meal.png", width=64)
    st.sidebar.title("⚙️ Preferences")
    diet         = st.sidebar.selectbox("🥗 Diet Type", DIET_OPTIONS)
    cuisine      = st.sidebar.selectbox("🌍 Cuisine", CUISINE_OPTIONS)
    allergies    = st.sidebar.multiselect("⚠️ Allergies", ALLERGY_OPTIONS)
    calorie_goal = st.sidebar.slider("🔥 Daily Calorie Goal", 1000, 4000, 2000, 100)
    servings     = st.sidebar.number_input("👥 Servings", min_value=1, max_value=10, value=2)
    st.sidebar.divider()
    st.sidebar.caption("⚡ Groq (Llama 3.3 70B) + Supabase")
    return {"diet": diet, "cuisine": cuisine, "allergies": allergies,
            "calorie_goal": calorie_goal, "servings": servings}


# ════════════════════════════════════════════════════════════
#  SHARED DISPLAY HELPERS
# ════════════════════════════════════════════════════════════
def display_recipe(r: dict):
    st.divider()
    st.subheader(f"🍽️ {r['name']}")
    c1, c2, c3, c4 = st.columns(4)
    nut = r.get("nutrition") or {}
    c1.metric("⏱ Prep",     r.get("prep_time", "–"))
    c2.metric("🔥 Cook",     r.get("cook_time", "–"))
    c3.metric("👥 Servings", r.get("servings", "–"))
    c4.metric("🔥 Calories", f"{nut.get('calories', '–')} kcal")
    if r.get("tags"):
        st.write(" ".join([f"`{t}`" for t in r["tags"]]))
    col_ing, col_inst = st.columns(2)
    with col_ing:
        st.markdown("**🧂 Ingredients**")
        for i in r.get("ingredients", []):
            st.write(f"• {i.get('qty','')} — {i.get('item','')}")
    with col_inst:
        st.markdown("**📋 Instructions**")
        for idx, step in enumerate(r.get("instructions", []), 1):
            st.write(f"**{idx}.** {step}")


def display_nutrition(n: dict):
    st.divider()
    st.subheader("📊 Nutrition Analysis")
    ps = n.get("per_serving", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Calories", f"{ps.get('calories', 0)} kcal")
    c2.metric("Protein",  f"{ps.get('protein_g', 0)}g")
    c3.metric("Carbs",    f"{ps.get('carbs_g', 0)}g")
    c4.metric("Fat",      f"{ps.get('fat_g', 0)}g")
    fig = go.Figure(go.Pie(
        labels=["Protein", "Carbs", "Fat"],
        values=[ps.get("protein_g", 0), ps.get("carbs_g", 0), ps.get("fat_g", 0)],
        hole=0.4, marker_colors=["#4f46e5", "#7c3aed", "#10b981"],
    ))
    fig.update_layout(
        title="Macronutrient Distribution", height=300,
        margin=dict(t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🏅 Health Score", f"{n.get('health_score', 0)}/10")
        st.caption(n.get("health_score_reason", ""))
        if n.get("vitamins"):
            st.write("**Vitamins:** " + ", ".join(n["vitamins"]))
    with c2:
        if n.get("tips"):
            st.markdown("**💡 Nutrition Tips**")
            for t in n["tips"]:
                st.write(f"• {t}")


def display_week_nutrition(a: dict):
    st.divider()
    st.subheader("📊 Weekly Nutrition Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Daily Calories",    f"{a.get('avg_daily_calories', 0)} kcal")
    c2.metric("Weekly Total Calories", f"{a.get('weekly_total_calories', 0)} kcal")
    c3.metric("Overall Diet Score",    f"{a.get('overall_diet_score', 0)}/10")
    mb = a.get("macro_balance", {})
    fig = go.Figure(go.Pie(
        labels=["Protein", "Carbs", "Fat"],
        values=[mb.get("protein_pct", 33), mb.get("carbs_pct", 33), mb.get("fat_pct", 33)],
        hole=0.4, marker_colors=["#4f46e5", "#7c3aed", "#10b981"],
    ))
    fig.update_layout(
        title="Weekly Macro Balance", height=300,
        margin=dict(t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        if a.get("nutritional_highlights"):
            st.markdown("**✅ Highlights**")
            for h in a["nutritional_highlights"]: st.write(f"• {h}")
    with c2:
        if a.get("improvement_suggestions"):
            st.markdown("**💡 Suggestions**")
            for s in a["improvement_suggestions"]: st.write(f"• {s}")


# ════════════════════════════════════════════════════════════
#  PAGE: RECIPE GENERATOR
# ════════════════════════════════════════════════════════════
def page_recipe(prefs: dict):
    st.header("🍳 AI Recipe Generator")
    tab1, tab2 = st.tabs(["✨ Generate Recipe", "🧺 Pantry Suggestions"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            meal_type = st.selectbox("Meal Type", MEAL_TYPES)
            cuisine   = st.selectbox("Cuisine", CUISINE_OPTIONS,
                                     index=CUISINE_OPTIONS.index(prefs["cuisine"]))
        with c2:
            diet     = st.text_input("Diet Preference", value=prefs["diet"])
            servings = st.number_input("Servings", 1, 10, int(prefs["servings"]))
        ingredients = st.text_area("Ingredients you have (optional)",
                                   placeholder="e.g. chicken, garlic, tomatoes, basil")

        if st.button("🔮 Generate Recipe", type="primary", use_container_width=True):
            ph = st.empty()
            try:
                recipe = generate_recipe(meal_type, cuisine, diet,
                                         prefs["allergies"], ingredients, servings, ph)
                st.session_state["last_recipe"] = recipe
                st.session_state.pop("last_nutrition", None)
            except Exception as e:
                st.error(f"Error generating recipe: {e}")

        if "last_recipe" in st.session_state:
            r = st.session_state["last_recipe"]
            display_recipe(r)
            c_save, c_analyze = st.columns(2)
            with c_save:
                if st.button("💾 Save Recipe", use_container_width=True):
                    saved = save_recipe(r)
                    st.success(f"✅ Saved! ID: {str(saved.get('id',''))[:8]}…")
            with c_analyze:
                if st.button("📊 Analyze Nutrition", use_container_width=True):
                    with st.spinner("Analyzing…"):
                        nut = analyze_nutrition(r["name"], r["ingredients"], r["servings"])
                        st.session_state["last_nutrition"] = nut
            if "last_nutrition" in st.session_state:
                display_nutrition(st.session_state["last_nutrition"])

    with tab2:
        st.subheader("What's in your pantry?")
        pantry = st.text_area("List your available ingredients",
                              placeholder="e.g. eggs, rice, onions, chicken, soy sauce")
        if st.button("💡 Suggest Recipes", type="primary", use_container_width=True):
            with st.spinner("Finding matches…"):
                try:
                    suggestions = suggest_recipes_from_ingredients(pantry, prefs["diet"])
                    for s in suggestions:
                        with st.expander(f"🍽️ {s['name']} ({s['difficulty']}) | "
                                         f"⏱ {s['prep_time']} + {s['cook_time']}"):
                            st.write(s["brief_description"])
                            if s.get("missing_ingredients"):
                                st.warning("Missing: " + ", ".join(s["missing_ingredients"]))
                except Exception as e:
                    st.error(f"Error: {e}")


# ════════════════════════════════════════════════════════════
#  PAGE: WEEKLY MEAL PLANNER
# ════════════════════════════════════════════════════════════
def page_planner(prefs: dict):
    st.header("📅 Weekly Meal Planner")

    with st.expander("⚙️ Plan Settings", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            meals_per_day = st.multiselect("Meals per day", MEAL_TYPES,
                                           default=["Breakfast", "Lunch", "Dinner"])
            week_label = st.text_input("Week Label", value="This Week")
        with c2:
            st.info(f"**Diet:** {prefs['diet']}  \n**Cuisine:** {prefs['cuisine']}  \n"
                    f"**Calories:** {prefs['calorie_goal']} kcal/day  \n"
                    f"**Allergies:** {', '.join(prefs['allergies']) or 'None'}")

    if st.button("🔮 Generate Weekly Plan", type="primary", use_container_width=True):
        with st.spinner("Planning your week…"):
            try:
                plan = generate_weekly_plan(prefs["diet"], prefs["cuisine"],
                                            prefs["allergies"], prefs["calorie_goal"],
                                            meals_per_day)
                st.session_state.update({
                    "weekly_plan": plan,
                    "week_label": week_label,
                    "meals_per_day": meals_per_day,
                })
                st.session_state.pop("week_nutrition", None)
            except Exception as e:
                st.error(f"Error: {e}")

    if "weekly_plan" in st.session_state:
        plan = st.session_state["weekly_plan"]
        st.divider()
        st.subheader("🗓️ Your Week at a Glance")
        for day in DAYS:
            meals = plan.get(day, {})
            if not meals: continue
            with st.expander(f"📆 **{day}**", expanded=(day == DAYS[0])):
                cols = st.columns(max(len(meals), 1))
                for idx, (mtype, meal) in enumerate(meals.items()):
                    with cols[idx]:
                        st.markdown(f"**{mtype}**")
                        st.write(f"🍽️ {meal.get('name', '–')}")
                        st.caption(f"⏱ {meal.get('prep_time', '–')} | 🔥 {meal.get('calories', '–')} kcal")
                        st.caption(meal.get("brief", ""))

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("💾 Save Plan", use_container_width=True):
                saved = save_meal_plan({
                    "week_label":   st.session_state.get("week_label", "Week"),
                    "diet":         prefs["diet"],
                    "cuisine":      prefs["cuisine"],
                    "allergies":    prefs["allergies"],
                    "calorie_goal": prefs["calorie_goal"],
                    "plan":         plan,
                })
                st.session_state["saved_plan_id"] = saved.get("id")
                st.success("✅ Plan saved!")
        with c2:
            if st.button("📊 Analyze Week's Nutrition", use_container_width=True):
                with st.spinner("Analyzing…"):
                    st.session_state["week_nutrition"] = analyze_weekly_nutrition(plan)
        with c3:
            st.button("🛒 Go to Grocery List →", use_container_width=True,
                      help="Switch to Grocery List in the nav above")

        if "week_nutrition" in st.session_state:
            display_week_nutrition(st.session_state["week_nutrition"])


# ════════════════════════════════════════════════════════════
#  PAGE: GROCERY LIST
# ════════════════════════════════════════════════════════════
def page_grocery():
    st.header("🛒 Smart Grocery List")

    if "weekly_plan" not in st.session_state:
        st.info("💡 Generate a **Weekly Meal Plan** first to auto-build your grocery list.")
        return

    st.success("✅ Using your current weekly meal plan.")

    if st.button("🔮 Generate Grocery List", type="primary", use_container_width=True):
        with st.spinner("Building your smart grocery list…"):
            try:
                items = generate_grocery_list(st.session_state["weekly_plan"])
                st.session_state["grocery_items"] = items
            except Exception as e:
                st.error(f"Error: {e}")

    if "grocery_items" in st.session_state:
        items = st.session_state["grocery_items"]
        st.divider()
        st.subheader("🛍️ Your Grocery List")
        st.metric("Total Items", sum(len(v) for v in items.values()))

        for cat, ing_list in items.items():
            if not ing_list: continue
            icon = CATEGORY_ICONS.get(cat, "🛒")
            with st.expander(f"{icon} **{cat}** ({len(ing_list)} items)", expanded=True):
                for i, item in enumerate(ing_list):
                    st.checkbox(item, key=f"groc_{cat}_{i}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save Grocery List", use_container_width=True):
                plan_id = st.session_state.get("saved_plan_id")
                if plan_id:
                    save_grocery_list(plan_id, items)
                    st.success("✅ Grocery list saved!")
                else:
                    st.warning("Save the meal plan first to link the grocery list.")
        with c2:
            text = "\n".join(
                f"\n{cat}:\n" + "\n".join(f"  - {i}" for i in its)
                for cat, its in items.items()
            )
            st.download_button("📥 Download List (.txt)", data=text,
                               file_name="grocery_list.txt", mime="text/plain",
                               use_container_width=True)


# ════════════════════════════════════════════════════════════
#  PAGE: HISTORY
# ════════════════════════════════════════════════════════════
def page_history():
    st.header("📚 Saved Recipes & Meal Plans")
    tab1, tab2 = st.tabs(["🍽️ Saved Recipes", "📅 Saved Meal Plans"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        f_meal  = c1.selectbox("Meal Type", ["All"] + MEAL_TYPES)
        f_diet  = c2.selectbox("Diet", ["All", "Vegan", "Keto", "Vegetarian", "None"])
        f_query = c3.text_input("🔍 Search by name")

        filters = {}
        if f_meal != "All": filters["meal_type"] = f_meal
        if f_diet != "All": filters["diet"]      = f_diet

        recipes = get_all_recipes(filters)
        if f_query:
            recipes = [r for r in recipes if f_query.lower() in r["name"].lower()]

        if not recipes:
            st.info("No saved recipes yet.")
        else:
            st.write(f"**{len(recipes)} recipe(s) found**")
            for r in recipes:
                with st.expander(f"🍽️ {r['name']} | {r.get('meal_type','')} | {r.get('cuisine','')}"):
                    nut = r.get("nutrition") or {}
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Calories", f"{nut.get('calories', '–')} kcal")
                    c2.metric("Protein",  f"{nut.get('protein_g', '–')}g")
                    c3.metric("Prep",     r.get("prep_time", "–"))
                    c4.metric("Servings", r.get("servings", "–"))
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.markdown("**Ingredients:**")
                        for i in (r.get("ingredients") or []):
                            st.write(f"• {i.get('qty','')} {i.get('item','')}")
                        st.markdown("**Instructions:**")
                        for idx, step in enumerate(r.get("instructions") or [], 1):
                            st.write(f"**{idx}.** {step}")
                    with col_b:
                        st.caption(f"Saved: {str(r.get('created_at',''))[:10]}")
                        if st.button("🗑️ Delete", key=f"del_{r['id']}"):
                            delete_recipe(r["id"])
                            st.rerun()

    with tab2:
        plans = get_all_meal_plans()
        if not plans:
            st.info("No saved meal plans yet.")
        else:
            for p in plans:
                with st.expander(f"📅 {p['week_label']} | {p.get('diet','')} | {p.get('cuisine','')}"):
                    st.caption(f"Saved: {str(p.get('created_at',''))[:10]} | "
                               f"Calorie goal: {p.get('calorie_goal','')} kcal")
                    plan_data = p.get("plan") or {}
                    for day, meals in plan_data.items():
                        st.markdown(f"**{day}**")
                        for mtype, meal in meals.items():
                            st.write(f"  • {mtype}: {meal.get('name','–')} "
                                     f"({meal.get('calories','–')} kcal)")


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════
def main():
    check_config()
    prefs = render_sidebar()

    st.title("🍽️ AI-Enabled Recipe & Meal Planner")
    st.caption("⚡ Groq (Llama 3.3 70B) • 🗄️ Supabase • 🎨 Streamlit")

    page = st.selectbox(
        "Navigate",
        ["🍳 Recipe Generator", "📅 Weekly Meal Planner", "🛒 Grocery List", "📚 History"],
        label_visibility="collapsed",
    )
    st.divider()

    if page == "🍳 Recipe Generator":      page_recipe(prefs)
    elif page == "📅 Weekly Meal Planner": page_planner(prefs)
    elif page == "🛒 Grocery List":        page_grocery()
    elif page == "📚 History":             page_history()


if __name__ == "__main__":
    main()