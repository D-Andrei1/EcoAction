import re
import sqlite3
from datetime import datetime, timedelta, timezone

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
    if step == 1:
        return step_1_form(request, errors)

    if step == 2:
        return step_2_form(request)

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

    if len(display_name) < MIN_LENGTH:
        errors["display_name"] = "Your name must be atleast 2 characters."

    if len(display_name) > MAX_LENGTH:
        errors["display_name"] = "Your name cannot be over 40 characters."

    if errors:
        return onboarding_page(request,errors,400)

    db.change("UPDATE users SET display_name = ?, onboarding_step = 1 WHERE id= ?",
              (display_name, request.user["id"]))
    return onboarding_page(request)


#---------- STEP 2 ------------
def step_2_form(request):
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
    print(habit)

    services.preferences(request.user["id"])

    db.change("UPDATE preferences SET baseline_habits = ? WHERE user_id = ?;set onboarding_step = 2",
              habit, request.user["id"])

    return onboarding_page(request)

#---------- STEP 3 ------------
def step_3_form(request, errors):
    pass

ui.add_nav("Onboarding", "/onboarding", order=90)