"""ARIA tool: parse_intent

Extracts structured shopping intent from customer's natural language message.
Uses Gemini 1.5 Flash for fast classification.

Spec: specs/SPEC-ARIA-01-parse_intent.md
"""

from __future__ import annotations

import re
from fastapi import APIRouter, HTTPException
from tools.shared.models import (
    ParseIntentRequest,
    ParseIntentResponse,
    ErrorResponse,
)
from tools.shared.logger import get_logger
from tools.shared.settings import settings

router = APIRouter()
logger = get_logger(__name__)

# Allowed categories for goal mapping
ALLOWED_CATEGORIES = [
    "dairy", "grains", "halal_meat", "vegetables",
    "fruits", "beverages", "snacks", "condiments",
]

# SQL injection patterns to reject
SQL_INJECTION_PATTERNS = [
    r'\bDROP\b',
    r'\bSELECT\s+\*\b',
    r'\bINSERT\b',
    r'\bDELETE\b',
    r'--',
    r';',
]

# Script injection patterns to reject
SCRIPT_INJECTION_PATTERNS = [
    r'<script>',
    r'javascript:',
]


def sanitize_message(message: str) -> str:
    """Strip whitespace and check for injection patterns."""
    msg = message.strip()
    
    # Check for SQL injection
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, msg, re.IGNORECASE):
            raise ValueError("Invalid input: potential SQL injection detected")
    
    # Check for script injection
    for pattern in SCRIPT_INJECTION_PATTERNS:
        if re.search(pattern, msg, re.IGNORECASE):
            raise ValueError("Invalid input: potential script injection detected")
    
    return msg


async def call_gemini_for_intent(message: str) -> dict:
    """
    Call Gemini 1.5 Flash to extract structured intent from customer message.
    
    In mock mode, returns canned responses. In production, calls Vertex AI.
    """
    if settings.use_mock:
        # Mock implementation - simple keyword matching
        msg_lower = message.lower()
        
        # Extract goal
        if "weekly" in msg_lower or "week" in msg_lower:
            goal = "weekly groceries"
        elif "biryani" in msg_lower:
            goal = "biryani ingredients"
        elif "breakfast" in msg_lower:
            goal = "breakfast items"
        elif "milk" in msg_lower or "urgent" in msg_lower:
            goal = "milk"
        else:
            goal = "grocery shopping"
        
        # Extract dietary preference
        if "halal" in msg_lower:
            dietary = "halal"
        elif "vegetarian" in msg_lower:
            dietary = "vegetarian"
        elif "vegan" in msg_lower:
            dietary = "vegan"
        else:
            dietary = "none"
        
        # Extract budget
        budget_match = re.search(r'(\d+)\s*(aed|dirham)', msg_lower)
        budget = float(budget_match.group(1)) if budget_match else None
        
        # Extract household size
        family_match = re.search(r'family of (\d+)', msg_lower)
        if not family_match:
            family_match = re.search(r'(\d+)\s*people', msg_lower)
        household = int(family_match.group(1)) if family_match else None
        
        # Extract urgency
        urgency = "urgent" if any(w in msg_lower for w in ["urgent", "now", "immediately", "right away"]) else "normal"
        
        return {
            "goal": goal,
            "dietary_preference": dietary,
            "budget_aed": budget,
            "household_size": household,
            "urgency": urgency,
        }
    
    # Production implementation - call Gemini via Vertex AI
    # TODO: Implement real Gemini API call
    import google.generativeai as genai
    
    prompt = f"""Extract shopping intent from this customer message and return JSON:
{message}

Return only JSON with these fields:
- goal: what they want to buy (string)
- dietary_preference: "halal", "vegetarian", "vegan", or "none"
- budget_aed: their budget in AED (number or null)
- household_size: number of people (number or null)
- urgency: "normal" or "urgent"

JSON:"""
    
    model = genai.GenerativeModel(settings.gemini_flash_model)
    response = await model.generate_content_async(prompt)
    
    # Parse JSON response
    import json
    try:
        result = json.loads(response.text)
        return result
    except:
        # Fallback to defaults
        return {
            "goal": "grocery shopping",
            "dietary_preference": "none",
            "budget_aed": None,
            "household_size": None,
            "urgency": "normal",
        }


@router.post("/parse-intent", response_model=ParseIntentResponse)
async def parse_intent(request: ParseIntentRequest):
    """
    Extract structured intent from customer's natural language message.
    
    Returns:
        ParseIntentResponse: goal, dietary_preference, budget_aed, household_size, urgency
    
    Raises:
        HTTPException: 400 if validation fails, 500 if Gemini fails
    """
    try:
        # Step 1: Sanitize input
        message = sanitize_message(request.customer_message)
        
        # Step 2: Call Gemini for extraction
        result = await call_gemini_for_intent(message)
        
        # Step 3: Validate extracted values
        if result["dietary_preference"] not in ["halal", "vegetarian", "vegan", "none"]:
            result["dietary_preference"] = "none"
        
        if result["urgency"] not in ["normal", "urgent"]:
            result["urgency"] = "normal"
        
        # Step 4: Log and return
        logger.info(
            "parse_intent_success",
            goal=result["goal"],
            dietary=result["dietary_preference"],
            budget=result["budget_aed"],
        )
        
        return ParseIntentResponse(**result)
        
    except ValueError as e:
        logger.error("parse_intent_validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("parse_intent_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
