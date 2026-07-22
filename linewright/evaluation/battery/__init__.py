"""Fast-battery run pipeline (Dispatch 24).

Turns the frozen fast battery (benchmarks/active-core/fast-v1/) into a frozen generation
plan, runs it across model roles (real HF worker on a GX10, or stub in tests), and scores the
normalized outputs with the Dispatch-21 mechanical gates + the Dispatch-23 Module-J slop
analysis, then builds blind reviewer packets. No model identity ever reaches a reviewer.
"""
BATTERY_DIR_REL = "benchmarks/active-core/fast-v1"
