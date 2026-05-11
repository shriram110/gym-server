"""Canned chatbot responses — no real AI. Picked by simple keyword matching."""
import random

GENERIC_REPLIES = [
    "Great question! At Iron Forge Gym, consistency beats intensity. Aim for at least 4 sessions a week and your results will compound.",
    "Remember — progress isn't linear. Track your sets and reps weekly so you can spot real trends, not noise.",
    "If you ever feel stuck, drop me a message. I can suggest variations to break a plateau.",
]

KEYWORD_REPLIES = {
    ("protein", "diet", "nutrition", "eat", "food", "macros"):
        "Aim for roughly 1.6–2.2 g of protein per kg of bodyweight. Spread it across 3–4 meals. Whole foods first — chicken, eggs, lentils, paneer, fish — and supplement with whey only if you can't hit your numbers from food.",
    ("muscle", "build", "bulk", "hypertrophy", "gain"):
        "For muscle growth: 8–12 reps in the working range, 3–5 sets per exercise, train each muscle 2× a week, sleep 7+ hours, and eat in a small calorie surplus (200–400 kcal). Compound lifts (squat, bench, deadlift, row, OHP) drive most of the growth.",
    ("fat", "lose", "cut", "weight loss", "slim", "shred"):
        "Fat loss = small calorie deficit + protein high + lifting heavy + walking daily. Don't slash calories too hard or you'll lose muscle. Aim for 0.5–1% bodyweight per week.",
    ("cardio", "running", "treadmill", "endurance"):
        "Mix it up — 1–2 zone-2 sessions (30–45 min easy) and 1 short HIIT session (10–15 min) per week is plenty for most goals. Cardio supports lifting, it doesn't replace it.",
    ("rest", "recovery", "sleep", "soreness"):
        "Recovery is where the gains happen. 7–9 hours of sleep, 1–2 full rest days per week, and at least 48h between hitting the same muscle hard. If you're sore for more than 3 days, deload.",
    ("plan", "routine", "split", "program", "workout"):
        "A simple, proven split: Push / Pull / Legs / Rest / Upper / Lower / Rest. 4–6 working sets per muscle per session. Pick 1 compound lift first, then 2–3 accessories. Progressive overload weekly.",
    ("warm", "warmup", "warm-up"):
        "5 min light cardio + dynamic mobility for the joints you'll use + 2 ramp-up sets of your first lift at 50% and 75% of working weight. Skip static stretching pre-lift.",
    ("water", "hydration", "drink"):
        "Aim for 35 ml per kg of bodyweight per day, more if you sweat a lot. A pale yellow morning pee is a good signal you're hydrated.",
    ("squat", "deadlift", "bench", "form", "technique"):
        "Form first, weight second. Brace your core, neutral spine, controlled tempo (2 sec down, 1 sec up). Film your sets from the side once a week — most form issues fix themselves once you SEE them.",
    ("injury", "pain", "hurt", "ache"):
        "Sharp pain? Stop and book a session with our physio at the front desk. Dull soreness 24–48h after training is normal. Never train through pain that sharpens during a movement.",
    ("supplements", "creatine", "whey", "bcaa"):
        "The only supplements with strong evidence: creatine monohydrate (3–5 g daily), whey protein (only if needed to hit protein goals), caffeine pre-workout, vitamin D if low. Skip the rest.",
    ("beginner", "start", "new", "first time"):
        "Welcome! Start with 3 full-body sessions a week — Mon, Wed, Fri. Focus on technique with light weights for the first 2 weeks. Our trainers can walk you through every machine — just ask at the floor desk.",
    ("women", "female", "girl", "lady"):
        "The training principles are identical regardless of gender — lift heavy, eat enough protein, recover well. Don't fear the heavy weights; you won't get 'too bulky.' Strength training is the single best thing you can do for long-term health.",
    ("attendance", "check in", "checkin", "log"):
        "You can mark today's attendance from your dashboard — there's a 'Check In' button on the home screen. Streaks unlock achievements!",
    ("fees", "payment", "due", "bill"):
        "All fee details are on your dashboard under the Fees section. We send a reminder 7 days before due date and apply a small late fee after 5 days past due.",
    ("hours", "open", "timing", "time"):
        "Iron Forge is open Mon–Sat 5 am – 11 pm and Sun 6 am – 10 pm. Off-peak (10 am – 4 pm) is the quietest if you like elbow room.",
    ("class", "yoga", "zumba", "hiit"):
        "Group classes are listed on the Schedule page. Yoga: Tue/Thu 7am. Zumba: Mon/Wed/Fri 6pm. HIIT: Tue/Sat 7pm. Drop in any time — included with your membership.",
}


def reply_for(message: str) -> str:
    msg = message.lower()
    for keys, response in KEYWORD_REPLIES.items():
        if any(k in msg for k in keys):
            return response
    return random.choice(GENERIC_REPLIES)
