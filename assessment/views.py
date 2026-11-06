from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from core.models import Child
from core.forms import ChildRegistrationForm
from .models import Assessment, Question, Answer
from .forms import QuestionAnswerForm


def overview(request):
    """
    Renders the assessment hub introducing both cognitive aptitude and
    interest exploration tracks with preparation guidelines. (Public page)
    """
    context = {
        'page_title': 'Assessments Overview',
        'active_nav': 'assessment',
        'brand_name': 'MindBloom',
    }
    return render(request, 'assessment/overview.html', context)


def aptitude_intro(request):
    """
    Renders the introduction to cognitive and aptitude evaluation,
    covering logical, numerical, and spatial reasoning pillars with sample formats. (Public page)
    """
    context = {
        'page_title': 'Aptitude Assessment Introduction',
        'active_nav': 'assessment',
        'brand_name': 'MindBloom',
    }
    return render(request, 'assessment/aptitude_intro.html', context)


def interest_intro(request):
    """
    Renders the introduction to interest and curiosity profiling,
    covering creative, STEM, and interpersonal preferences with sample scenarios. (Public page)
    """
    context = {
        'page_title': 'Interest Profiling Introduction',
        'active_nav': 'assessment',
        'brand_name': 'MindBloom',
    }
    return render(request, 'assessment/interest_intro.html', context)


@login_required
def child_register(request):
    """
    Handles child information intake via ModelForm with validation,
    associates the child with the authenticated parent/educator account,
    stores active_child_id in the session, and redirects to assessment selection.
    """
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.owner = request.user
            child.save()
            request.session['active_child_id'] = child.id
            messages.success(
                request,
                f"Child profile for {child.name} has been successfully created!"
            )
            return redirect('assessment:selection', child_id=child.id)
        else:
            messages.error(
                request,
                "Please correct the errors in the form before proceeding."
            )
    else:
        form = ChildRegistrationForm()

    context = {
        'page_title': 'Register Child Information',
        'active_nav': 'assessment',
        'form': form,
        'brand_name': 'MindBloom',
    }
    return render(request, 'assessment/child_register.html', context)


@login_required
def assessment_selection(request, child_id):
    """
    Displays the confirmation message with the registered child's name,
    child profile metadata, and available assessment tracks (Aptitude & Interest).
    Enforces user ownership on the child profile.
    """
    child = get_object_or_404(Child, pk=child_id)

    # Ownership check: user can only access their own children
    if child.owner_id is None or child.owner_id != request.user.id:
        raise PermissionDenied("You are not authorized to access this child profile.")

    request.session['active_child_id'] = child.id
    existing_assessments = child.assessments.all()

    context = {
        'page_title': f'Select Assessment &mdash; {child.name}',
        'active_nav': 'assessment',
        'child': child,
        'existing_assessments': existing_assessments,
        'brand_name': 'MindBloom',
    }
    return render(request, 'assessment/assessment_selection.html', context)


@login_required
def initiate_assessment(request, child_id, assessment_type):
    """
    Initiates an Assessment record (status=PENDING) for the selected child
    and transitions directly into the questionnaire player.
    Enforces user ownership.
    """
    child = get_object_or_404(Child, pk=child_id)

    # Ownership check
    if child.owner_id is None or child.owner_id != request.user.id:
        raise PermissionDenied("You are not authorized to initiate assessments for this child.")

    request.session['active_child_id'] = child.id
    type_upper = assessment_type.upper()

    if type_upper not in Assessment.AssessmentType.values:
        messages.error(request, f"Invalid assessment type: '{assessment_type}'.")
        return redirect('assessment:selection', child_id=child.id)

    assessment, _ = Assessment.objects.get_or_create(
        child=child,
        assessment_type=type_upper,
        status=Assessment.AssessmentStatus.PENDING,
        defaults={'created_at': timezone.now()}
    )

    return redirect('assessment:question', assessment_id=assessment.id, question_index=1)


@login_required
def questionnaire_entry(request, assessment_id):
    """
    Entrypoint that redirects to question #1 of an active assessment attempt.
    Synchronizes session active child to ensure seamless continuation from dashboard.
    """
    assessment = get_object_or_404(Assessment.objects.select_related('child'), pk=assessment_id)
    if assessment.child.owner_id is None or assessment.child.owner_id != request.user.id:
        raise PermissionDenied("You are not authorized to access this assessment.")
    request.session['active_child_id'] = assessment.child_id
    return redirect('assessment:question', assessment_id=assessment_id, question_index=1)


