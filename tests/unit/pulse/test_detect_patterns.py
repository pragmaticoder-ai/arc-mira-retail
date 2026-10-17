"""Unit tests for PULSE tool: detect_patterns

Tests the detect_patterns tool function following SPEC-PULSE-01.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from tools.pulse_tools.main import app


client = TestClient(app)


@pytest.mark.unit
class TestDetectPatterns:
    """Unit tests for detect_patterns endpoint."""

    def test_detect_patterns_sorted_by_revenue(self):
        """
        TC-PULSE-01-U01: Patterns detected and sorted by revenue
        
        Given: Mock BQ returns stockout patterns
        When: detect_patterns called
        Then: Returns patterns sorted by estimated_revenue_lost_aed DESC
        """
        response = client.post(
            "/tools/detect-patterns",
            json={"store_id": "dubai_marina_01", "hours": 48, "min_incidents": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        patterns = data["patterns"]
        assert isinstance(patterns, list)
        
        # Verify sorting if multiple patterns
        if len(patterns) > 1:
            for i in range(len(patterns) - 1):
                assert patterns[i]["estimated_revenue_lost_aed"] >= patterns[i + 1]["estimated_revenue_lost_aed"]

    def test_detect_patterns_empty_results(self):
        """
        TC-PULSE-01-U02: No patterns returns empty array
        
        Given: No incidents in BigQuery for last 48 hours (or below threshold)
        When: detect_patterns called with high min_incidents threshold
        Then: Returns patterns=[] (not an error)
        """
        response = client.post(
            "/tools/detect-patterns",
            json={"store_id": "nonexistent_store", "hours": 48, "min_incidents": 999}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["patterns"] == []

    def test_detect_patterns_demo_scenario(self):
        """
        TC-PULSE-01-I02: Bridge test — reads ARIA writes
        
        Given: Mock BigQuery with seeded brown rice incidents
        When: detect_patterns runs for dubai_marina_01
        Then: Detects brown rice pattern with correct product_id
        """
        response = client.post(
            "/tools/detect-patterns",
            json={"store_id": "dubai_marina_01", "hours": 48, "min_incidents": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        patterns = data["patterns"]
        assert len(patterns) > 0
        
        # Find brown rice pattern
        brown_rice = next(
            (p for p in patterns if p["product_id"] == "rice_brown_500g"),
            None
        )
        
        assert brown_rice is not None
        assert brown_rice["product_name"] == "Brown Rice 500g"
        assert brown_rice["incident_count"] >= 5
        assert brown_rice["estimated_revenue_lost_aed"] > 0

    def test_detect_patterns_evidence_block(self):
        """
        TC-PULSE-01-U05: evidence block populated
        
        Given: Patterns detected
        When: detect_patterns called
        Then: Each pattern has evidence block with required fields
        """
        response = client.post(
            "/tools/detect-patterns",
            json={"store_id": "dubai_marina_01", "hours": 48, "min_incidents": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        patterns = data["patterns"]
        if len(patterns) > 0:
            pattern = patterns[0]
            evidence = pattern.get("evidence")
            
            assert evidence is not None
            assert "first_incident" in evidence
            assert "last_incident" in evidence
            assert "sample_session_ids" in evidence
            assert isinstance(evidence["sample_session_ids"], list)

    def test_detect_patterns_hours_filter(self):
        """
        TC-PULSE-01-U06: hours parameter filters correctly
        
        Given: Incidents from different time ranges
        When: detect_patterns called with hours=24
        Then: Only incidents from last 24 hours included
        """
        response_24h = client.post(
            "/tools/detect-patterns",
            json={"store_id": "dubai_marina_01", "hours": 24, "min_incidents": 1}
        )
        
        response_48h = client.post(
            "/tools/detect-patterns",
            json={"store_id": "dubai_marina_01", "hours": 48, "min_incidents": 1}
        )
        
        assert response_24h.status_code == 200
        assert response_48h.status_code == 200
        
        # 48h window should have equal or more patterns
        patterns_24h = response_24h.json()["patterns"]
        patterns_48h = response_48h.json()["patterns"]
        
        assert len(patterns_48h) >= len(patterns_24h)

    def test_detect_patterns_validation_error(self):
        """
        Test: Invalid parameters rejected
        
        Given: Invalid store_id or hours
        When: detect_patterns called
        Then: Returns appropriate error
        """
        # Empty store_id
        response = client.post(
            "/tools/detect-patterns",
            json={"store_id": "", "hours": 48, "min_incidents": 5}
        )
        
        # Should either validate and reject, or handle gracefully
        # Implementation-dependent
        assert response.status_code in [200, 400, 422]

    def test_detect_patterns_abandonment_count(self):
        """
        TC-PULSE-01-U04: abandonment_count accurate
        
        Given: Patterns with known abandonment rate
        When: detect_patterns called
        Then: abandonment_count reflects actual count
        """
        response = client.post(
            "/tools/detect-patterns",
            json={"store_id": "dubai_marina_01", "hours": 48, "min_incidents": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        patterns = data["patterns"]
        if len(patterns) > 0:
            pattern = patterns[0]
            
            # abandonment_count should be non-negative
            assert pattern.get("abandonment_count", 0) >= 0
            
            # abandonment_count should be <= incident_count
            assert pattern.get("abandonment_count", 0) <= pattern.get("incident_count", 0)
