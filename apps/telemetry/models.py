import json
import uuid
from django.db import models
from django.contrib.auth.models import User
import io
import docker
import matplotlib
import urllib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

class SITFComponent(models.Model):
    """Class 1: Represents the 5 core SDLC Pillars"""
    component_id = models.CharField(max_length=50, primary_key=True)
    component_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.component_name

    def get_vulnerability_score(self) -> float:
        """
        Computes the current security vulnerability exposure.
        Returns a default baseline for initialization.
        """
        return 0.0
    
class SITFTechnique(models.Model):
    """Class 2: Represents the 75+ Threat Vector Definitions"""
    technique_id = models.CharField(max_length=50, primary_key=True)
    component = models.ForeignKey(SITFComponent, on_delete=models.CASCADE, related_name='techniques')
    technique_name = models.CharField(max_length=150)
    attack_vector_payload = models.TextField()

    def __str__(self):
        return f"{self.technique_id} - {self.technique_name}"

class MitigationControl(models.Model):
    """Class 3: Countermeasure mapping rule baseline"""
    STATUS_CHOICES = [
        ('Mapped', 'Mapped'),
        ('Implemented', 'Implemented'),
        ('Verified', 'Verified'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Mapped'
    )

    control_id = models.CharField(max_length=50, primary_key=True)
    technique = models.ForeignKey(SITFTechnique, on_delete=models.CASCADE, related_name='mitigations')
    control_name = models.CharField(max_length=150)
    detection_rule_reference = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.control_id

class SimulationSession(models.Model):
    """Class 4: Active Sandbox Environment Tracks"""
    STATUS_CHOICES = [
        ('Initializing', 'Initializing'),
        ('Running', 'Running'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions', null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    terminated_at = models.DateTimeField(blank=True, null=True)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Initializing')

    def __str__(self):
        return f"{self.session_id} [{self.current_status}]"

class SimulationActivityLog(models.Model):
    """Class 5: Live Ingested Telemetry Capture Sink"""
    RESULT_CHOICES = [
        ('Breach Success', 'Breach Success'),
        ('Control Blocked', 'Control Blocked'),
    ]
    log_id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(SimulationSession, on_delete=models.CASCADE, related_name='logs')
    technique = models.ForeignKey(SITFTechnique, on_delete=models.CASCADE, related_name='logs')
    captured_log_string = models.TextField()
    execution_result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log #{self.log_id} -> {self.execution_result}"

    def parse_raw_telemetry(self, raw_string: str) -> None:
        """
        Normalizes and injects incoming raw text simulation log streams 
        directly into the analytics data persistence table.
        """
        self.captured_log_string = raw_string
        self.save()


class AnalyticsEngine(models.Model):
    """Class 6: Monolithic computing and reporting hub"""
    chart_format = models.CharField(max_length=10, default="png")
    theme_color = models.JSONField(default=list)

    
    def generate_posture_trend_chart(self, session_id=None) -> bytes:
        """
        Generates a security posture chart from recorded simulation activity.
        Uses actual database records rather than fabricated or external metrics.
        """

        logs = SimulationActivityLog.objects.all()

        # Filter by simulation session when requested
        if session_id:
            logs = logs.filter(session_id=session_id)

        breach_count = logs.filter(
            execution_result='Breach Success'
        ).count()

        blocked_count = logs.filter(
            execution_result='Control Blocked'
        ).count()

        # Prepare chart
        fig, ax = plt.subplots(figsize=(7, 4))

        categories = ['Simulated Breaches', 'Controls Blocked']
        values = [breach_count, blocked_count]

        bars = ax.bar(
            categories,
            values,
            color=['#dc3545', '#198754'],
            width=0.55
        )

        ax.set_title(
            'SITF Security Simulation Results',
            fontsize=13,
            fontweight='bold',
            pad=15
        )

        ax.set_ylabel('Recorded Events')
        ax.grid(axis='y', linestyle='--', alpha=0.25)
        ax.set_axisbelow(True)

        # Display values above bars
        ax.bar_label(bars, padding=4, fontsize=10)

        # Handle empty datasets
        if breach_count == 0 and blocked_count == 0:
            ax.text(
                0.5,
                0.5,
                'No simulation activity recorded',
                transform=ax.transAxes,
                ha='center',
                va='center',
                fontsize=11,
                color='#777777'
            )

        fig.tight_layout()

        buffer = io.BytesIO()

        plt.savefig(
            buffer,
            format=self.chart_format,
            bbox_inches='tight'
        )

        plt.close(fig)

        return buffer.getvalue()



class DashboardController(models.Model):
    """Class 7: Systemic entry state manager"""
    current_view_pillar = models.CharField(max_length=255)

    def get_pillar_status_matrix(self) -> dict:
        return {}


class DockerOrchestration(models.Model):
    """Class 8: Runtime micro-container manager"""
    docker_client_env = models.CharField(max_length=255, default="unix://var/run/docker.sock")
    target_network_name = models.CharField(max_length=255, default="isolated_bridge")

    
    def provision_jenkins_node(self) -> bool:
        """
        Starts an existing Jenkins container or creates it if it does not exist.
        """
        try:
            client = docker.from_env()

            container_name = "sitf_jenkins_sandbox"

            # Check whether the Jenkins container already exists
            try:
                container = client.containers.get(container_name)

                # Reuse an already running container
                if container.status == "running":
                    print("[ORCHESTRATION] Jenkins container is already running.")
                    return True

                # Restart an existing stopped container
                container.start()
                container.reload()

                print("[ORCHESTRATION] Existing Jenkins container restarted.")
                return container.status == "running"

            except docker.errors.NotFound:
                # Create a new container only when none exists
                container = client.containers.run(
                    "sitf-jenkins-python:latest",
                    detach=True,
                    name=container_name,
                    ports={
                        '8080/tcp': 8081,
                        '50000/tcp': 50000
                    },
                    environment={
                        "JAVA_OPTS": "-Djenkins.install.runSetupWizard=false"
                    },
                    volumes={
                        "sitf_jenkins_home": {
                            "bind": "/var/jenkins_home",
                            "mode": "rw"
                        }
                    }
                )

                print("[ORCHESTRATION] New Jenkins container created.")
                return True

        except Exception as e:
            print(f"[ORCHESTRATION ERROR] Container provisioning failed: {e}")
            return False


    def destroy_sandbox_node(self, container_id="sitf_jenkins_sandbox") -> bool:
        """
        Safely halts and demolishes active runtime simulation container blocks.
        """
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
            container.stop(timeout=5)
            return True
        except Exception as e:
            print(f"[ORCHESTRATION ERROR] Container breakdown failed: {e}")
            return False