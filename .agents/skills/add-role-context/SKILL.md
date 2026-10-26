---
name: add-role-context
description: Add a new job role context for role-based resume analysis
---

## Prerequisites

- Understanding of the role-based analysis mode
- Existing role context files in `app/ai/prompts/roles/`

## Steps

1. **Create the role context file** in `app/ai/prompts/roles/<role_name>.py`

   ```python
   ROLE_KEY = "data_engineer"  # Matches API enum value
   ROLE_DISPLAY_NAME = "Data Engineer"

   ROLE_CONTEXT_PROMPT = """
   ## Data Engineer Role Context

   ### Key Skills Expected
   - Python, SQL, Spark, Airflow
   - Data pipeline design and implementation
   - ETL/ELT processes
   - Cloud platforms (AWS/GCP/Azure)
   - Data warehousing (Snowflake, BigQuery, Redshift)
   - Streaming (Kafka, Flink)

   ### Common Project Types
   - Data pipeline implementations
   - ETL workflow automation
   - Data quality monitoring
   - Dashboard/reporting infrastructure
   - Migration projects

   ### Technology Stack Expectations
   - Must have: Python, SQL, at least one pipeline tool
   - Strong signal: Spark, Airflow, cloud data services
   - Bonus: dbt, Iceberg, Delta Lake

   ### Red Flags
   - No SQL experience for a data role
   - Only frontend/backend projects with no data work
   - No mention of data quality or testing
   - Generic "worked with data" without specifics

   ### What Recruiters Look For
   - Quantified impact (processed X TB/day, reduced latency by Y%)
   - Scale of data handled
   - Specific tools and versions
   - End-to-end pipeline ownership
   """
   ```

2. **Register in the role registry** (`app/ai/prompts/roles/__init__.py`)
   ```python
   from app.ai.prompts.roles import data_engineer

   ROLE_REGISTRY = {
       "frontend_dev": frontend_dev,
       "backend_dev": backend_dev,
       "fullstack_dev": fullstack_dev,
       "ai_engineer": ai_engineer,
       "data_scientist": data_scientist,
       "devops": devops,
       "data_engineer": data_engineer,  # Add here
   }
   ```

3. **Add to the role enum** in `app/api/schemas/analyses.py`
   ```python
   class TargetRole(str, Enum):
       frontend_dev = "frontend_dev"
       backend_dev = "backend_dev"
       # ... existing roles
       data_engineer = "data_engineer"  # Add here
   ```

4. **Write tests** to verify:
   - Role context loads correctly
   - Role is available in the API enum
   - Role-based analysis with this role uses the correct context

## Role Context Writing Rules

- Be specific about technologies and tools
- Include both "must have" and "nice to have" skills
- List red flags that would disqualify a candidate
- Describe what recruiters specifically look for
- Include common project types for the role
- Keep context under 500 words — focused and actionable

## Verification

- Create a role-based analysis targeting the new role
- Verify the role context is included in the evaluator prompts
- Check that the analysis results reflect role-specific feedback

## Available Roles (MVP)

| Key | Display Name |
|---|---|
| `frontend_dev` | Frontend Developer |
| `backend_dev` | Backend Developer |
| `fullstack_dev` | Full Stack Developer |
| `ai_engineer` | AI Engineer |
| `data_scientist` | Data Scientist |
| `devops` | DevOps Engineer |
