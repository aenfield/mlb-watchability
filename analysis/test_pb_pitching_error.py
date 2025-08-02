#!/usr/bin/env python3
"""Test script to see what happens when pb.pitching_stats fails."""

import pybaseball as pb

print("Calling pb.pitching_stats(2025, qual=20)...")
result = pb.pitching_stats(2025, qual=20)
print(f"Success! Got {len(result)} rows")
print(result.head())
