"""features/styleguide.py - FE1: one page that shows every part of the design system."""
import security
import ui
import web
from web import route

@route("GET", "/styleguide")
@security.admin_required
def styleguide(request):
    buttons = (ui.button("Primary", "primary", "button") + " " + ui.button("Secondary", "secondary", "button")
               + " " + ui.button("Ghost", "ghost", "button") + " " + ui.button("Danger", "danger", "button"))
    body = ui.card("Buttons", buttons)
    body += ui.card("Empty state", ui.empty_state("Nothing here yet", "This is what an empty list looks like."))
    body += ui.card("Modal", ui.modal("demo-modal", "A dialog", "<p>Press Esc or Close to shut it.</p>")
                    + ui.button("Open dialog", "secondary", "button", 'data-open-modal="demo-modal"'))
    body += ui.card("Toast", ui.button("Show a toast", "secondary", "button",
                                       'onclick="showToast(\'Saved\', \'success\')"'))

    # TO DO: add cards for ui.skeleton(3), ui.kpi(...), the four ui.badge(...) kinds,
    # and ui.field(...) with error="..." so the error style shows.

    body += ui.card("Skeleton",ui.skeleton(3))

    body += ui.card("Kpi",ui.kpi("Key Performance Indicator", 10, "KPI description"))

    badges = (
        ui.badge("Neutral badge", "neutral") + " " +
        ui.badge("Good badge", "good") + " " +
        ui.badge("Warn badge", "warn") + " " +
        ui.badge("Bad badge", "bad")
    )
    body += ui.card("Badges", badges)

    body += ui.card("Error field", ui.field("Field", "field", error="Invalid input"))

    return web.html(ui.layout(request, "Style guide", body))
    
ui.add_nav("Style guide", "/styleguide", who="admin", order=95)