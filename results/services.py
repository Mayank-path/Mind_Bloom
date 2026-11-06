"""
MindBloom - Assessment Result Calculation Engine
Handles deterministic evaluation for Aptitude assessments and preference
distribution calculations for Interest assessments.
"""
from django.utils import timezone
from assessment.models import Assessment, Question
from .models import Result

APTITUDE_CATEGORIES = [
    'Logical Reasoning',
    'Numerical Ability',
    'Spatial Reasoning',
    'Pattern Recognition',
    'Problem Solving',
]

INTEREST_CATEGORIES = [
    'Science and Technology',
    'Arts and Creativity',
    'Social Activities',
    'Nature and Exploration',
    'Sports and Physical Activities',
]


def calculate_aptitude_result(assessment):
    """
    Evaluates answers for an Aptitude Assessment attempt.
    Calculates correct/incorrect counts, percentages, and category breakdowns.
    """
    answers = list(assessment.answers.select_related('question').all())
    child_age_group = assessment.child.age_group
    expected_questions = Question.objects.filter(
        assessment_type=Assessment.AssessmentType.APTITUDE,
        age_group=child_age_group,
        is_active=True
    )
    expected_count = expected_questions.count()

    if expected_count > 0 and len(answers) < expected_count and assessment.status != Assessment.AssessmentStatus.COMPLETED:
        raise ValueError(
            f"Assessment is incomplete. Answered {len(answers)} of {expected_count} questions."
        )
    if len(answers) == 0:
        raise ValueError("Assessment has no recorded answers.")

    total_questions = len(answers)
    correct_answers = sum(1 for ans in answers if ans.is_correct)
    incorrect_answers = total_questions - correct_answers
    overall_percentage = round((correct_answers / total_questions) * 100, 1) if total_questions > 0 else 0.0

    # Category-wise performance
    category_scores = {}
    for cat in APTITUDE_CATEGORIES:
        cat_answers = [ans for ans in answers if ans.question.category == cat]
        total_in_cat = len(cat_answers)
        correct_in_cat = sum(1 for ans in cat_answers if ans.is_correct)
        incorrect_in_cat = total_in_cat - correct_in_cat
        pct = round((correct_in_cat / total_in_cat) * 100, 1) if total_in_cat > 0 else 0.0

        category_scores[cat] = {
            'correct': correct_in_cat,
            'total': total_in_cat,
            'incorrect': incorrect_in_cat,
            'percentage': pct,
        }

    # Relative Strengths and Growth Areas (rank-based, non-diagnostic)
    sorted_by_pct = sorted(
        category_scores.items(),
        key=lambda item: (item[1]['percentage'], item[1]['correct']),
        reverse=True
    )

    max_pct = sorted_by_pct[0][1]['percentage'] if sorted_by_pct else 0.0

    strongest_categories = [cat for cat, data in sorted_by_pct if data['percentage'] >= max(max_pct - 15.0, 50.0)]
    growth_categories = [cat for cat, data in sorted_by_pct if cat not in strongest_categories or data['percentage'] < 100.0]

    # Constructive narrative summary with exploratory framing
    child_name = assessment.child.name
    top_str = ", ".join(strongest_categories[:2]) if strongest_categories else "all evaluated areas"
    summary = (
        f"{child_name} demonstrated strong analytical engagement during this {assessment.child.age_group_display} "
        f"aptitude exploration, showing relative strengths in {top_str}. Please note that a short questionnaire provides "
        f"exploratory indicators rather than a complete measure of lifelong potential. Use these observations as an encouraging "
        f"conversation starter to support growth through playful, low-stress reasoning activities."
    )

    return {
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'overall_percentage': overall_percentage,
        'category_scores': category_scores,
        'strongest_categories': strongest_categories[:3],
        'growth_categories': growth_categories[-2:] if len(growth_categories) > 1 else growth_categories,
        'summary': summary,
    }


def calculate_interest_result(assessment):
    """
    Calculates preference selection counts and distribution percentages
    across the five interest domains. No answer is judged right or wrong.
    """
    answers = list(assessment.answers.select_related('question').all())
    child_age_group = assessment.child.age_group
    expected_questions = Question.objects.filter(
        assessment_type=Assessment.AssessmentType.INTEREST,
        age_group=child_age_group,
        is_active=True
    )
    expected_count = expected_questions.count()

    if expected_count > 0 and len(answers) < expected_count and assessment.status != Assessment.AssessmentStatus.COMPLETED:
        raise ValueError(
            f"Assessment is incomplete. Answered {len(answers)} of {expected_count} questions."
        )
    if len(answers) == 0:
        raise ValueError("Assessment has no recorded answers.")

    total_selections = len(answers)
    category_counts = {cat: 0 for cat in INTEREST_CATEGORIES}

    for ans in answers:
        cat = ans.contributed_category
        if cat in category_counts:
            category_counts[cat] += 1
        else:
            category_counts[cat] = 1

    category_distribution = {}
    for cat in INTEREST_CATEGORIES:
        count = category_counts.get(cat, 0)
        pct = round((count / total_selections) * 100, 1) if total_selections > 0 else 0.0
        category_distribution[cat] = {
            'count': count,
            'percentage': pct,
        }

    # Identify most selected and secondary interest areas
    sorted_interests = sorted(
        category_distribution.items(),
        key=lambda item: item[1]['count'],
        reverse=True
    )

    top_interest_categories = [cat for cat, data in sorted_interests if data['count'] > 0][:2]
    secondary_interest_categories = [cat for cat, data in sorted_interests[2:] if data['count'] > 0]

    child_name = assessment.child.name
    top_interest_names = " and ".join(top_interest_categories) if top_interest_categories else "diverse learning pathways"
    summary = (
        f"{child_name}'s choices reflect strong natural curiosity towards {top_interest_names}. "
        f"Because interests evolve dynamically with age, experience, and new opportunities, these insights are exploratory "
        f"guidance rather than fixed career paths. Parents and educators should use them as conversation starters to foster "
        f"curiosity through varied extracurricular exploration."
    )

    return {
        'total_questions': total_selections,
        'category_distribution': category_distribution,
        'top_interest_categories': top_interest_categories,
        'secondary_interest_categories': secondary_interest_categories,
        'summary': summary,
    }


def get_or_generate_result(assessment):
    """
    Safely retrieves the existing Result for a completed Assessment, or calculates
    and persists it idempotently if not yet generated.
    """
    if assessment.status != Assessment.AssessmentStatus.COMPLETED:
        raise ValueError("Results can only be generated for completed assessments.")

    # Check if result already exists (prevent duplicate results)
    existing_result = Result.objects.filter(assessment=assessment).first()
    if existing_result:
        return existing_result

    # Compute according to assessment type
    if assessment.assessment_type == Assessment.AssessmentType.APTITUDE:
        metrics = calculate_aptitude_result(assessment)
        result = Result.objects.create(
            assessment=assessment,
            total_questions=metrics['total_questions'],
            correct_answers=metrics['correct_answers'],
            incorrect_answers=metrics['incorrect_answers'],
            overall_percentage=metrics['overall_percentage'],
            category_scores=metrics['category_scores'],
            strongest_categories=metrics['strongest_categories'],
            growth_categories=metrics['growth_categories'],
            summary=metrics['summary'],
        )
    else:
        metrics = calculate_interest_result(assessment)
        result = Result.objects.create(
            assessment=assessment,
            total_questions=metrics['total_questions'],
            category_distribution=metrics['category_distribution'],
            top_interest_categories=metrics['top_interest_categories'],
            secondary_interest_categories=metrics['secondary_interest_categories'],
            summary=metrics['summary'],
        )

    return result

