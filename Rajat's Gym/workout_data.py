# # app.py
# import sqlite3
# from datetime import datetime
# from functools import wraps

# from flask import (
#     Flask, render_template, request,
#     redirect, session, jsonify
# )

# # ---------------- BASIC FLASK SETUP ----------------

# app = Flask(__name__)
# app.secret_key = "super_gym_secret_key"   # change in production

# DB_NAME = "gym.db"


# # ---------------- DATABASE HELPERS -----------------

# def connect():
#     """Return sqlite connection."""
#     return sqlite3.connect(DB_NAME, check_same_thread=False)


# def init_db():
#     """Create required tables if they don't exist."""
#     conn = connect()
#     cur = conn.cursor()

#     # Users table
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         name TEXT NOT NULL,
#         email TEXT UNIQUE NOT NULL,
#         password TEXT NOT NULL,
#         age INTEGER,
#         weight REAL,
#         height REAL
#     );
#     """)

#     # Progress table (weight log)
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS progress (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         user_id INTEGER NOT NULL,
#         weight REAL NOT NULL,
#         date TEXT NOT NULL,
#         FOREIGN KEY(user_id) REFERENCES users(id)
#     );
#     """)

#     conn.commit()
#     conn.close()


# # Call at start
# init_db()


# # ------------- LOGIN REQUIRED DECORATOR ------------

# def login_required(fn):
#     @wraps(fn)
#     def wrapper(*args, **kwargs):
#         if "user_id" not in session:
#             return redirect("/login")
#         return fn(*args, **kwargs)
#     return wrapper


# # ---------------- AUTH ROUTES ----------------------

# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         name = request.form["name"].strip()
#         email = request.form["email"].strip()
#         password = request.form["password"].strip()

#         conn = connect()
#         cur = conn.cursor()
#         try:
#             cur.execute(
#                 "INSERT INTO users(name,email,password) VALUES(?,?,?)",
#                 (name, email, password)
#             )
#             conn.commit()
#         except Exception as e:
#             conn.close()
#             return f"Error while registering: {e}"
#         conn.close()
#         return redirect("/login")

#     return render_template("register.html")

# # ---------------- LOGIN ROUTE ----------------------

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     msg = None
#     if request.method == "POST":
#         email = request.form["email"].strip()
#         pwd = request.form["password"].strip()

#         conn = connect()
#         cur = conn.cursor()
#         cur.execute("SELECT id, name FROM users WHERE email=? AND password=?",
#                     (email, pwd))
#         user = cur.fetchone()
#         conn.close()

#         if user:
#             session["user_id"] = user[0]
#             session["user_name"] = user[1]
#             return redirect("/")
#         else:
#             msg = "❌ Invalid email or password"

#     return render_template("login.html", msg=msg)


# @app.route("/logout")
# def logout():
#     session.clear()
#     return redirect("/login")


# # ---------------- HOME / HERO ----------------------

# @app.route("/")
# @login_required
# def home():
#     return render_template("index.html", username=session.get("user_name"))


# # ---------------- WORKOUT DIAGNOSIS ----------------

# def get_workout_plan(goal):
#     """Return list of workout lines based on goal keyword."""
#     plans = {
#         "fat_loss": [
#             "Day 1: Full Body HIIT (20–30 min)",
#             "Day 2: Brisk Walk + Core Work",
#             "Day 3: Upper Body Dumbbells",
#             "Day 4: Rest / Mobility",
#             "Day 5: Cardio + Abs",
#             "Day 6: Lower Body Strength",
#             "Day 7: Light Walk / Yoga"
#         ],
#         "muscle_gain": [
#             "Day 1: Chest + Triceps",
#             "Day 2: Back + Biceps",
#             "Day 3: Heavy Legs",
#             "Day 4: Shoulders + Abs",
#             "Day 5: Full Upper Body Pump",
#             "Day 6: Legs + Glutes",
#             "Day 7: Rest / Stretch"
#         ],
#         "strength": [
#             "Day 1: Squats + Core",
#             "Day 2: Bench Press + Push Movements",
#             "Day 3: Deadlifts + Posterior Chain",
#             "Day 4: Overhead Press + Pull-ups",
#             "Day 5: Farmer Walk / Carries",
#             "Day 6–7: Rest / Mobility"
#         ],
#         "beginner": [
#             "Day 1: Full Body (Bodyweight)",
#             "Day 2: Walk 30 mins",
#             "Day 3: Full Body (Light Dumbbells)",
#             "Day 4: Rest",
#             "Day 5: Full Body (Repeat)",
#             "Day 6: Walk + Core",
#             "Day 7: Rest"
#         ],
#         "home": [
#             "Pushups / Incline Pushups",
#             "Bodyweight Squats",
#             "Glute Bridges",
#             "Plank 3 x 30 sec",
#             "Mountain Climbers",
#             "Skipping / High Knees (10–15 min)"
#         ]
#     }
#     return plans.get(goal, [])

# # ------------- WORKOUT RECOMMENDATION --------------

# @app.route("/workout", methods=["GET", "POST"])
# @login_required
# def workout():
#     plan = None
#     goal = None
#     if request.method == "POST":
#         goal = request.form.get("goal")
#         plan = get_workout_plan(goal)
#     return render_template("workout.html", goal=goal, plan=plan)


# # ------------- DIET RECOMMENDATION -----------------

# def get_diet_plan(dtype):
#     """Return diet plan list based on diet type."""
#     if dtype == "veg":
#         return [
#             "Breakfast: Oats + Milk + Banana",
#             "Mid: Sprouts Salad",
#             "Lunch: 2 Roti + Dal + Sabzi + Curd",
#             "Snack: Fruit + Nuts",
#             "Dinner: Paneer / Soya + Salad"
#         ]
#     if dtype == "nonveg":
#         return [
#             "Breakfast: Eggs + Toast + Fruit",
#             "Mid: Yogurt + Nuts",
#             "Lunch: Chicken + Rice + Veggies",
#             "Snack: Whey / Milk + Fruit",
#             "Dinner: Fish / Chicken + Salad"
#         ]
#     if dtype == "fast_fatloss":
#         return [
#             "Low-carb Breakfast (Egg/Oats)",
#             "No sugar drinks / No cold drinks",
#             "High protein each meal",
#             "Evening: Green tea + nuts",
#             "Night: Light dinner (soup/salad + protein)"
#         ]
#     if dtype == "high_protein":
#         return [
#             "Every meal: 20–30g protein",
#             "Include Paneer/Tofu/Eggs/Chicken",
#             "Add Greek Yogurt / Curd daily",
#             "Nuts & Seeds between meals"
#         ]
#     if dtype == "budget":
#         return [
#             "Chana, Rajma, Dal as main protein",
#             "Seasonal fruits only",
#             "Simple roti + sabzi + dal pattern",
#             "Avoid packaged food & cold drinks"
#         ]
#     return []

# # ------------- DIET RECOMMENDATION ROUTE -------------

# @app.route("/diet", methods=["GET", "POST"])
# @login_required
# def diet():
#     dtype = None
#     plan = None
#     if request.method == "POST":
#         dtype = request.form.get("diet_type")
#         plan = get_diet_plan(dtype)
#     return render_template("diet.html", dtype=dtype, plan=plan)


# # ------------- AI STYLE WEEKLY PLANNER -------------

# def calculate_bmi(weight, height_cm):
#     try:
#         h_m = height_cm / 100
#         bmi = weight / (h_m * h_m)
#     except Exception:
#         return None, None

#     if bmi < 18.5:
#         status = "Underweight"
#     elif bmi < 25:
#         status = "Healthy"
#     elif bmi < 30:
#         status = "Overweight"
#     else:
#         status = "Obese"
#     return round(bmi, 1), status

# # ------------- WEEKLY PLANNER ROUTE -----------------

# @app.route("/planner", methods=["GET", "POST"])
# @login_required
# def planner():
#     info = None
#     if request.method == "POST":
#         try:
#             weight = float(request.form["weight"])
#             height = float(request.form["height"])
#         except ValueError:
#             weight = height = 0.0

#         bmi, status = calculate_bmi(weight, height)
#         if bmi is not None:
#             if status == "Underweight":
#                 cal = "2200–2600 kcal/day"
#                 protein = "1.6–2g per kg bodyweight"
#             elif status == "Healthy":
#                 cal = "2000–2400 kcal/day"
#                 protein = "1.4–1.8g per kg"
#             elif status == "Overweight":
#                 cal = "1500–1900 kcal/day (fat loss focus)"
#                 protein = "1.6–2g per kg"
#             else:
#                 cal = "1400–1700 kcal/day (strict fat loss)"
#                 protein = "1.8–2.2g per kg"

#             water = "3–4 Litres / day"

#             info = {
#                 "bmi": bmi,
#                 "status": status,
#                 "calories": cal,
#                 "protein": protein,
#                 "water": water
#             }

#     return render_template("planner.html", info=info)


# # ------------- PROGRESS TRACKER (GRAPH) -----------

# @app.route("/tracker", methods=["GET", "POST"])
# @login_required
# def tracker():
#     uid = session["user_id"]
#     conn = connect()
#     cur = conn.cursor()

#     if request.method == "POST":
#         try:
#             weight = float(request.form["weight"])
#         except ValueError:
#             weight = None

#         if weight:
#             today = datetime.today().strftime("%Y-%m-%d")
#             cur.execute(
#                 "INSERT INTO progress(user_id,weight,date) VALUES(?,?,?)",
#                 (uid, weight, today)
#             )
#             conn.commit()

#     cur.execute(
#         "SELECT date, weight FROM progress WHERE user_id=? ORDER BY date",
#         (uid,)
#     )
#     rows = cur.fetchall()
#     conn.close()

#     dates = [r[0] for r in rows]
#     weights = [r[1] for r in rows]

#     return render_template("tracker.html", dates=dates, weights=weights)


# # ------------- MOTIVATIONAL QUOTES API ------------

# @app.route("/quotes")
# def quotes():
#     data = [
#         "Push yourself because no one else is going to do it for you.",
#         "One more rep. Always.",
#         "Your body can stand almost anything. It’s your mind you have to convince.",
#         "Small progress is still progress.",
#         "Discipline over motivation.",
#         "Sweat is just fat crying."
#     ]
#     return jsonify(data)

# # ------------- MOTIVATION PAGE ---------------------

# @app.route("/motivation")
# @login_required
# def motivation():
#     return render_template("quotes.html")

# # ------------- MEET THE TRAINERS PAGE --------------

# @app.route("/trainer-ai", methods=["GET", "POST"])
# @login_required
# def trainer_ai():
    
#     if request.method == "POST":
        
#         goal = request.form.get("goal")
#         level = request.form.get("level")
#         body = request.form.get("body")

#         plans = {
#             "fatloss": ["HIIT Circuit 20min", "Battle Ropes", "Skipping 1000 reps", "Treadmill run 15min"],
#             "muscle": ["Heavy Bench Press 5x5", "Deadlift 4x6", "Barbell Squat 4x8", "Dumbbell Row 4x10"],
#             "strength": ["Low reps Heavy Squat", "Farmer Walk 3 rounds", "Sled Push", "Rack Pulls"],
#             "beginner": ["Push-ups 3x10", "Squats 3x15", "Plank 30 sec x3", "Light Dumbbell Shoulder Press"],
#             "home": ["Burpees 3x15", "Jumping Jacks 50x3", "Push-ups", "Mountain Climbers 30sec"]
#         }
        
#         trainer_output = plans.get(goal, [])
        
#         return render_template("trainer_ai.html",
#                                goal=goal,
#                                level=level,
#                                body=body,
#                                workout=trainer_output)

#     return render_template("trainer_ai.html", workout=None)


# # ================= STRENGTH TEST =================

# def evaluate_strength(pushups, squats, plank):
#     score = 0

#     # Pushups (Max considered = 40)
#     score += min(pushups, 40) * 0.4 

#     # Squats (Max considered = 60)
#     score += min(squats, 60) * 0.3

#     # Plank seconds (Max considered = 120 sec)
#     score += min(plank, 120) * 0.3
    
#     percentage = round(score, 2)

#     if percentage < 40:
#         level = "Beginner 🟢"
#     elif percentage < 75:
#         level = "Intermediate 🟡"
#     else:
#         level = "Beast Mode 🔥"

#     return percentage, level

# # ------------- STRENGTH TEST ROUTE -----------------

# @app.route("/strength", methods=["GET","POST"])
# @login_required
# def strength():
#     result = None
#     if request.method == "POST":
#         pushups = int(request.form["pushups"])
#         squats  = int(request.form["squats"])
#         plank   = int(request.form["plank"])
        
#         result = evaluate_strength(pushups, squats, plank)

#     return render_template("strength.html", result=result)

# # ================= AI Diet Generator =================
# @app.route("/diet_ai", methods=["GET", "POST"])
# @login_required
# def diet_ai():
#     if request.method == "POST":
#         goal = request.form.get("goal")

#         diet_plan = {
#             "fatloss": ["🥣 Oats + Apple + Green Tea", "🥗 Roti + Dal + Salad", "🍎 Fruits + Makhana", "🥦 Veg Soup Dinner"],
#             "muscle": ["🍳 Eggs + Milk", "🍚 Rice + Chicken/Panner", "🥤 Banana + Whey", "🍽 High Protein Dinner"],
#             "strength": ["🍳 6-8 Eggs", "🥔 Rice + Sweet Potato", "🍗 Chicken + Nuts", "🥛 Milk at Bedtime"]
#         }

#         return render_template("diet_ai.html", plan=diet_plan.get(goal), goal=goal)
#     return render_template("diet_ai.html", plan=None)



# # ================= Calories + Protein Calculator =================

# @app.route("/calorie_calc", methods=["GET","POST"])
# @login_required
# def calorie_calc():

#     if request.method == "POST":
#         weight = float(request.form['weight'])

#         # Height Input Mode
#         mode = request.form['mode']

#         # --- CM Input ---
#         if mode == "cm":
#             height_cm = float(request.form['height_cm'])
#             height_m = height_cm / 100   # convert → meters

#         # --- FEET + INCH Input ---
#         else:
#             feet = float(request.form['height_ft'])
#             inch = float(request.form['height_in'])
#             height_m = ((feet * 12) + inch) * 0.0254   # convert → meters

#         # CALCULATIONS
#         bmi = round(weight / (height_m * height_m), 2)
#         calories = round(weight * 30)        # avg maintenance kcal
#         protein = round(weight * 1.8)        # athlete recommended (gm/day)

#         return render_template("calorie_calc.html",
#                                bmi=bmi, cal=calories, pro=protein,
#                                weight=weight)
    
#     return render_template("calorie_calc.html")


# # ================= Weekly Workout Chart =================
# @app.route("/weekly_plan")
# @login_required
# def weekly_plan():
#     level = request.args.get("level", session.get("level", "beginner"))

#     # SAVE user preference
#     session["level"] = level  

#     # Titles visible on cards
#     week_titles = {
#         "Monday": "Chest + Triceps",
#         "Tuesday": "Back + Biceps",
#         "Wednesday": "Leg Strength",
#         "Thursday": "Shoulders + Abs",
#         "Friday": "Upper Body Pump",
#         "Saturday": "HIIT + Core",
#         "Sunday": "Recovery & Stretch"
#     }

#     # Full exercises for modal
#     plans = {
#         "beginner": {
#     "Monday": [
#         "Pushups – 3×10",
#         "Incline Pushups – 3×12",
#         "Bodyweight Squats – 3×15",
#         "Glute Bridge – 3×15",
#         "Plank – 30 sec",
#         "Dumbbell Chest Press (if available) – 3×12"
#     ],

#     "Tuesday": [
#         "Brisk Walk – 20–30 min",
#         "Arm Circles – 2×20",
#         "Hip Mobility Routine – 5 min",
#         "Child Pose Stretch – 40 sec",
#         "Hamstring Stretch – 40 sec"
#     ],

#     "Wednesday": [
#         "Dumbbell Shoulder Press – 3×12",
#         "One-Arm Dumbbell Row – 3×12 each side",
#         "Bicep Curl – 3×12",
#         "Tricep Dips on chair – 3×12",
#         "Reverse Snow Angels – 3×15",
#         "Front Raise (Light DB) – 3×12"
#     ],

#     "Thursday": [
#         "Rest Day + Light Activity",
#         "Cat-Cow Stretch – 10 reps",
#         "Cobra Stretch – 40 sec",
#         "Neck Mobility – 10 reps",
#         "Shoulder Stretch – 30 sec"
#     ],

#     "Friday": [
#         "Lunges – 3×12",
#         "Sumo Squats – 3×15",
#         "Glute Kickback – 3×15",
#         "Calf Raises – 3×20",
#         "Wall Sit – 30 sec",
#         "Hip Thrust – 3×12",
#         "Side Leg Raises – 3×15"
#     ],

#     "Saturday": [
#         "Low Intensity Jog – 5 min",
#         "Mountain Climbers – 3×20",
#         "Crunches – 3×15",
#         "Leg Raises – 3×12",
#         "Russian Twist – 3×20",
#         "Bicycle Crunch – 3×15"
#     ],

#     "Sunday": [
#         "Yoga Flow – 10 min",
#         "Deep Breathing – 5 min",
#         "Ankle Mobility – 10 reps",
#         "Full Body Stretch – 5 min"
#     ]
# },

        

#         "intermediate": {
#     "Monday": [
#         "Bench Press – 4×8",
#         "Incline Dumbbell Press – 4×10",
#         "Pushups – 3×15",
#         "Chest Fly (DB) – 3×12",
#         "Tricep Dips – 3×12",
#         "Overhead Tricep Extension – 3×12"
#     ],

#     "Tuesday": [
#         "Pull-Ups / Assisted – 3×8",
#         "Lat Pulldown – 4×10",
#         "One-Arm Dumbbell Row – 3×12 each side",
#         "Seated Row – 3×12",
#         "Bicep Curl – 3×12",
#         "Hammer Curl – 3×10"
#     ],

#     "Wednesday": [
#         "Barbell Squat – 4×8",
#         "Dumbbell Lunges – 3×12",
#         "Leg Press – 4×12",
#         "Romanian Deadlift – 3×10",
#         "Calf Raises – 4×20",
#         "Glute Bridge – 3×15"
#     ],

#     "Thursday": [
#         "Shoulder Press – 4×10",
#         "Lateral Raise – 3×15",
#         "Front Raise – 3×12",
#         "Reverse Fly – 3×12",
#         "Plank – 45 sec",
#         "Hanging Knee Raise – 3×12"
#     ],

#     "Friday": [
#         "Upper Body Circuit",
#         "Pushups – 20 reps",
#         "Bent Over Row – 15 reps",
#         "Arnold Press – 12 reps",
#         "Curls – 12 reps",
#         "Repeat circuit × 3"
#     ],

#     "Saturday": [
#         "HIIT: 20s ON / 20s OFF × 10 rounds",
#         "Mountain Climbers",
#         "Jump Squats",
#         "Burpees",
#         "High Knees",
#         "Core Finisher: Leg Raises – 3×12"
#     ],

#     "Sunday": [
#         "Recovery Walk – 20 min",
#         "Full Body Stretch – 10 min",
#         "Foam Roll (if available) – 5 min",
#         "Light Yoga Flow – 8 min"
#     ]
# },

#        "advanced": {
#     "Monday": [
#         "Heavy Bench Press – 5×5",
#         "Weighted Dips – 4×6",
#         "Incline Barbell Press – 4×8",
#         "Cable Fly – 3×12",
#         "Close-Grip Bench – 3×8",
#         "Skull Crushers – 3×10",
#         "Pushups Burnout – max reps"
#     ],

#     "Tuesday": [
#         "Deadlift – 5×5",
#         "Weighted Pull-Ups – 4×6",
#         "Barbell Row – 4×8",
#         "T-Bar Row – 3×10",
#         "Face Pulls – 3×15",
#         "Barbell Curl – 3×10",
#         "Alternating DB Curl – 3×12"
#     ],

#     "Wednesday": [
#         "Back Squat – 5×5",
#         "Bulgarian Split Squat – 4×8",
#         "Romanian Deadlift – 4×8",
#         "Leg Extension – 3×15",
#         "Hamstring Curl – 3×15",
#         "Calf Raises – 4×20",
#         "Glute Hip Thrust – 4×10"
#     ],

#     "Thursday": [
#         "Overhead Press – 5×5",
#         "Arnold Press – 4×10",
#         "Lateral Raise – 4×15",
#         "Rear Delt Row – 3×12",
#         "Barbell Shrugs – 3×12",
#         "Hanging Leg Raise – 4×12",
#         "Weighted Plank – 45 sec"
#     ],

#     "Friday": [
#         "Push-Pull Hybrid Volume",
#         "Incline DB Press – 4×12",
#         "Chin-Ups – 4×10",
#         "Cable Row – 3×12",
#         "Side Lateral Raise – 3×15",
#         "Concentration Curl – 3×12",
#         "Tricep Rope Pushdown – 3×15"
#     ],

#     "Saturday": [
#         "Conditioning Day",
#         "HIIT (20 min)",
#         "Sled Push or Sprint – 6 rounds",
#         "Burpees – 3×15",
#         "Core Circuit: Plank, Russian Twist, Toe Touch – 3 rounds",
#         "Farmer Carry – 3×45 sec"
#     ],

#     "Sunday": [
#         "Active Recovery",
#         "Slow Yoga 15 min",
#         "Mobility Sequence – 10 min",
#         "Light Walk / Cycling – 20 min"
#     ]
# }

#     }

#     return render_template(
#         "weekly_plan.html",
#         level=level,
#         week_titles=week_titles,
#         workout_plan=plans[level]
#     )



# # ================= Progress Graph & Tracker =================
# @app.route("/progress", methods=["GET","POST"])
# @login_required
# def progress():

#     conn = connect()
#     cur = conn.cursor()

#     uid = session["user_id"]  # current logged-in user

#     # ---- SAVE ENTRY ----
#     if request.method == "POST":
#         weight_str = request.form.get('weight', '').strip()
#         if weight_str:
#             try:
#                 weight = float(weight_str)
#                 today = datetime.today().strftime("%Y-%m-%d")
#                 cur.execute(
#                     "INSERT INTO progress(user_id, weight, date) VALUES (?,?,?)",
#                     (uid, weight, today)
#                 )
#                 conn.commit()
#             except ValueError:
#                 pass  # galat value ignore

#     # ---- LOAD DATA FOR GRAPH (user-wise) ----
#     cur.execute(
#         "SELECT date, weight FROM progress WHERE user_id=? ORDER BY date",
#         (uid,)
#     )
#     rows = cur.fetchall()
#     conn.close()

#     dates = [r[0] for r in rows]      # "YYYY-MM-DD"
#     weights = [r[1] for r in rows]

#     # progress %
#     progress_pct = None
#     if len(weights) >= 2 and weights[0] != 0:
#         start = weights[0]
#         latest = weights[-1]
#         progress_pct = round(((latest - start) / start) * 100, 2)

#     return render_template(
#         "progress.html",
#         weights=weights,
#         dates=dates,
#         progress=progress_pct
#     )

# # ===================== SAVAGE AI FITNESS COACH =======================
# from difflib import SequenceMatcher

# def update_context(ctx, text):
#     """User ka data (weight/height/goal/place/level) memory me store kare."""
#     t = text.lower()

#     # weight detect (e.g. 70kg)
#     for part in t.split():
#         if "kg" in part:
#             try:
#                 w = float(part.replace("kg", ""))
#                 ctx["weight"] = w
#             except:
#                 pass

#     # height detect (e.g. 170cm)
#     for part in t.split():
#         if "cm" in part:
#             try:
#                 h = float(part.replace("cm", ""))
#                 ctx["height"] = h
#             except:
#                 pass

#     # goal detect
#     if any(w in t for w in ["fat", "cut", "shred"]):
#         ctx["goal"] = "fat_loss"
#     if any(w in t for w in ["muscle", "bulk", "size"]):
#         ctx["goal"] = "muscle_gain"
#     if any(w in t for w in ["strength", "strong", "power"]):
#         ctx["goal"] = "strength"

#     # place detect
#     if "home" in t or "no gym" in t:
#         ctx["place"] = "home"
#     if "gym" in t:
#         ctx["place"] = "gym"

#     # level detect
#     if "beginner" in t or "new" in t or "start" in t:
#         ctx["level"] = "beginner"
#     if "intermediate" in t or "average" in t:
#         ctx["level"] = "intermediate"
#     if "advanced" in t or "pro" in t or "beast" in t:
#         ctx["level"] = "advanced"

#     return ctx


# def build_plan(ctx):
#     """Context ke base par proper savage plan banaye."""
#     w = ctx.get("weight")
#     h = ctx.get("height")
#     goal = ctx.get("goal")
#     place = ctx.get("place")
#     level = ctx.get("level")

#     lines = []

#     # BMI / calories
#     if w and h:
#         h_m = h / 100
#         bmi = round(w / (h_m * h_m), 2)
#         lines.append(f"📊 BMI = {bmi}")
#         if bmi < 18.5:
#             lines.append("Status: Underweight — bulk clean karo, bhai.")
#             calories = f"{int(w*35)}–{int(w*40)} kcal/day"
#         elif bmi < 25:
#             lines.append("Status: Normal — perfect time to chase strength & muscle.")
#             calories = f"{int(w*30)}–{int(w*33)} kcal/day"
#         else:
#             lines.append("Status: Overweight — fat cut kare bina excuse ke.")
#             calories = f"{int(w*22)}–{int(w*26)} kcal/day"

#         protein = f"{round(w*1.8)} g protein/day"
#         water   = "3–4L water/day"
#         lines.append(f"🔥 Calories Target: {calories}")
#         lines.append(f"💪 Protein Target: {protein}")
#         lines.append(f"💧 Water Target: {water}")

#     # Workout plan
#     if goal:
#         lines.append("──────── WORKOUT PLAN ────────")
#         gym = (place == "gym")
#         if goal == "fat_loss":
#             if gym:
#                 lines += [
#                     "Day 1: HIIT + Full Body Circuit",
#                     "Day 2: Incline walk 30 min + Core",
#                     "Day 3: Weights (Upper Body) + 15 min cardio",
#                     "Day 4: Rest / Light walk",
#                     "Day 5: Legs + 10 min stair master",
#                     "Day 6: HIIT 20 min + Abs",
#                     "Day 7: Stretching / Mobility"
#                 ]
#             else:
#                 lines += [
#                     "Day 1: HIIT (Burpees, Jumping Jacks, Mountain Climbers)",
#                     "Day 2: Brisk walk 40 min",
#                     "Day 3: Home Full Body (Pushup/Squat/Lunges/Plank)",
#                     "Day 4: Rest + Stretching",
#                     "Day 5: HIIT 15–20 min",
#                     "Day 6: Core + Walk 30 min",
#                     "Day 7: Yoga / Mobility"
#                 ]
#         elif goal == "muscle_gain":
#             if gym:
#                 lines += [
#                     "Day 1: Push (Chest+Shoulder+Triceps)",
#                     "Day 2: Pull (Back+Biceps)",
#                     "Day 3: Legs (Quads+Hams+Glutes)",
#                     "Day 4: Rest / Walk",
#                     "Day 5: Push (Heavier)",
#                     "Day 6: Pull (Heavy + Rows)",
#                     "Day 7: Legs + Calves"
#                 ]
#             else:
#                 lines += [
#                     "Day 1: Pushups variations + Dips / Chair dips",
#                     "Day 2: Squats + Lunges + Glute Bridge",
#                     "Day 3: Pike pushups + Plank",
#                     "Day 4: Rest / Walk",
#                     "Day 5: Repeat Day1",
#                     "Day 6: Repeat Day2",
#                     "Day 7: Light stretching"
#                 ]
#         elif goal == "strength":
#             lines += [
#                 "Day 1: Heavy Squat + Core",
#                 "Day 2: Heavy Bench + Push accessories",
#                 "Day 3: Rest / Mobility",
#                 "Day 4: Heavy Deadlift + Rows",
#                 "Day 5: Overhead Press + Pullups",
#                 "Day 6: Accessories / Weak point training",
#                 "Day 7: Full recovery"
#             ]

#     # Diet hints
#     if goal:
#         lines.append("──────── DIET CHECKLIST ────────")
#         if goal == "fat_loss":
#             lines += [
#                 "• Roti 3 se zyada mat, rice quantity control.",
#                 "• Har meal me protein fix (Egg/Paneer/Chicken/Curd).",
#                 "• Cold drink, chips, bakery = straight ban 🚫"
#             ]
#         else:
#             lines += [
#                 "• Har meal me solid protein (Egg/Paneer/Chicken/Tofu).",
#                 "• Ghar ka normal khana, junk minimal.",
#                 "• Soya/Paneer/Curd/Chana as daily add-ons."
#             ]

#     if not lines:
#         lines.append("Pehle apna weight, height, goal bata — phir main full plan phod ke dunga 💥")

#     lines.append("\nNo excuses now. Start today, not ‘kal se’. 🔥")
#     return "\n".join(lines)


# def savage_ai_reply(ctx, text):
#     t = text.lower().strip()

#     # reset
#     if "reset" in t or "clear" in t:
#         ctx.clear()
#         return ctx, "Context clear kar diya. Ab fresh se start karte hain. Weight, height, goal bata 💪"

#     # greetings
#     if any(word in t for word in ["hello","hi","hey","yo","namaste"]):
#         if not ctx:
#             return ctx, "Sun champion 👊 — weight (kg), height (cm) aur goal (fat loss / muscle / strength) bata."
#         else:
#             return ctx, "Bata ab aage kya scene hai? Diet, workout ya progress?"

#     # update context from message
#     ctx = update_context(ctx, t)

#     # quick Q/A shortcuts
#     if "bmi" in t and (ctx.get("weight") and ctx.get("height")):
#         return ctx, build_plan(ctx)

#     if "diet" in t and ctx.get("goal"):
#         return ctx, build_plan(ctx)

#     if "workout" in t or "plan" in t or "routine" in t:
#         return ctx, build_plan(ctx)

#     # generic: if enough info, give full plan
#     if ctx.get("weight") and ctx.get("height") and ctx.get("goal"):
#         return ctx, build_plan(ctx)

#     # else ask for missing pieces
#     missing = []
#     if not ctx.get("weight"):
#         missing.append("weight (kg)")
#     if not ctx.get("height"):
#         missing.append("height (cm)")
#     if not ctx.get("goal"):
#         missing.append("goal (fat loss / muscle / strength)")
#     if missing:
#         return ctx, "Thoda clear bata 👉 " + ", ".join(missing) + " — phir pura savage plan dunga."

#     # fallback
#     return ctx, "Fitness ke bare me kuch bhi puch — fat loss, muscle, diet, BMI. Seedha bol, घुमा मत 🙂"

# #=============== assistant =======================
# @app.route("/assistant", methods=["GET", "POST"])
# @login_required
# def assistant():
#     # session-based memory
#     chat = session.get("chat_history", [])
#     ctx  = session.get("coach_ctx", {})

#     if request.method == "POST":
#         user_msg = request.form.get("question", "").strip()
#         if user_msg:
#             # user msg add karo
#             chat.append({"sender": "user", "text": user_msg})

#             # ai reply
#             ctx, ai_text = savage_ai_reply(ctx, user_msg)
#             chat.append({"sender": "ai", "text": ai_text})

#             # save back to session
#             session["chat_history"] = chat
#             session["coach_ctx"] = ctx

#     return render_template("assistant.html", chat=chat)


# # ================= Today Workout (auto day) =================
# def today_schedule():
#     """Har din ka simple gym split (example)."""
#     return {
#         "Monday": "Chest + Triceps 🔥 (Bench Press, Pushups, Cable Flyes)",
#         "Tuesday": "Back + Biceps 💪 (Lat Pulldown, Rows, Curls)",
#         "Wednesday": "Leg Day 🦵 (Squats, Lunges, Leg Press)",
#         "Thursday": "Shoulders + Abs 🧠 (Shoulder Press, Lateral Raises, Planks)",
#         "Friday": "Full Upper Body ⚡ (Compound + Isolation Mix)",
#         "Saturday": "Cardio + Core ❤️‍🔥 (Treadmill / Cycling + Abs Circuit)",
#         "Sunday": "Active Rest 😴 (Walk, Stretching, Mobility)"
#     }


# @app.route("/today_workout")
# @login_required
# def today_workout():

#     import datetime
#     today = datetime.datetime.now().strftime("%A")

#     # Your full workout dictionary defined earlier
#     from workout_data import workouts   # where beginner/intermediate/advanced stored

#     beginner = workouts["beginner"][today]
#     intermediate = workouts["intermediate"][today]
#     advanced = workouts["advanced"][today]

#     return render_template(
#         "today_workout.html",
#         today=today,
#         beginner=beginner,
#         intermediate=intermediate,
#         advanced=advanced
#     )



# # ==================== CALENDAR PAGE ====================

# @app.route("/calendar")
# @login_required
# def calendar_full():
#     return render_template("calendar.html")

# # ---------------- MAIN RUN ------------------------

# if __name__ == "__main__":
#     app.run(debug=True)


workouts = {

    "beginner": {
        "Monday": [
            "Pushups – 3×10",
            "Incline Pushups – 3×12",
            "Bodyweight Squats – 3×15",
            "Glute Bridge – 3×15",
            "Plank – 30 sec",
            "Dumbbell Chest Press – 3×12"
        ],

        "Tuesday": [
            "Brisk Walk – 20–30 min",
            "Arm Circles – 2×20",
            "Hip Mobility Routine – 5 min",
            "Child Pose Stretch – 40 sec",
            "Hamstring Stretch – 40 sec"
        ],

        "Wednesday": [
            "Dumbbell Shoulder Press – 3×12",
            "One-Arm Dumbbell Row – 3×12 each side",
            "Bicep Curl – 3×12",
            "Tricep Dips on chair – 3×12",
            "Reverse Snow Angels – 3×15",
            "Front Raise – 3×12"
        ],

        "Thursday": [
            "Rest Day + Light Activity",
            "Cat-Cow Stretch – 10 reps",
            "Cobra Stretch – 40 sec",
            "Neck Mobility – 10 reps",
            "Shoulder Stretch – 30 sec"
        ],

        "Friday": [
            "Lunges – 3×12",
            "Sumo Squats – 3×15",
            "Glute Kickback – 3×15",
            "Calf Raises – 3×20",
            "Wall Sit – 30 sec",
            "Hip Thrust – 3×12",
            "Side Leg Raises – 3×15"
        ],

        "Saturday": [
            "Low Intensity Jog – 5 min",
            "Mountain Climbers – 3×20",
            "Crunches – 3×15",
            "Leg Raises – 3×12",
            "Russian Twist – 3×20",
            "Bicycle Crunch – 3×15"
        ],

        "Sunday": [
            "Yoga Flow – 10 min",
            "Deep Breathing – 5 min",
            "Ankle Mobility – 10 reps",
            "Full Body Stretch – 5 min"
        ]
    },

    # ======================== INTERMEDIATE ========================

    "intermediate": {
        "Monday": [
            "Bench Press – 4×8",
            "Incline DB Press – 4×10",
            "Weighted Pushups – 3×12",
            "Triceps Rope Pushdown – 3×12",
            "Chest Fly Machine – 3×15",
            "Overhead Tricep Extension – 3×12"
        ],

        "Tuesday": [
            "Pull-Ups – 4×6",
            "Lat Pulldown – 4×10",
            "Seated Row – 4×10",
            "Dumbbell Bicep Curl – 3×12",
            "Hammer Curl – 3×12",
            "Face Pull – 3×15"
        ],

        "Wednesday": [
            "Back Squats – 4×8",
            "Lunges – 3×12",
            "Romanian Deadlift – 4×10",
            "Leg Press – 4×12",
            "Leg Extension – 3×15",
            "Calf Raises – 3×20"
        ],

        "Thursday": [
            "Shoulder Press – 4×10",
            "Lateral Raises – 4×12",
            "Front Raise – 3×12",
            "Arnold Press – 3×10",
            "Cable Crunch – 3×15",
            "Hanging Leg Raises – 3×12"
        ],

        "Friday": [
            "Incline Bench Press – 4×8",
            "Bent Over Row – 4×8",
            "Chest Dip – 3×10",
            "Lat Pulldown Heavy – 3×10",
            "Tricep Dips – 3×12",
            "Barbell Curl – 3×12"
        ],

        "Saturday": [
            "HIIT 10 Min",
            "Mountain Climbers – 3×25",
            "Plank – 45 sec",
            "Side Plank – 30 sec each",
            "Russian Twist – 3×25",
            "Burpees – 3×10"
        ],

        "Sunday": [
            "Active Recovery Walk – 20 min",
            "Full Body Stretch – 10 min",
            "Deep Breathing – 5 min"
        ]
    },

    # ======================== ADVANCED ========================

    "advanced": {
        "Monday": [
            "Heavy Bench Press – 5×5",
            "Weighted Dips – 4×8",
            "Incline DB Press – 4×10",
            "Cable Crossovers – 4×12",
            "Skull Crushers – 4×10",
            "Diamond Pushups – 3×15"
        ],

        "Tuesday": [
            "Deadlift – 5×5",
            "Weighted Pull-Ups – 4×6",
            "T-Bar Row – 4×10",
            "Single Arm Row – 4×12",
            "Barbell Curl – 4×10",
            "Reverse Curl – 3×12"
        ],

        "Wednesday": [
            "Heavy Squats – 5×5",
            "Bulgarian Split Squats – 4×10",
            "Hip Thrust – 4×10",
            "Leg Press – 4×12",
            "Lying Leg Curl – 4×12",
            "Standing Calf Raise – 4×20"
        ],

        "Thursday": [
            "Overhead Press – 5×5",
            "Lateral Raise – 4×15",
            "Rear Delt Fly – 4×15",
            "Upright Row – 4×10",
            "Hanging Leg Raise – 4×12",
            "Cable Woodchopper – 3×15"
        ],

        "Friday": [
            "Barbell Row – 5×5",
            "Weighted Chin-Ups – 4×8",
            "Bench Press Volume – 4×10",
            "Face Pull – 4×15",
            "Hammer Curl – 4×12",
            "Tricep Rope Pushdown – 4×12"
        ],

        "Saturday": [
            "HIIT Sprints 10 Min",
            "Burpees – 4×12",
            "V-Ups – 4×15",
            "Mountain Climbers – 4×25",
            "Plank – 60 sec",
            "Toe Touch Crunch – 4×15"
        ],

        "Sunday": [
            "Mobility Flow – 10 min",
            "Yoga — Strength Release – 10 min",
            "Deep breathing + Meditation – 10 min"
        ]
    }
}
