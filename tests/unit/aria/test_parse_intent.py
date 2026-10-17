"""Unit tests for ARIA tool: parse_intent

Tests the parse_intent tool function following SPEC-ARIA-01.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from tools.aria_tools.main import app


client = TestClient(app)


@pytest.mark.unit
class TestParseIntent:
    """Unit tests for parse_intent endpoint."""

    def test_parse_intent_full_message(self):
        """
        TC-ARIA-01-U01: Happy path — full intent extraction
        
        Given: "I need halal groceries for the week, family of 4, under AED 300"
        When: parse_intent is called
        Then: Returns goal, dietary_preference, budget, household_size
        """
        response = client.post(
            "/tools/parse-intent",
            json={"customer_message": "I need halal groceries for the week, family of 4, under AED 300"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["goal"] == "weekly groceries"
        assert data["dietary_preference"] == "halal"
        assert data["budget_aed"] == 300.0
        assert data["household_size"] == 4
        assert data["urgency"] == "normal"

    def test_parse_intent_vegetarian(self):
        """
        TC-ARIA-01-U02: Dietary preference extraction — vegetarian
        
        Given: "I need vegetarian food for 2 people"
        When: parse_intent is called
        Then: dietary_preference="vegetarian", household_size=2
        """
        response = client.post(
            "/tools/parse-intent",
            json={"customer_message": "I need vegetarian food for 2 people"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["dietary_preference"] == "vegetarian"
        assert data["household_size"] == 2

    def test_parse_intent_urgent(self):
        """
        TC-ARIA-01-U03: Urgency extraction
        
        Given: "I need milk urgently right now"
        When: parse_intent is called
        Then: urgency="urgent", goal="milk"
        """
        response = client.post(
            "/tools/parse-intent",
            json={"customer_message": "I need milk urgently right now"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["urgency"] == "urgent"
        assert data["goal"] == "milk"

    def test_parse_intent_partial_message(self):
        """
        TC-ARIA-01-U04: Missing fields default correctly
        
        Given: "I need some groceries"
        When: parse_intent is called
        Then: goal="groceries", dietary_preference="none", others null
        """
        response = client.post(
            "/tools/parse-intent",
            json={"customer_message": "I need some groceries"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["goal"] == "grocery shopping"
        assert data["dietary_preference"] == "none"
        assert data["budget_aed"] is None
        assert data["household_size"] is None
        assert data["urgency"] == "normal"

    def test_parse_intent_empty_message(self):
        """
        TC-ARIA-01-U05: Empty message rejected
        
        Given: customer_message=""
        When: parse_intent is called
        Then: Returns 422 validation error
        """
        response = client.post(
            "/tools/parse-intent",
            json={"customer_message": ""}
        )
        
        assert response.status_code == 422  # Validation error

    def test_parse_intent_message_too_long(self):
        """
        TC-ARIA-01-U06: Message too long rejected
        
        Given: customer_message="a" * 1001
        When: parse_intent is called
        Then: Returns 422 validation error
        """
        response = client.post(
            "/tools/parse-intent",
            json={"customer_message": "a" * 1001}
        )
        
        assert response.status_code == 422  # Validation error

    def test_parse_intent_sql_injection_rejected(self):
        """
        TC-ARIA-01-U07: SQL injection rejected
        
        Given: customer_message with SQL injection
        When: parse_intent is called
        Then: Returns 400 bad request
        """
        response = client.post(
            "/tools/parse-intent",
            json={"customer_message": "SELECT * FROM inventory; DROP TABLE orders;"}
        )
        
        assert response.status_code == 400
        assert "injection" in response.json()["detail"].lower()

    def test_parse_intent_mixed_language(self):
        """
        TC-ARIA-01-U10: Arabic/mixed language message
        
        Given: "أريد groceries for the week, halal, AED 200"
        When: parse_intent is called
        Then: dietary_preference="halal", budget_aed=200.0
        """
        response = client.post(
            "/tools/parse-intent",
            json={"customer_message": "أريد groceries for the week, halal, AED 200"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["dietary_preference"] == "halal"
        assert data["budget_aed"] == 200.0
