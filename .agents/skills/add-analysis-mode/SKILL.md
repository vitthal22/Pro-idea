---
name: add-analysis-mode
description: Add a new resume analysis mode to the system
---

## Prerequisites

- Understanding of the evaluator pipeline and orchestrator
- At least one existing evaluator implemented

## Steps

1. **Add the mode to the enum** in `app/api/schemas/analyses.py`
   ```python
   from enum import Enum

   class AnalysisType(str, Enum):
       general = "general"
       role_based = "role_based"
       jd_based = "jd_based"
       custom = "custom"
       new_mode = "new_mode"  # Add here
   ```

2. **Create mode configuration** in `app/ai/prompts/modes/<mode>.py`
   ```python
   MODE = "new_mode"
   DESCRIPTION = "Description of what this mode does"

   # Which evaluators run for this mode
   EVALUATORS = ["recruiter", "ats", "technical", "content_quality"]

   # Scoring category weights (must sum to 100)
   SCORING_WEIGHTS = {
       "content_quality": 25,
       "experience_quality": 25,
       "skills_alignment": 15,
       "ats_compatibility": 20,
       "role_relevance": 15,
   }
   ```

3. **Update the orchestrator** (`app/ai/orchestrator.py`)
   - Add mode routing logic
   - Map mode → evaluators → prompts
   - Handle mode-specific context (e.g., role_based needs target_role)

4. **Update the scoring engine** (`app/ai/scoring.py`)
   - Add mode-specific weight configuration
   - Ensure scoring uses the correct weights for the mode

5. **Update API validation** in `app/api/schemas/analyses.py`
   - Add mode-specific request fields (e.g., target_role for role_based)
   - Validate that required fields are present for the mode

6. **Write integration tests** in `tests/test_api/test_analyses.py`
   - Test the new mode with valid input
   - Test missing required fields for the mode
   - Test evaluator selection matches mode config

## Verification

- Create an analysis with the new mode via API
- Verify correct evaluators are called
- Verify scoring uses correct weights
- Check results contain expected sections

## Common Mistakes

- Not updating the orchestrator (mode won't work)
- Scoring weights not summing to 100
- Missing validation for mode-specific required fields
- Not writing tests for the new mode
