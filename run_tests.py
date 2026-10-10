"""
run_tests.py - runs every test in the tests folder. RUN THIS FILE (in IDLE: open it and press F5).
PROVIDED COMPLETE - type it in exactly and do not change it.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, "tests"), top_level_dir=ROOT)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("ALL TESTS PASSED" if result.wasSuccessful() else "SOME TESTS FAILED - read the messages above")
    raise SystemExit(0 if result.wasSuccessful() else 1) # 0 = passed, for automatic checks