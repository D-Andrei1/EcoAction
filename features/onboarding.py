import re
import sqlite3
from datetime import datetime, timedelta, timezone, date

import calendar
import db
import security
import services
import ui
import web
from ui import h
from web import route

STEPS = 3

def finish_path():
    return "/dashboard" if web.has_route("GET", "/dashboard") else "/"

def month_bounds(today):
    """First and last day of the month `today` is in."""
    last = calendar.monthrange(today.year, today.month)[1]
    return today.replace(day=1), today.replace(day=last)

def progress_bar(step):
    percent = int(step * 100 / STEPS)
    return ('<p>Step %d of %d</p><div class="progress" role="progressbar" aria-valuemin="0" '
            'aria-valuemax="%d" aria-valuenow="%d" aria-label="Onboarding progress">'
            '<span style="width:%d%%"></span></div>' % (step, STEPS, STEPS, step, percent))

@route("GET","/onboarding")
@security.login_required
def get_onboarding_page(request):
    if request.user["onboarding_done"]:
        return web.redirect(finish_path())
    else: 
        return onboarding_page(request)

def onboarding_page(request,errors={}, status=200):
    step = min(request.user["onboarding_step"] + 1, STEPS)

    body = ui.card("Progress", progress_bar(step))
    body += choose_onboarding_step(request, step, errors)

    return web.html(ui.layout(request, "Onboarding", body), status)

def choose_onboarding_step(request, step, errors):
    form = {
        1 : step_1_form(request, errors),
        2 : step_2_form(request, errors),
        3 : step_3_form(request, errors)
    }

    chosen_form = form[step]
    print(chosen_form)

    if chosen_form == None:
        return ""
    else:
        return chosen_form

#---------- STEP 1 ------------
def step_1_form(request, errors):
    errors = errors or {}

    fields = (ui.field("What should we call you?",
                       "display_name",
                        error=errors.get("display_name", ""),
                        required=False
                       ))

    body = ui.card("", ui.form(request, "/onboarding/1", fields, "Choose your display name"))

    return body

@route("POST", "/onboarding/1")
@security.login_required
def step_1(request):
    errors = {}
    MAX_LENGTH = 40
    MIN_LENGTH = 2
    form = request.form

    display_name = form.get("display_name", "").strip()

    if display_name != "":
        if len(display_name) < MIN_LENGTH:
            errors["display_name"] = "Your name must be atleast 2 characters."

        if len(display_name) > MAX_LENGTH:
            errors["display_name"] = "Your name cannot be over 40 characters."
    else:
        email = request.user["email"]
        display_name = email.split("@")[0]

    if errors:
        return onboarding_page(request,errors,400)

    db.change("UPDATE users SET display_name = ?, onboarding_step = 1 WHERE id= ?",
              (display_name, request.user["id"]))
    return web.redirect("/onboarding")


#---------- STEP 2 ------------
def step_2_form(request, errors):
    OPTIONS = ((" ", "Rather not say"),
               ("car","car"),
               ("bus","bus"),
               ("train","train"),
               ("cycle","cycle"),
               ("walk","walk"),
               ("mix","mix")
               )

    fields = (ui.select_field("Your habits","habit",OPTIONS,required=True))

    body = ui.card("", ui.form(request, "/onboarding/2", fields, "Choose your habit"))

    return body

@route("POST", "/onboarding/2")
@security.login_required
def step_2(request):
    form = request.form

    habit = form.get("habit", "")

    services.preferences(request.user["id"])

    db.change("UPDATE preferences SET baseline_habits = ? WHERE user_id = ?",
              (habit, request.user["id"]))

    db.change("UPDATE users SET onboarding_step = 2 WHERE id= ?",
              (str(request.user["id"])))

    return web.redirect("/onboarding")

#---------- STEP 3 ------------
def step_3_form(request,errors):
    errors = errors or {}

    fields = (
        ui.field("A first goal for this month",
                "first_goal_kg", "20", 
                required=True,
                error = errors.get("first_goal", "")
                )
    )

    body = ui.card("", ui.form(request, "/onboarding/3", fields, "Set your goal"))

    return body

@route("POST", "/onboarding/3")
@security.login_required
def step_3(request):
    errors = {}
    MIN_GOAL = 0
    MAX_GOAL = 100000
    today = date.today()
    form = request.form

    goal_kg = int(form.get("first_goal_kg", "").strip())

    if goal_kg < MIN_GOAL:
        errors["first_goal"] = "Your goal must be over 0kg"

    if goal_kg > MAX_GOAL: 
        errors["first_goal"] = "Your goal must be less than 10,000kg"

    if errors:
        return onboarding_page(request, errors, 400)

    db.change("UPDATE goals set is_active = 0 WHERE id = ?",
              (request.user["id"],))

    db.execute("INSERT INTO goals (user_id, target_kg, start_date, end_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
               (request.user["id"], goal_kg, month_bounds(today)[0], month_bounds(today)[1], db.now(), db.now()))

    db.change("UPDATE users set onboarding_step = 3, onboarding_done = 1 WHERE id = ?",
              (request.user["id"],))

    ui.flash(request, "You're all set. Log your first action to start tracking progress.")
    return web.redirect(finish_path())



ui.add_nav("Onboarding", "/onboarding", order=90)