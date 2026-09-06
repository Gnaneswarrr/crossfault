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


AUTH_TOPOLOGY_PATH = [
    "Physician Portal",
    "Identity Provider",
    "Patient Records API",
    "Results Database",
]


ICU_TOPOLOGY_PATH = [
    "Bedside ICU Monitor",
    "Telemetry Ingestion Service",
    "ICU Gateway Router",
    "Central Clinical Dashboard",
]


PHARMACY_TOPOLOGY_PATH = [
    "e-Prescribing Portal",
    "Pharmacy Verification Service",
    "Drug Interaction Gateway",
    "Automated Medication Dispenser",
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


def create_cf002_scenario() -> Scenario:
    """
    Creates scenario CF-002: Physician Portal Auth Failure.

    Contains 4 network candidates around deployment time:
    1. LIS_PATH_INTERRUPTION (irrelevant background noise)
    2. DNS_CHANGE (irrelevant TTL update for external vendor)
    3. ROUTE_CHANGE (irrelevant BGP update)
    4. ACCESS_RULE_CHANGE (causal event blocking Identity Provider -> Patient Records API)
    """
    candidates = [
        NetworkCandidate(
            candidate_id="NET-011",
            candidate_type=CandidateType.LIS_PATH_INTERRUPTION,
            description="Background LIS path degradation noise",
            affected_source="Specimen Processing Service",
            affected_destination="LIS Gateway",
            interrupts_path=False,
        ),
        NetworkCandidate(
            candidate_id="NET-012",
            candidate_type=CandidateType.DNS_CHANGE,
            description="DNS TTL update for external vendor",
            affected_source="Identity Provider",
            affected_destination="External Vendor",
            interrupts_path=False,
        ),
        NetworkCandidate(
            candidate_id="NET-013",
            candidate_type=CandidateType.ROUTE_CHANGE,
            description="BGP route update for non-critical subnet",
            affected_source="Patient Records API",
            affected_destination="Non-Critical Subnet",
            interrupts_path=False,
        ),
        NetworkCandidate(
            candidate_id="NET-014",
            candidate_type=CandidateType.ACCESS_RULE_CHANGE,
            description="Zero-trust firewall rule misconfiguration blocking identity token exchange",
            affected_source="Identity Provider",
            affected_destination="Patient Records API",
            interrupts_path=True,
        ),
    ]

    app_input = ApplicationInput(
        request_id="REQ-HC-20055",
        workload_type="PhysicianLogin",
        target_environment="Production",
        specimen_type="N/A",
    )

    return Scenario(
        scenario_id="CF-002",
        name="Physician Portal Auth Failure",
        description="Simulated deployment failure caused by a zero-trust firewall rule blocking token exchange.",
        topology_path=AUTH_TOPOLOGY_PATH,
        candidates=candidates,
        application_input=app_input,
    )


def create_cf004_scenario() -> Scenario:
    """
    Creates scenario CF-004: ICU Telemetry Egress BGP Route Failure.

    Contains 4 network candidates around deployment time:
    1. ACCESS_RULE_CHANGE (irrelevant background metrics cluster ACL)
    2. DNS_CHANGE (irrelevant TTL refresh for remote archive)
    3. ROUTE_CHANGE (causal event blackholing ICU gateway egress traffic)
    4. LIS_PATH_INTERRUPTION (irrelevant path jitter on secondary backup link)
    """
    candidates = [
        NetworkCandidate(
            candidate_id="NET-031",
            candidate_type=CandidateType.ACCESS_RULE_CHANGE,
            description="Firewall egress ACL modification for background metrics cluster",
            affected_source="Telemetry Ingestion Service",
            affected_destination="Metrics Cluster",
            interrupts_path=False,
        ),
        NetworkCandidate(
            candidate_id="NET-032",
            candidate_type=CandidateType.DNS_CHANGE,
            description="Internal DNS TTL refresh for remote telemetry archive",
            affected_source="Central Clinical Dashboard",
            affected_destination="Telemetry Archive",
            interrupts_path=False,
        ),
        NetworkCandidate(
            candidate_id="NET-033",
            candidate_type=CandidateType.ROUTE_CHANGE,
            description="BGP route table withdrawal blackholing ICU gateway egress traffic",
            affected_source="Telemetry Ingestion Service",
            affected_destination="ICU Gateway Router",
            interrupts_path=True,
        ),
        NetworkCandidate(
            candidate_id="NET-034",
            candidate_type=CandidateType.LIS_PATH_INTERRUPTION,
            description="Background path jitter on secondary legacy backup link",
            affected_source="ICU Gateway Router",
            affected_destination="Legacy Backup Link",
            interrupts_path=False,
        ),
    ]

    app_input = ApplicationInput(
        request_id="REQ-ICU-40081",
        workload_type="ICUTelemetryStream",
        target_environment="Production",
        specimen_type="N/A",
    )

    return Scenario(
        scenario_id="CF-004",
        name="ICU Telemetry Egress BGP Route Failure",
        description="Simulated ICU telemetry deployment failure caused by BGP route table withdrawal.",
        topology_path=ICU_TOPOLOGY_PATH,
        candidates=candidates,
        application_input=app_input,
    )


def create_cf005_scenario() -> Scenario:
    """
    Creates scenario CF-005: EHR Pharmacy Dispense DNS Resolution Failure.

    Contains 4 network candidates around deployment time:
    1. LIS_PATH_INTERRUPTION (irrelevant path latency on secondary lab sync)
    2. ACCESS_RULE_CHANGE (irrelevant ACL rule modification for audit logging daemon)
    3. DNS_CHANGE (causal event mapping Drug Interaction Gateway to unresolvable hostname)
    4. ROUTE_CHANGE (irrelevant static route maintenance update on secondary interface)
    """
    candidates = [
        NetworkCandidate(
            candidate_id="NET-041",
            candidate_type=CandidateType.LIS_PATH_INTERRUPTION,
            description="Transient path latency on secondary lab sync interface",
            affected_source="Pharmacy Verification Service",
            affected_destination="Secondary Lab Sync",
            interrupts_path=False,
        ),
        NetworkCandidate(
            candidate_id="NET-042",
            candidate_type=CandidateType.ACCESS_RULE_CHANGE,
            description="Ingress ACL rule modification for audit logging daemon",
            affected_source="Drug Interaction Gateway",
            affected_destination="Audit Logging Server",
            interrupts_path=False,
        ),
        NetworkCandidate(
            candidate_id="NET-043",
            candidate_type=CandidateType.DNS_CHANGE,
            description="Internal DNS CNAME update mapping Drug Interaction Gateway to unresolvable hostname",
            affected_source="Pharmacy Verification Service",
            affected_destination="Drug Interaction Gateway",
            interrupts_path=True,
        ),
        NetworkCandidate(
            candidate_id="NET-044",
            candidate_type=CandidateType.ROUTE_CHANGE,
            description="Static route maintenance update on secondary gateway interface",
            affected_source="Drug Interaction Gateway",
            affected_destination="Backup Interface",
            interrupts_path=False,
        ),
    ]

    app_input = ApplicationInput(
        request_id="REQ-PHARM-50092",
        workload_type="PharmacyMedDispense",
        target_environment="Production",
        specimen_type="N/A",
    )

    return Scenario(
        scenario_id="CF-005",
        name="EHR Pharmacy Dispense DNS Resolution Failure",
        description="Simulated EHR pharmacy dispense failure caused by internal DNS CNAME resolution failure.",
        topology_path=PHARMACY_TOPOLOGY_PATH,
        candidates=candidates,
        application_input=app_input,
    )
