from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from .forms import MindBloomAuthenticationForm, UserRegistrationForm, ChildRegistrationForm
from .models import Child
from assessment.models import Assessment, Answer
from results.models import Result
from results.services import APTITUDE_CATEGORIES, INTEREST_CATEGORIES


def home(request):
    """
    Renders the polished MindBloom homepage with hero, assessment categories,
    workflow explanation, and benefit highlights.
    """
    context = {
        'page_title': 'Home',
        'active_nav': 'home',
        'project_title': 'Child Aptitude & Interest Assessment System',
        'brand_name': 'MindBloom',
    }
    return render(request, 'core/home.html', context)


def about(request):
    """
    Renders the About page explaining the educational philosophy,
    methodology, and academic context of the semester project.
    """
    context = {
        'page_title': 'About MindBloom',
        'active_nav': 'about',
        'project_title': 'Child Aptitude & Interest Assessment System',
        'brand_name': 'MindBloom',
    }
    return render(request, 'core/about.html', context)


def contact(request):
    """
    Renders the Contact page providing academic institution details,
    project laboratory location, and feedback placeholders.
    """
    context = {
        'page_title': 'Contact & Inquiries',
        'active_nav': 'contact',
        'project_title': 'Child Aptitude & Interest Assessment System',
        'brand_name': 'MindBloom',
    }
    return render(request, 'core/contact.html', context)


def login_view(request):
    """
    Authenticates registered users (parents/educators) using Django's built-in
    AuthenticationForm, authenticate(), and login() functions.
    Handles next-parameter redirects and friendly failure messaging.
    """
    if request.user.is_authenticated:
        return redirect('results:overview')

    redirect_to = request.POST.get('next') or request.GET.get('next') or ''

    if request.method == 'POST':
        form = MindBloomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            if redirect_to and redirect_to.startswith('/'):
                return redirect(redirect_to)
            return redirect('results:overview')
        else:
            messages.error(request, "Invalid username or password. Please check your credentials and try again.")
    else:
        form = MindBloomAuthenticationForm(request)

    context = {
        'page_title': 'Account Login | MindBloom',
        'active_nav': 'login',
        'form': form,
        'next': redirect_to,
        'brand_name': 'MindBloom',
    }
    return render(request, 'core/login.html', context)


def register_user(request):
    """
    Registers a new parent/educator account using Django's UserCreationForm.
    Automatically logs the user in upon creation and redirects to child setup.
    """
    if request.user.is_authenticated:
        return redirect('results:overview')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to MindBloom, {user.first_name or user.username}! Your account has been created."
            )
            return redirect('assessment:register')
        else:
            messages.error(request, "Please correct the errors in the registration form below.")
    else:
        form = UserRegistrationForm()

    context = {
        'page_title': 'Create Parent / Educator Account | MindBloom',
        'active_nav': 'register',
        'form': form,
        'brand_name': 'MindBloom',
    }
    return render(request, 'core/register.html', context)


def logout_view(request):
    """
    Logs out the authenticated user, completely clears child session data,
    and redirects to the homepage with a confirmation alert.
    """
    # Explicitly clear child-specific session information
    request.session.pop('active_child_id', None)
    logout(request)
    messages.info(request, "You have been successfully logged out. Thank you for using MindBloom!")
    return redirect('core:home')


def register_redirect(request):
    """
    Convenience route for legacy /register/ paths.
    Redirects unauthenticated visitors to account registration,
    and authenticated users to child profile registration.
    """
    if request.user.is_authenticated:
        return redirect('assessment:register')
    return redirect('core:register')


