"""Nebius AI (OpenAI-compatible) LLM interface for medical document extraction."""

from __future__ import annotations

from typing import Any, Dict, List
import json
import re

from openai import OpenAI


def init_llm_nebius(api_key: str, model_name: str, base_url: str) -> OpenAI:
    """Initialize Nebius OpenAI-compatible client."""
    return OpenAI(api_key=api_key, base_url=base_url)


def extract_claimant_with_llm_nebius(
    client: OpenAI, model_name: str, text: str
) -> Dict[str, Any]:
    """Extract claimant info from PDF text using Nebius."""

    prompt = f"""You are extracting disability claim information. Read carefully and extract ALL fields.

DOCUMENT:
{text[:12000]}

EXTRACT THESE FIELDS (look for EXACT patterns):

1. NAME: After "Claimant:" or "RE:" or "Name:"
   Example: "Claimant: Arthur Miller" → "Arthur Miller"

2. SSN: After "SSN:"
   Example: "SSN: 456-12-7890" → "456-12-7890"

3. DATE OF BIRTH: Look for "Date of Birth" in a table or "DOB" or birth date field
   Example: "Date of Birth: 05/21/1965" → "05/21/1965"
   
4. ALLEGED ONSET DATE (AOD): After "Alleged onset:"
   Example: "Alleged onset: 07/01/2022" → "07/01/2022"

5. DATE LAST INSURED (DLI): This appears AFTER "Last Insured:" or "Last Insured: Application:"
   Example: "Last Insured: Application: 07/14/2022" → "07/14/2022"
   IMPORTANT: DLI is usually DIFFERENT from AOD. Look for the date that comes after "Last Insured:"

6. TITLE: After "Claim type:" or "Title:" (usually T16, TII, or XVI)
   Example: "Claim type: T16" → "T16"

7. EDUCATION: Look for "12th grade education", "obtained a 12th grade", "10th grade" - extract ONLY the NUMBER
   Example: "12th grade education" → "12" 
   Example: "Claimant is 57 years old, 12th grade education" → "12"
   Example: "obtained a 12th grade education" → "12"

8. SPECIAL EDUCATION: Look for "Special Ed:" or special education mentions
   Example: "Special Ed: No" → false

Return ONLY this JSON format (no other text):
{{"name": "Arthur Miller", "ssn": "456-12-7890", "dob": "05/21/1965", "aod": "07/01/2022", "dli": "07/14/2022", "title": "T16", "last_grade_completed": "12", "attended_special_ed": false}}"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical document extraction expert. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=512,
        )

        content = response.choices[0].message.content
        if not content:
            return {}

        # Extract JSON from response
        json_match = re.search(r"\{.*?\}", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Error extracting claimant info: {e}")

    return {}


def extract_impairments_with_llm_nebius(
    client: OpenAI, model_name: str, text: str
) -> List[str]:
    """Extract impairments from PDF text using Nebius."""

    prompt = f"""Extract the PRIMARY medical impairments/conditions for this disability claim.

DOCUMENT:
{text[:10000]}

Look for these patterns:
- "ALLEGATIONS OF IMPAIRMENTS" section
- "IMPAIRMENT:" followed by condition names
- Medical codes like "7150 - Osteoarthrosis"
- Phrases like "allegations of", "diagnosed with", "suffers from"
- List of medical conditions causing disability

Examples of GOOD impairments to extract:
- "Chronic hip pain"
- "Osteoarthrosis" or "Arthritis"  
- "Nerve damage related to neck area"
- "Insomnia"
- "Hypertension"

Examples of what NOT to extract:
- Administrative terms
- Document names
- Generic "pain" without body part

Return JSON array with 3-5 specific medical conditions:
["Chronic hip pain", "Nerve damage related to neck area", "Insomnia"]"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical document extraction expert. Return only valid JSON arrays.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=512,
        )

        content = response.choices[0].message.content
        if not content:
            return []

        # Extract JSON array from response
        json_match = re.search(r"\[.*?\]", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Error extracting impairments: {e}")

    return []


def extract_events_with_llm_nebius(
    client: OpenAI, model_name: str, text: str, page_num: int
) -> List[Dict[str, Any]]:
    """Extract medical events from a page using Nebius."""

    prompt = f"""Extract medical encounters from this page. This may be an index/table listing records OR actual medical content.

PAGE {page_num}:
{text[:1500]}

IMPORTANT: If you see a format like "8F: Office Treatment Records - Sterling Health Clinic 07/21/2021-07/06/2023 Pg 34",
extract the ACTUAL page number from "Pg 34" and use that as ref_page (not the current page).

For each medical visit/treatment, extract:

1. DATE: In MM/DD/YYYY format or date range start (must be between 2020-2024)

2. PROVIDER: Healthcare facility name. Normalize:
   - "METRO HEALTH & WELLNESS #2" → "Metro Health & Wellness Center"
   - "METRO WELLNESS CLINIC" → "Metro Health & Wellness Center"  
   - "WILLOW CREEK MEDICAL" → "Willow Creek Medical Center"
   - "CENTRAL PLAINS MEDICAL" → "Central Plains Medical Center"
   - "STERLING HEALTH" → "Sterling Health Clinic"
   - "UNITY CARE" → "Unity Care Clinic"

3. REASON: Be SPECIFIC. Look for symptoms, procedures, diagnoses.
   Good: "Hip pain; X-ray shows arthritis changes", "Right total hip replacement surgery"
   Avoid: "Medical Visit", "Hospital Records"

4. REF_PAGE: 
   - If the text shows "Pg XX" after the record, use XX as the ref_page
   - Otherwise use {page_num}

SKIP: "Disability Report", "Function Report", "MER", "HIT Response", "Evidence Requested"

Return JSON array:
[{{"date": "07/21/2021", "provider": "Sterling Health Clinic", "reason": "Routine outpatient treatment for joint pain", "ref_page": 34}}]"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical document extraction expert. Return only valid JSON arrays.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=1024,
        )

        content = response.choices[0].message.content
        if not content:
            return []

        # Extract JSON array from response
        json_match = re.search(r"\[.*?\]", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Error extracting events from page {page_num}: {e}")

    return []