@login_required
def questionnaire_question(request, assessment_id, question_index):
    """
    Presents questions one at a time with progress tracking, selectable options,
    previous/next navigation, and submission on the final question.
    Enforces user ownership and session isolation.
    """
    assessment = get_object_or_404(Assessment.objects.select_related('child'), pk=assessment_id)

    # User ownership check
    if assessment.child.owner_id is None or assessment.child.owner_id != request.user.id:
        raise PermissionDenied("You are not authorized to access this assessment.")

    # Session check: verify child cannot access another child's assessment by URL change
    active_child_id = request.session.get('active_child_id')
    if active_child_id and active_child_id != assessment.child_id:
        raise PermissionDenied("You are not authorized to access another child's assessment.")

    # Remember active child in session
    request.session['active_child_id'] = assessment.child_id

    # If already completed, redirect to completion page
    if assessment.status == Assessment.AssessmentStatus.COMPLETED:
        return redirect('assessment:completion', assessment_id=assessment.id)

    # Retrieve all active questions for this assessment type matching the child's age group
    child_age_group = assessment.child.age_group
    questions = list(
        Question.objects.filter(
            assessment_type=assessment.assessment_type,
            age_group=child_age_group,
            is_active=True
        ).order_by('order', 'id')
    )

    total_questions = len(questions)
    if total_questions == 0:
        messages.warning(
            request,
            f"No active questions are currently configured for the {assessment.child.age_group_display} track."
        )
        return redirect('assessment:selection', child_id=assessment.child_id)

    # Bounds check
    if question_index < 1 or question_index > total_questions:
        messages.warning(request, f"Question {question_index} does not exist.")
        return redirect('assessment:question', assessment_id=assessment.id, question_index=1)

    current_question = questions[question_index - 1]
    is_first = (question_index == 1)
    is_last = (question_index == total_questions)

    # Check for existing answer
    existing_answer = Answer.objects.filter(
        assessment=assessment,
        question=current_question
    ).first()

    form_error = None

    if request.method == 'POST':
        action = request.POST.get('action', 'next')

        if action == 'prev':
            if not is_first:
                return redirect('assessment:question', assessment_id=assessment.id, question_index=question_index - 1)
            return redirect('assessment:question', assessment_id=assessment.id, question_index=1)

        if action == 'submit' and not is_last:
            messages.warning(request, "Please continue answering the remaining questions before submitting.")
            return redirect('assessment:question', assessment_id=assessment.id, question_index=question_index)

        form = QuestionAnswerForm(request.POST)
        if form.is_valid():
            selected = form.cleaned_data['selected_option']

            # Update or create answer
            Answer.objects.update_or_create(
                assessment=assessment,
                question=current_question,
                defaults={'selected_option': selected}
            )

            if is_last:
                # Mark assessment completed
                assessment.status = Assessment.AssessmentStatus.COMPLETED
                assessment.completed_at = timezone.now()
                assessment.save()
                messages.success(
                    request,
                    f"Congratulations! You have successfully completed the {assessment.get_assessment_type_display()}."
                )
                return redirect('assessment:completion', assessment_id=assessment.id)
            else:
                return redirect('assessment:question', assessment_id=assessment.id, question_index=question_index + 1)
        else:
            form_error = "Please select an answer option to proceed."

    # Selected value for rendering
    selected_value = existing_answer.selected_option if existing_answer else ''

    # Progress Calculation
    answered_count = assessment.answers.count()
    progress_percent = int((question_index / total_questions) * 100)

    options_data = [
        ('A', current_question.option_a),
        ('B', current_question.option_b),
        ('C', current_question.option_c),
        ('D', current_question.option_d),
    ]

    context = {
        'page_title': f"{assessment.get_assessment_type_display()} &bull; Q{question_index} of {total_questions}",
        'active_nav': 'assessment',
        'assessment': assessment,
        'child': assessment.child,
        'question': current_question,
        'question_index': question_index,
        'total_questions': total_questions,
        'answered_count': answered_count,
        'progress_percent': progress_percent,
        'options_data': options_data,
        'selected_value': selected_value,
        'is_first': is_first,
        'is_last': is_last,
        'form_error': form_error,
        'age_group_label': assessment.child.age_group_display,
        'difficulty_display': current_question.get_difficulty_display() if assessment.assessment_type == Assessment.AssessmentType.APTITUDE else None,
        'brand_name': 'MindBloom',
    }
    return render(request, 'assessment/questionnaire.html', context)


@login_required
def assessment_completion(request, assessment_id):
    """
    Renders the post-submission confirmation state showing completion metrics
    and navigation options. Enforces user ownership and session integrity.
    """
    assessment = get_object_or_404(Assessment.objects.select_related('child'), pk=assessment_id)

    # User ownership check
    if assessment.child.owner_id is None or assessment.child.owner_id != request.user.id:
        raise PermissionDenied("You are not authorized to view this assessment.")

    # Authorization Check
    active_child_id = request.session.get('active_child_id')
    if active_child_id and active_child_id != assessment.child_id:
        raise PermissionDenied("You are not authorized to view another child's assessment.")

    total_answers = assessment.answers.count()

    context = {
        'page_title': 'Assessment Completed | MindBloom',
        'active_nav': 'assessment',
        'assessment': assessment,
        'child': assessment.child,
        'total_answers': total_answers,
        'brand_name': 'MindBloom',
    }
    return render(request, 'assessment/completion.html', context)