@login_required
def dashboard(request):
    """
    Parent / Educator Dashboard.
    Acts as the central workspace for authenticated users to monitor child profiles,
    view real-time statistics, inspect progress, and trigger new assessments.
    """
    user_children = Child.objects.filter(owner=request.user).order_by('-created_at')
    total_children = user_children.count()

    user_assessments = Assessment.objects.filter(child__owner=request.user)
    total_assessments = user_assessments.count()
    completed_assessments_count = user_assessments.filter(status=Assessment.AssessmentStatus.COMPLETED).count()
    pending_assessments_count = user_assessments.filter(status=Assessment.AssessmentStatus.PENDING).count()

    # Prefetch child assessments for performance
    children_data = []
    children_with_assessments = user_children.prefetch_related('assessments__result')
    for child in children_with_assessments:
        child_asmts = list(child.assessments.all())
        asmt_total = len(child_asmts)
        c_count = sum(1 for a in child_asmts if a.status == Assessment.AssessmentStatus.COMPLETED)
        p_count = asmt_total - c_count

        # Most recent assessment date (completed_at or created_at)
        latest_date = None
        if child_asmts:
            latest_asmt = max(child_asmts, key=lambda a: a.completed_at or a.created_at)
            latest_date = latest_asmt.completed_at or latest_asmt.created_at

        children_data.append({
            'child': child,
            'total_assessments': asmt_total,
            'completed_count': c_count,
            'pending_count': p_count,
            'latest_assessment_date': latest_date,
        })

    context = {
        'page_title': 'Parent Dashboard | MindBloom',
        'active_nav': 'dashboard',
        'parent_name': request.user.first_name or request.user.username,
        'current_date': timezone.now(),
        'total_children': total_children,
        'total_assessments': total_assessments,
        'completed_assessments_count': completed_assessments_count,
        'pending_assessments_count': pending_assessments_count,
        'children_data': children_data,
        'brand_name': 'MindBloom',
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def child_add(request):
    """
    Adds a new child profile assigned to the authenticated user directly from the dashboard.
    """
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.owner = request.user
            child.save()
            request.session['active_child_id'] = child.id
            messages.success(request, f"Child profile for '{child.name}' has been created successfully!")
            return redirect('core:child_detail', child_id=child.id)
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = ChildRegistrationForm()

    context = {
        'page_title': "Add Child Profile | MindBloom",
        'active_nav': 'dashboard',
        'form': form,
        'brand_name': 'MindBloom',
    }
    return render(request, 'core/child_add.html', context)


@login_required
def child_detail(request, child_id):
    """
    Dedicated Child Profile, Assessment Summary, Complete History, and Attempt Comparison.
    Enforces strict ownership: records not owned by request.user raise PermissionDenied.
    """
    child = get_object_or_404(Child, pk=child_id)
    if child.owner_id is None or child.owner_id != request.user.id:
        raise PermissionDenied("You are not authorized to access this child's profile.")

    # Synchronize active child in session
    request.session['active_child_id'] = child.id

    # All assessments for this child, newest first
    all_assessments = list(
        child.assessments.select_related('result')
        .order_by('-created_at', '-id')
    )

    # Separate by assessment type
    aptitude_assessments = [a for a in all_assessments if a.assessment_type == Assessment.AssessmentType.APTITUDE]
    interest_assessments = [a for a in all_assessments if a.assessment_type == Assessment.AssessmentType.INTEREST]

    # Aptitude Summary Metrics
    apt_total = len(aptitude_assessments)
    apt_completed = [a for a in aptitude_assessments if a.status == Assessment.AssessmentStatus.COMPLETED]
    apt_pending_count = apt_total - len(apt_completed)
    apt_latest_date = max((a.completed_at or a.created_at for a in aptitude_assessments), default=None)
    apt_latest_completed = max((a for a in apt_completed), key=lambda a: a.completed_at or a.created_at, default=None)
    apt_latest_result = getattr(apt_latest_completed, 'result', None) if apt_latest_completed else None

    # Interest Summary Metrics
    int_total = len(interest_assessments)
    int_completed = [a for a in interest_assessments if a.status == Assessment.AssessmentStatus.COMPLETED]
    int_pending_count = int_total - len(int_completed)
    int_latest_date = max((a.completed_at or a.created_at for a in interest_assessments), default=None)
    int_latest_completed = max((a for a in int_completed), key=lambda a: a.completed_at or a.created_at, default=None)
    int_latest_result = getattr(int_latest_completed, 'result', None) if int_latest_completed else None

    # Historical Comparison (Section 7)
    # Chronological ordering (oldest to newest) to compare the latest two completed attempts
    apt_chronological = sorted(apt_completed, key=lambda a: a.completed_at or a.created_at)
    apt_comparison = None
    if len(apt_chronological) >= 2:
        prev_apt = apt_chronological[-2]
        curr_apt = apt_chronological[-1]
        prev_res = getattr(prev_apt, 'result', None)
        curr_res = getattr(curr_apt, 'result', None)
        if prev_res and curr_res:
            score_diff = round(curr_res.overall_percentage - prev_res.overall_percentage, 1)
            cat_comparison = []
            for cat in APTITUDE_CATEGORIES:
                p_pct = prev_res.category_scores.get(cat, {}).get('percentage', 0.0) if prev_res.category_scores else 0.0
                c_pct = curr_res.category_scores.get(cat, {}).get('percentage', 0.0) if curr_res.category_scores else 0.0
                cat_comparison.append({
                    'category': cat,
                    'prev_pct': p_pct,
                    'curr_pct': c_pct,
                    'diff': round(c_pct - p_pct, 1),
                })
            apt_comparison = {
                'has_comparison': True,
                'prev_date': prev_apt.completed_at,
                'curr_date': curr_apt.completed_at,
                'prev_pct': prev_res.overall_percentage,
                'curr_pct': curr_res.overall_percentage,
                'diff': score_diff,
                'categories': cat_comparison,
            }

    int_chronological = sorted(int_completed, key=lambda a: a.completed_at or a.created_at)
    int_comparison = None
    if len(int_chronological) >= 2:
        prev_int = int_chronological[-2]
        curr_int = int_chronological[-1]
        prev_res = getattr(prev_int, 'result', None)
        curr_res = getattr(curr_int, 'result', None)
        if prev_res and curr_res:
            cat_comparison = []
            for cat in INTEREST_CATEGORIES:
                p_pct = prev_res.category_distribution.get(cat, {}).get('percentage', 0.0) if prev_res.category_distribution else 0.0
                c_pct = curr_res.category_distribution.get(cat, {}).get('percentage', 0.0) if curr_res.category_distribution else 0.0
                cat_comparison.append({
                    'category': cat,
                    'prev_pct': p_pct,
                    'curr_pct': c_pct,
                    'diff': round(c_pct - p_pct, 1),
                })
            int_comparison = {
                'has_comparison': True,
                'prev_date': prev_int.completed_at,
                'curr_date': curr_int.completed_at,
                'categories': cat_comparison,
            }

    # Format assessment history items
    history_items = []
    for asmt in all_assessments:
        res = getattr(asmt, 'result', None)
        result_display = None
        if asmt.status == Assessment.AssessmentStatus.COMPLETED:
            if asmt.assessment_type == Assessment.AssessmentType.APTITUDE and res:
                result_display = f"{res.overall_percentage}%"
            elif asmt.assessment_type == Assessment.AssessmentType.INTEREST and res:
                top_domains = res.top_interest_categories
                result_display = ", ".join(top_domains[:2]) if top_domains else "Completed"
            else:
                result_display = "Completed"
        else:
            result_display = "—"

        history_items.append({
            'assessment': asmt,
            'result': res,
            'result_display': result_display,
            'is_completed': (asmt.status == Assessment.AssessmentStatus.COMPLETED),
        })

    context = {
        'page_title': f"{child.name}'s Profile & Assessment History | MindBloom",
        'active_nav': 'dashboard',
        'child': child,
        'apt_total': apt_total,
        'apt_completed_count': len(apt_completed),
        'apt_pending_count': apt_pending_count,
        'apt_latest_date': apt_latest_date,
        'apt_latest_result': apt_latest_result,
        'int_total': int_total,
        'int_completed_count': len(int_completed),
        'int_pending_count': int_pending_count,
        'int_latest_date': int_latest_date,
        'int_latest_result': int_latest_result,
        'apt_comparison': apt_comparison,
        'int_comparison': int_comparison,
        'history_items': history_items,
        'brand_name': 'MindBloom',
    }
    return render(request, 'core/child_detail.html', context)


@login_required
def child_edit(request, child_id):
    """
    Allows the authenticated owner to update their child's name, age, gender, and grade.
    Strictly isolated: accessing another user's child raises PermissionDenied.
    """
    child = get_object_or_404(Child, pk=child_id)
    if child.owner_id is None or child.owner_id != request.user.id:
        raise PermissionDenied("You are not authorized to edit this child's profile.")

    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST, instance=child)
        if form.is_valid():
            updated_child = form.save()
            messages.success(request, f"Profile for '{updated_child.name}' updated successfully.")
            return redirect('core:child_detail', child_id=updated_child.id)
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = ChildRegistrationForm(instance=child)

    context = {
        'page_title': f"Edit {child.name}'s Profile | MindBloom",
        'active_nav': 'dashboard',
        'child': child,
        'form': form,
        'brand_name': 'MindBloom',
    }
    return render(request, 'core/child_edit.html', context)


