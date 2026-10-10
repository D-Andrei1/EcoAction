"""
app.py - starts EcoAction Hub. RUN THIS FILE to start the app (in IDLE: open it and press F5).
PROVIDED COMPLETE - type it in exactly and do not change it.
"""

import importlib
import db
import jobs
import security # noqa: F401 (switches on sessions and CSRF protection)
import ui # noqa: F401 (switches on the error pages)
import web

# One file per feature, in the features folder. A feature that hasn't been built yet is skipped.
FEATURES = ["accounts", "styleguide", "onboarding", "calc", "actions", "dashboard", "goals", "challenges",
"community", "stories", "reports", "notifications", "admin"]

def load_features():
    loaded = []
    for name in FEATURES:
        try:
            importlib.import_module("features." + name)
        except ModuleNotFoundError as problem:
            if problem.name == "features." + name:
                continue # not built yet - that's fine
            raise # a real mistake inside a feature file
        loaded.append(name)
    return loaded

def main():
    db.init_db()
    loaded = load_features()
    print("Features loaded: " + (", ".join(loaded) if loaded else "none yet"))
    jobs.start()
    web.serve()

if __name__ == "__main__":
    main()