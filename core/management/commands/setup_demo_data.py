"""
MindBloom - Demonstration Data Setup Management Command
Prepares realistic, repeatable, and idempotent sample data for academic demonstration.
Creates:
- Demo parent account (demo_parent)
- Multiple child profiles spanning distinct developmental age groups (GROUP_1, GROUP_2)
- Completed aptitude and interest assessments with realistic results
- Longitudinal comparison data (previous vs. latest attempt)
- A pending assessment to demonstrate ongoing assessment continuation
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Child
from assessment.models import Assessment, Question, Answer
from results.models import Result
from results.services import (
    calculate_aptitude_result,
    calculate_interest_result,
    APTITUDE_CATEGORIES,
    INTEREST_CATEGORIES,
)


class Command(BaseCommand):
    help = "Sets up idempotent demonstration account and realistic sample data for MindBloom evaluation."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing MindBloom demonstration dataset..."))

        # Ensure question bank is loaded
        from assessment.seed_data import load_initial_questions
        if Question.objects.count() == 0:
            load_initial_questions()

        # 1. Demonstration Parent Account
        demo_user, created_user = User.objects.get_or_create(
            username='demo_parent',
            defaults={
                'first_name': 'Priya',
                'last_name': 'Sharma',
                'email': 'parent@mindbloom.edu',
            }
        )
        demo_user.set_password('DemoPass2026!')
        demo_user.save()
        if created_user:
            self.stdout.write(self.style.SUCCESS("Created demo user: demo_parent"))
        else:
            self.stdout.write(self.style.SUCCESS("Updated demo user: demo_parent (password reset to DemoPass2026!)"))

        # 2. Child 1: Aarav Sharma (Age 10, GROUP_2: Developing Reasoning)
        aarav, _ = Child.objects.get_or_create(
            name="Aarav Sharma",
            owner=demo_user,
            defaults={
                'age': 10,
                'gender': Child.Gender.MALE,
                'grade': 'Grade 5',
            }
        )

        # 3. Child 2: Diya Sharma (Age 7, GROUP_1: Early Exploration)
        diya, _ = Child.objects.get_or_create(
            name="Diya Sharma",
            owner=demo_user,
            defaults={
                'age': 7,
                'gender': Child.Gender.FEMALE,
                'grade': 'Class 2',
            }
        )

        # 4. Child 3: Samarpan Roy (Age 11, GROUP_2: Developing Reasoning) - for pending workflow
        samarpan, _ = Child.objects.get_or_create(
            name="Samarpan Roy",
            owner=demo_user,
            defaults={
                'age': 11,
                'gender': Child.Gender.MALE,
                'grade': 'Grade 6',
            }
        )

        now = timezone.now()

        # 5. Populate Diya's Assessments (GROUP_1: Ages 5–8)
        # Diya: 1 Completed Aptitude Assessment
        diya_apt, created_diya_apt = Assessment.objects.get_or_create(
            child=diya,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            defaults={
                'created_at': now - timezone.timedelta(days=2),
                'completed_at': now - timezone.timedelta(days=2),
            }
        )
        if created_diya_apt or not hasattr(diya_apt, 'result'):
            # Answer GROUP_1 aptitude questions
            g1_apt_qs = list(Question.objects.filter(
                assessment_type=Assessment.AssessmentType.APTITUDE,
                age_group=Question.AgeGroup.GROUP_1,
                is_active=True
            ).order_by('order', 'id'))
            for idx, q in enumerate(g1_apt_qs):
                # 21 correct out of 25 (84%)
                selected = q.correct_option if idx < 21 else ('A' if q.correct_option != 'A' else 'B')
                Answer.objects.update_or_create(
                    assessment=diya_apt,
                    question=q,
                    defaults={'selected_option': selected}
                )
            metrics = calculate_aptitude_result(diya_apt)
            Result.objects.update_or_create(
                assessment=diya_apt,
                defaults={
                    'total_questions': metrics['total_questions'],
                    'correct_answers': metrics['correct_answers'],
                    'incorrect_answers': metrics['incorrect_answers'],
                    'overall_percentage': metrics['overall_percentage'],
                    'category_scores': metrics['category_scores'],
                    'strongest_categories': metrics['strongest_categories'],
                    'growth_categories': metrics['growth_categories'],
                    'summary': metrics['summary'],
                }
            )

        # Diya: 1 Completed Interest Assessment
        diya_int, created_diya_int = Assessment.objects.get_or_create(
            child=diya,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.COMPLETED,
            defaults={
                'created_at': now - timezone.timedelta(days=1),
                'completed_at': now - timezone.timedelta(days=1),
            }
        )
        if created_diya_int or not hasattr(diya_int, 'result'):
            g1_int_qs = list(Question.objects.filter(
                assessment_type=Assessment.AssessmentType.INTEREST,
                age_group=Question.AgeGroup.GROUP_1,
                is_active=True
            ).order_by('order', 'id'))
            for idx, q in enumerate(g1_int_qs):
                selected = 'A' if (idx % 2 == 0) else 'B'
                Answer.objects.update_or_create(
                    assessment=diya_int,
                    question=q,
                    defaults={'selected_option': selected}
                )
            int_metrics = calculate_interest_result(diya_int)
            Result.objects.update_or_create(
                assessment=diya_int,
                defaults={
                    'total_questions': int_metrics['total_questions'],
                    'category_distribution': int_metrics['category_distribution'],
                    'top_interest_categories': int_metrics['top_interest_categories'],
                    'secondary_interest_categories': int_metrics['secondary_interest_categories'],
                    'summary': int_metrics['summary'],
                }
            )

        # 6. Aarav Sharma: Ensure comparison data exists
        # Aarav needs at least 2 completed Aptitude attempts to demonstrate progress comparison.
        g2_apt_qs = list(Question.objects.filter(
            assessment_type=Assessment.AssessmentType.APTITUDE,
            age_group=Question.AgeGroup.GROUP_2,
            is_active=True
        ).order_by('order', 'id'))

        aarav_apt_list = list(Assessment.objects.filter(
            child=aarav,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED
        ).order_by('completed_at', 'id'))

        while len(aarav_apt_list) < 2:
            idx_offset = len(aarav_apt_list)
            asmt_time = now - timezone.timedelta(days=(2 - idx_offset) * 3)
            new_asmt = Assessment.objects.create(
                child=aarav,
                assessment_type=Assessment.AssessmentType.APTITUDE,
                status=Assessment.AssessmentStatus.COMPLETED,
                created_at=asmt_time,
                completed_at=asmt_time,
            )
            # Score: 80% on first, 88% on second
            correct_threshold = 20 if idx_offset == 0 else 22
            for q_idx, q in enumerate(g2_apt_qs):
                selected = q.correct_option if q_idx < correct_threshold else ('A' if q.correct_option != 'A' else 'B')
                Answer.objects.create(
                    assessment=new_asmt,
                    question=q,
                    selected_option=selected,
                )
            metrics = calculate_aptitude_result(new_asmt)
            Result.objects.create(
                assessment=new_asmt,
                total_questions=metrics['total_questions'],
                correct_answers=metrics['correct_answers'],
                incorrect_answers=metrics['incorrect_answers'],
                overall_percentage=metrics['overall_percentage'],
                category_scores=metrics['category_scores'],
                strongest_categories=metrics['strongest_categories'],
                growth_categories=metrics['growth_categories'],
                summary=metrics['summary'],
            )
            aarav_apt_list.append(new_asmt)
            self.stdout.write(self.style.SUCCESS(f"Created Aptitude comparison attempt for Aarav Sharma ({metrics['overall_percentage']}%)."))

        # 7. Samarpan Roy: Ensure pending assessment exists
        samarpan_pending, _ = Assessment.objects.get_or_create(
            child=samarpan,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.PENDING,
            defaults={'created_at': now}
        )

        self.stdout.write(self.style.SUCCESS("MindBloom demonstration dataset ready!"))
        self.stdout.write("Credentials: Username = 'demo_parent', Password = 'DemoPass2026!'")
