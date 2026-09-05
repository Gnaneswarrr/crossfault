"""Scenario definitions for CrossFault simulator."""

from crossfault.models import ApplicationInput, CandidateType, NetworkCandidate, Scenario


HEALTHCARE_TOPOLOGY_PATH = [
    "Clinic",
    "Lab Order Service",
    "Specimen Processing Service",
    "LIS Gateway",
    "Results Service",
    "Results Database",
]


def create_initial_scenario() -> Scenario:
    """
    Creates scenario CF-001: Initial healthcare deployment failure scenario.
    
    Contains 4 network candidates around deployment time:
    1. ROUTE_CHANGE (irrelevant link / external billing)
    2. ACCESS_RULE_CHANGE (irrelevant link / analytics egress)
    3. DNS_CHANGE (irrelevant link / auth domain)
    4. LIS_PATH_INTERRUPTION (causal event targeting Specimen Processing -> LIS Gateway)
    """
    candidates = [
        NetworkCandidate(
            candidate_id="NET-001",
            candidate_type=CandidateType.ROUTE_CHANGE,
            description="BGP route update for external billing gateway",
            affected_source="Clinic",
            affected_destination="External Billing Gateway",
            interrupts_path=False,
        ),
        NetworkCandidate(
            candidate_id="NET-002",
            candidate_type=CandidateType.ACCESS_RULE_CHANGE,
            description="Firewall egress rule modification for analytics cluster",
            affected_source="Lab Order Service",
            affected_destination="Analytics Egress",
            interrupts_path=False,
        ),
        NetworkCandidate(
            candidate_id="NET-003",
            candidate_type=CandidateType.DNS_CHANGE,
            description="Internal DNS record TTL updated for auth service",
            affected_source="Clinic",
            affected_destination="Auth Service",
            interrupts_path=False,
        ),
        NetworkCandidate(
            candidate_id="NET-004",
            candidate_type=CandidateType.LIS_PATH_INTERRUPTION,
            description="LIS network path link degradation / interruption",
            affected_source="Specimen Processing Service",
            affected_destination="LIS Gateway",
            interrupts_path=True,
        ),
    ]

    app_input = ApplicationInput(
        request_id="REQ-HC-10024",
        workload_type="LabResultDeployment",
        target_environment="Production",
        specimen_type="BloodPanel",
    )

    return Scenario(
        scenario_id="CF-001",
        name="Healthcare Deployment with LIS Gateway Path Interruption",
        description="Simulated healthcare deployment failure caused by network path interruption between Specimen Processing and LIS Gateway.",
        topology_path=HEALTHCARE_TOPOLOGY_PATH,
        candidates=candidates,
        application_input=app_input,
    )
