"""
BKT (Bayesian Knowledge Tracing) module.

This module implements the mathematical core for tracking user skill mastery.
It is completely independent from database, API, or frontend concerns.

Components:
- engine.py: Core BKT mathematical formula
- base.py: Abstract interface for skill trackers
- manager.py: Registry mapping skills to their trackers
- *_tracker.py: Skill-specific tracker implementations
"""
