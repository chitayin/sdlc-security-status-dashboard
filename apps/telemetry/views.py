from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import DockerOrchestration, SITFComponent, SITFTechnique, SimulationSession, SimulationActivityLog, AnalyticsEngine, DashboardController

@login_required
def dashboard_controller(request):
    """
    Upgraded controller handling layout states, Docker orchestration hooks, 
    and direct interactive live threat simulation injections.
    """
    controller, _ = DashboardController.objects.get_or_create(id=1, defaults={'current_view_pillar': 'Core SDLC'})
    orchestrator, _ = DockerOrchestration.objects.get_or_create(id=1)
    
    status_alert = None
    
    if request.method == "POST":
        action = request.POST.get("action")
        print("SIMULATION POST RECEIVED:", action, request.POST.get("technique_id"))
        # --- Handle Docker Sandbox Buttons ---
        if action == "provision":
            success = orchestrator.provision_jenkins_node()
            status_alert = "Jenkins Sandbox Container Provisioned via Docker Daemon!" if success else "Sandbox simulation bypassed: Local Docker engine not running. Using local fallback runtime environment."
        elif action == "destroy":
            success = orchestrator.destroy_sandbox_node()
            status_alert = "Jenkins Sandbox Container Safely Demolished." if success else " Local sandbox teardown skipped: No active Docker footprint found."
            
        # --- Handle Interactive Threat Simulation Triggers ---
        elif action == "simulate_threat":
            technique_id = request.POST.get("technique_id")
            technique = SITFTechnique.objects.filter(technique_id=technique_id).first()
            
            if technique:
                # 1. Ensure an active tracking session exists
                session, _ = SimulationSession.objects.get_or_create(current_status='Running')
                
                has_verified_control = technique.mitigations.filter(
                    status='Verified'
                ).exists()

                # 3. Determine the controlled simulation outcome
                simulated_result = (
                    'Control Blocked'
                    if has_verified_control
                    else 'Breach Success'
                )
                
                # 4. Save directly into the database log sink
                simulated_log = (
                    f"SIMULATION EVENT // "
                    f"PILLAR: {technique.component.component_name} // "
                    f"TECHNIQUE: {technique.technique_name} // "
                    f"VERIFIED CONTROL: {has_verified_control} // "
                    f"RESULT: {simulated_result}"
                )

                SimulationActivityLog.objects.create(
                    session=session,
                    technique=technique,
                    execution_result=simulated_result,
                    captured_log_string=simulated_log
                )
                
                status_alert = f"Simulated {technique.technique_name} ({technique_id}) -> Result: {simulated_result}!"

    # Gather data components
    components = SITFComponent.objects.all()

    context = {
        "current_pillar": controller.current_view_pillar,
        "components": components,
        "status_alert": status_alert
    }
    return render(request, "telemetry/dashboard.html", context)


@login_required
def analytics_engine(request):
    """
    Processes real-time inbound logs and handles complex chart asset requests via AnalyticsEngine.
    """
    # Handle incoming telemetry ingestion payload via POST
    if request.method == 'POST':
        raw_log = request.POST.get('log_string', '')
        session_id = request.POST.get('session_id')
        technique_id = request.POST.get('technique_id')
        result = request.POST.get('execution_result', 'Control Blocked')
        
        if raw_log and session_id and technique_id:
            # Instantiate an isolated log sink entry using the model logic
            log_entry = SimulationActivityLog(
                session_id=session_id,
                technique_id=technique_id,
                execution_result=result
            )
            log_entry.parse_raw_telemetry(raw_log)
            
            return JsonResponse({"status": "ingested", "log_id": log_entry.log_id})
        return JsonResponse({"error": "Missing parameters"}, status=400)
        
    # Handle baseline analytical trend chart delivery via GET
    session_id = request.GET.get('session_id')
    engine, _ = AnalyticsEngine.objects.get_or_create(id=1)
    
    # Return binary image string content matching requested parameters
    chart_bytes = engine.generate_posture_trend_chart(session_id)
    return HttpResponse(chart_bytes, content_type=f"image/{engine.chart_format}")



