from django.test import TestCase
from .models import SITFComponent, SITFTechnique, SimulationActivityLog, SimulationSession
from django.urls import reverse
from django.contrib.auth import get_user_model

class TelemetryFrameworkIngestionTests(TestCase):
    """
    Validates structural consistency and operational verification of 
    Step 2 framework ingestion and JSON fixture assets.
    """

    fixtures = ['sitf_data.json']

    def setUp(self):
        self.session = SimulationSession.objects.create(
            current_status='Running'
    )

    def test_fixture_components_ingested(self):
        """Verify all 5 core infrastructure components are properly populated."""
        expected_components = ['COMP-IDE', 'COMP-VCS', 'COMP-CICD', 'COMP-REG', 'COMP-PROD']
        
        for comp_id in expected_components:
            component = SITFComponent.objects.filter(component_id=comp_id).first()
            self.assertIsNotNone(component, f"Component {comp_id} was not found in database records.")
            self.assertEqual(component.get_vulnerability_score(), 0.0)

    def test_fixture_techniques_and_relations(self):
        """Validate that Threat Vector definitions are mapped to correct structural parent components."""
        cache_poison = SITFTechnique.objects.filter(technique_id='T1001').first()
        self.assertIsNotNone(cache_poison)
        self.assertEqual(cache_poison.component.component_id, 'COMP-CICD')
        self.assertEqual(cache_poison.attack_vector_payload, 'simulations/action_cache_poison.sh')

        imposter = SITFTechnique.objects.filter(technique_id='T1002').first()
        self.assertIsNotNone(imposter)
        self.assertEqual(imposter.component.component_id, 'COMP-VCS')

    def test_component_reverse_lookup_counts(self):
        """Confirm that reverse relational fields resolve cleanly via related_name configurations."""
        vcs_component = SITFComponent.objects.get(component_id='COMP-VCS')
        self.assertTrue(vcs_component.techniques.filter(technique_id='T1002').exists())


    from apps.telemetry.models import SITFTechnique, SimulationActivityLog, SimulationSession


    def test_log_parsing_pipeline_success(self):
            """TC-06-MAP: Verify telemetry parsing creates accurate records upon successful exploit simulation."""
            # Query prerequisite seeded records
            session_instance = self.session
            technique_instance = SITFTechnique.objects.get(technique_id='T1001')

            # Instantiate empty target log entry
            log_entry = SimulationActivityLog(
                session=session_instance,
                technique=technique_instance,
                execution_result='Breach Success'
            )
            
            # Fire model parsing framework logic
            mock_raw_stream = "INBOUND_STREAM // INJECT_TARGET: Jenkins_Node // SIG_MATCH: REVERSE_SHELL // STATUS: ESCALATED"
            log_entry.parse_raw_telemetry(mock_raw_stream)

            # Assert data layer capture
            self.assertIsNotNone(log_entry.log_id)
            self.assertEqual(log_entry.captured_log_string, mock_raw_stream)
            self.assertEqual(log_entry.execution_result, 'Breach Success')

    def test_log_parsing_pipeline_blocked(self):
        """Verify telemetry engine handles and commits mitigated countermeasure payload logs cleanly."""
        session_instance = self.session
        technique_instance = SITFTechnique.objects.get(technique_id='T1002')

        log_entry = SimulationActivityLog(
            session=session_instance,
            technique=technique_instance,
            execution_result='Control Blocked'
        )
        
        mock_blocked_stream = "INBOUND_STREAM // INJECT_TARGET: Git_VCS // CAPTURE_RULE: IMPOSTER_COMMIT // STATUS: DROPPED"
        log_entry.parse_raw_telemetry(mock_blocked_stream)

        self.assertEqual(log_entry.execution_result, 'Control Blocked')


class AuthenticationAccessTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="TestPassword123!"
        )

    def test_dashboard_redirects_unauthenticated_user(self):
        response = self.client.get(
            reverse("telemetry:dashboard")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_analytics_redirects_unauthenticated_user(self):
        response = self.client.get(
            reverse("telemetry:analytics_engine")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_authenticated_user_can_access_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("telemetry:dashboard")
        )

        self.assertEqual(response.status_code, 200)