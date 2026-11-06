from django.core.management.base import BaseCommand
from assessment.models import Question
from assessment.seed_data import load_initial_questions


class Command(BaseCommand):
    help = "Seeds all 150 age-appropriate Aptitude and Interest questions across GROUP_1, GROUP_2, and GROUP_3 into SQLite."

    def handle(self, *args, **options):
        created, updated = load_initial_questions()
        total_questions = Question.objects.count()
        g1_count = Question.objects.filter(age_group='GROUP_1').count()
        g2_count = Question.objects.filter(age_group='GROUP_2').count()
        g3_count = Question.objects.filter(age_group='GROUP_3').count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded question bank! Created: {created}, Updated: {updated}.\n"
                f"Database Totals: {total_questions} questions "
                f"(GROUP_1: {g1_count}, GROUP_2: {g2_count}, GROUP_3: {g3_count})."
            )
        )
