from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from core.models import Child
from assessment.models import Assessment
from .models import Result
from .services import get_or_generate_result


@login_required
def overview(request):
    """
    Renders the Results Overview page.
    Strictly displays results for children owned by the authenticated parent/educator.
    If the active child in session belongs to this user and has completed assessments,
    displays their report cards. Otherwise, renders the informational overview.
    """
    # Retrieve only children owned by the logged-in user
    user_children = list(request.user.children.all().order_by('-created_at'))
    active_child_id = request.session.get('active_child_id')
    active_child = None

    if active_child_id:
        # Strictly verify active_child belongs to request.user
        active_child = next((c for c in user_children if c.id == active_child_id), None)

    if not active_child and user_children:
        active_child = user_children[0]
        request.session['active_child_id'] = active_child.id

    completed_assessments = []
    if active_child:
        completed_qs = active_child.assessments.filter(
            status=Assessment.AssessmentStatus.COMPLETED
        ).order_by('-completed_at', '-id')

        for assessment in completed_qs:
            try:
                # Ensure result exists for each completed assessment
                result = get_or_generate_result(assessment)
                completed_assessments.append({
                    'assessment': assessment,
                    'result': result,
                })
            except ValueError:
                # In case of any incomplete anomaly, skip
                pass

    context = {
        'page_title': 'Assessment Results & Insights | MindBloom',
        'active_nav': 'results',
        'brand_name': 'MindBloom',
        'child': active_child,
        'user_children': user_children,
        'completed_assessments': completed_assessments,
        'has_active_results': bool(completed_assessments),
    }
    return render(request, 'results/overview.html', context)


@login_required
def assessment_report(request, assessment_id):
    """
    Generates or retrieves the evaluation result for a completed assessment
    and renders the corresponding comprehensive report (Aptitude or Interest).
    Strictly enforces child ownership and session isolation.
    """
    assessment = get_object_or_404(Assessment.objects.select_related('child'), pk=assessment_id)

    # Strict ownership check: child must belong to request.user
    if assessment.child.owner_id is None or assessment.child.owner_id != request.user.id:
        raise PermissionDenied("You are not authorized to view this assessment report.")

    # Authorization Check: prevent cross-user session access
    active_child_id = request.session.get('active_child_id')
    if active_child_id and active_child_id != assessment.child_id:
        active_child = Child.objects.filter(pk=active_child_id).first()
        if active_child and (active_child.owner_id is None or active_child.owner_id != request.user.id):
            raise PermissionDenied("You are not authorized to view another child's assessment report.")

    # Synchronize active child in session
    request.session['active_child_id'] = assessment.child_id

    # Must be completed
    if assessment.status != Assessment.AssessmentStatus.COMPLETED:
        messages.warning(request, "Assessment results are only available once all questions are submitted.")
        return redirect('assessment:question', assessment_id=assessment.id, question_index=1)

    try:
        result = get_or_generate_result(assessment)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('assessment:selection', child_id=assessment.child_id)

    context = {
        'page_title': f"{assessment.get_assessment_type_display()} Report \u2022 {assessment.child.name}",
        'active_nav': 'results',
        'assessment': assessment,
        'child': assessment.child,
        'result': result,
        'brand_name': 'MindBloom',
    }

    if assessment.assessment_type == Assessment.AssessmentType.APTITUDE:
        return render(request, 'results/aptitude_report.html', context)
    else:
        return render(request, 'results/interest_report.html', context)


@login_required
def result_detail(request, result_id):
    """
    Convenience view to access a report directly via result ID.
    Strictly enforces child ownership and redirects to the canonical assessment_report route.
    """
    result = get_object_or_404(Result.objects.select_related('assessment__child'), pk=result_id)
    if (
        result.assessment.child.owner_id is None
        or result.assessment.child.owner_id != request.user.id
    ):
        raise PermissionDenied("You are not authorized to view this assessment report.")
    return redirect('results:assessment_report', assessment_id=result.assessment_id)
