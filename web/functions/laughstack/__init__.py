"""LaughStack: audience-response analytics for live comedy.

Pipeline stages:
    ingest   -> load/QC audio (kit recordings or YouTube pulls)
    detect   -> laughter/applause event detection
    align    -> attach events to transcript segments (joke instances)
    metrics  -> per-event, per-bit, per-set scores; within-room normalization
    compare  -> match the same joke across sets, A/B delivery comparison
    report   -> JSON / Markdown deliverables, clip candidates
"""

__version__ = "0.1.0"
