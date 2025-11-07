# Gemini Slide Generator (Person A)

This module generates slide titles, bullet points, narration, and timing.
The result is used by Person B to create the voiceover + video.

## Output Files
Raw model output → ai_generation/output/raw_gemini/<task_id>.json  
Clean final JSON → ai_generation/output/slides/<task_id>.json  

## Slide Count Guide
2–3 minutes → 5 slides  
4–5 minutes → 6 slides  
6–7 minutes → 7 slides  

## Duration Guide
10–15 seconds narration per slide  
Total ≈ target length (±10%)  

## Schema
See SCHEMA.md