@login_required
def child_delete(request, child_id):
    """
    Safely deletes a child profile with a GET confirmation step explaining
    the cascading deletion of all associated assessments, answers, and reports.
    Strictly isolated: accessing another user's child raises PermissionDenied.
    """
    child = get_object_or_404(Child, pk=child_id)
    if child.owner_id is None or child.owner_id != request.user.id:
        raise PermissionDenied("You are not authorized to delete this child's profile.")

    total_assessments = child.assessments.count()
    aptitude_count = child.assessments.filter(assessment_type=Assessment.AssessmentType.APTITUDE).count()
    interest_count = child.assessments.filter(assessment_type=Assessment.AssessmentType.INTEREST).count()
    results_count = Result.objects.filter(assessment__child=child).count()
    answers_count = Answer.objects.filter(assessment__child=child).count()

    if request.method == 'POST':
        child_name = child.name
        # Clear active child from session if matching
        if request.session.get('active_child_id') == child.id:
            request.session.pop('active_child_id', None)
        child.delete()
        messages.info(request, f"Child profile '{child_name}' and all associated assessments have been deleted.")
        return redirect('core:dashboard')

    context = {
        'page_title': f"Confirm Delete: {child.name} | MindBloom",
        'active_nav': 'dashboard',
        'child': child,
        'total_assessments': total_assessments,
        'aptitude_count': aptitude_count,
        'interest_count': interest_count,
        'results_count': results_count,
        'answers_count': answers_count,
        'brand_name': 'MindBloom',
    }
    return render(request, 'core/child_confirm_delete.html', context)
