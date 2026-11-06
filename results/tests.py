from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Child
from assessment.models import Assessment, Question, Answer
from results.models import Result
from results.services import (
    calculate_aptitude_result,
    calculate_interest_result,
    get_or_generate_result,
    APTITUDE_CATEGORIES,
    INTEREST_CATEGORIES,
)


class ResultModelAndServicesTest(TestCase):
    def setUp(self):
        self.child = Child.objects.create(
            name="Aarav Sharma",
            age=10,
            gender=Child.Gender.MALE,
            grade="Grade 5"
        )

        # Create 5 Aptitude questions (one for each category)
        self.aptitude_questions = []
        for i, cat in enumerate(APTITUDE_CATEGORIES, start=1):
            q = Question.objects.create(
                assessment_type=Assessment.AssessmentType.APTITUDE,
                category=cat,
                question_text=f"Aptitude Question {i} in {cat}?",
                option_a="Choice Alpha",
                option_b="Choice Beta",
                option_c="Choice Gamma",
                option_d="Choice Delta",
                correct_option="A",
                order=i,
                is_active=True
            )
            self.aptitude_questions.append(q)

        # Create 5 Interest questions
        self.interest_questions = []
        for i, cat in enumerate(INTEREST_CATEGORIES, start=1):
            q = Question.objects.create(
                assessment_type=Assessment.AssessmentType.INTEREST,
                category=cat,
                question_text=f"Interest Question {i} in {cat}?",
                option_a="Explore science gadgets",
                option_a_category="Science and Technology",
                option_b="Paint a mural",
                option_b_category="Arts and Creativity",
                option_c="Organize a team picnic",
                option_c_category="Social Activities",
                option_d="Hike a nature trail",
                option_d_category="Nature and Exploration",
                order=i,
                is_active=True
            )
            self.interest_questions.append(q)

    def test_aptitude_result_calculation_accuracy(self):
        """Verify total, correct, incorrect, overall percentage, and category breakdown."""
        assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )

        # Answer 4 correctly (option A) and 1 incorrectly (option B)
        # Expected: 4 correct, 1 incorrect, total 5, percentage = 80.0%
        for i, q in enumerate(self.aptitude_questions):
            selected = 'A' if i < 4 else 'B'
            Answer.objects.create(
                assessment=assessment,
                question=q,
                selected_option=selected
            )

        metrics = calculate_aptitude_result(assessment)
        self.assertEqual(metrics['total_questions'], 5)
        self.assertEqual(metrics['correct_answers'], 4)
        self.assertEqual(metrics['incorrect_answers'], 1)
        self.assertEqual(metrics['overall_percentage'], 80.0)

        # Category scores check
        for i, cat in enumerate(APTITUDE_CATEGORIES):
            cat_data = metrics['category_scores'][cat]
            self.assertEqual(cat_data['total'], 1)
            if i < 4:
                self.assertEqual(cat_data['correct'], 1)
                self.assertEqual(cat_data['percentage'], 100.0)
            else:
                self.assertEqual(cat_data['correct'], 0)
                self.assertEqual(cat_data['percentage'], 0.0)

        self.assertIn("Aarav Sharma", metrics['summary'])

    def test_interest_result_calculation_accuracy(self):
        """Verify preference distribution counts, percentages, and top interest determination."""
        assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )

        # Answer selections: Option A maps to Science, Option B to Arts
        # Choose Option A for first 3 questions (Science: 3), Option B for remaining 2 (Arts: 2)
        for i, q in enumerate(self.interest_questions):
            selected = 'A' if i < 3 else 'B'
            Answer.objects.create(
                assessment=assessment,
                question=q,
                selected_option=selected
            )

        metrics = calculate_interest_result(assessment)
        self.assertEqual(metrics['total_questions'], 5)
        dist = metrics['category_distribution']
        self.assertEqual(dist['Science and Technology']['count'], 3)
        self.assertEqual(dist['Science and Technology']['percentage'], 60.0)
        self.assertEqual(dist['Arts and Creativity']['count'], 2)
        self.assertEqual(dist['Arts and Creativity']['percentage'], 40.0)
        self.assertEqual(dist['Social Activities']['count'], 0)
        self.assertEqual(dist['Social Activities']['percentage'], 0.0)

        self.assertEqual(metrics['top_interest_categories'][0], 'Science and Technology')
        self.assertEqual(metrics['top_interest_categories'][1], 'Arts and Creativity')
        self.assertIn("Aarav Sharma", metrics['summary'])

    def test_incomplete_assessment_raises_value_error(self):
        """Verify results cannot be calculated for an incomplete assessment."""
        assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.PENDING
        )

        # Only answer 1 question out of 5
        Answer.objects.create(
            assessment=assessment,
            question=self.aptitude_questions[0],
            selected_option='A'
        )

        with self.assertRaises(ValueError):
            calculate_aptitude_result(assessment)

        with self.assertRaises(ValueError):
            get_or_generate_result(assessment)

    def test_historical_completed_assessment_calculation(self):
        """Historical assessments completed prior to Task 07 (e.g. 15 questions) remain viewable and calculable."""
        historical_asmt = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        # Only answer 3 questions, simulating an older completed assessment schema
        for q in self.aptitude_questions[:3]:
            Answer.objects.create(
                assessment=historical_asmt,
                question=q,
                selected_option='A'
            )

        # Because status is COMPLETED, calculation proceeds cleanly without raising ValueError
        metrics = calculate_aptitude_result(historical_asmt)
        self.assertEqual(metrics['total_questions'], 3)
        self.assertEqual(metrics['correct_answers'], 3)
        self.assertEqual(metrics['overall_percentage'], 100.0)

    def test_get_or_generate_result_idempotency_and_uniqueness(self):
        """Ensure get_or_generate_result creates once and reuses existing record."""
        assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.aptitude_questions:
            Answer.objects.create(
                assessment=assessment,
                question=q,
                selected_option='A'
            )

        self.assertEqual(Result.objects.count(), 0)
        result1 = get_or_generate_result(assessment)
        self.assertEqual(Result.objects.count(), 1)
        self.assertEqual(result1.assessment, assessment)
        self.assertEqual(result1.overall_percentage, 100.0)

        # Calling again must not create a duplicate
        result2 = get_or_generate_result(assessment)
        self.assertEqual(Result.objects.count(), 1)
        self.assertEqual(result1.id, result2.id)


class ResultsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='parent_diya', password='password123')
        self.other_user = User.objects.create_user(username='parent_rohan', password='password123')
        self.child = Child.objects.create(
            owner=self.user,
            name="Diya Patel",
            age=9,
            gender=Child.Gender.FEMALE,
            grade="Grade 4"
        )
        self.other_child = Child.objects.create(
            owner=self.other_user,
            name="Rohan Varma",
            age=11,
            gender=Child.Gender.MALE
        )
        self.client.login(username='parent_diya', password='password123')

        # 5 active aptitude questions
        self.apt_questions = []
        for i, cat in enumerate(APTITUDE_CATEGORIES, start=1):
            q = Question.objects.create(
                assessment_type=Assessment.AssessmentType.APTITUDE,
                category=cat,
                question_text=f"Q{i}: What is {i} + {i}?",
                option_a=str(i * 2),
                option_b=str(i * 2 + 1),
                option_c=str(i * 2 + 2),
                option_d=str(i * 2 + 3),
                correct_option="A",
                order=i,
                is_active=True
            )
            self.apt_questions.append(q)

        # 5 active interest questions
        self.int_questions = []
        for i, cat in enumerate(INTEREST_CATEGORIES, start=1):
            q = Question.objects.create(
                assessment_type=Assessment.AssessmentType.INTEREST,
                category=cat,
                question_text=f"Q{i}: What do you like doing in free time?",
                option_a="Build a robot model",
                option_a_category="Science and Technology",
                option_b="Paint a landscape",
                option_b_category="Arts and Creativity",
                option_c="Organize an event",
                option_c_category="Social Activities",
                option_d="Plant saplings",
                option_d_category="Nature and Exploration",
                order=i,
                is_active=True
            )
            self.int_questions.append(q)

    def test_unauthenticated_results_overview_redirects_to_login(self):
        """Unauthenticated user visiting results overview is redirected to login."""
        self.client.logout()
        response = self.client.get(reverse('results:overview'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_results_overview_empty_state(self):
        """When no active child or no completed assessments, display friendly empty state."""
        response = self.client.get(reverse('results:overview'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'results/overview.html')
        self.assertContains(response, 'No Active Assessment Results Yet')
        self.assertContains(response, 'What MindBloom Reports Deliver')

    def test_results_overview_with_completed_assessment(self):
        """When active child has completed assessments, show results cards."""
        assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.apt_questions:
            Answer.objects.create(assessment=assessment, question=q, selected_option='A')

        # Set active child in session
        session = self.client.session
        session['active_child_id'] = self.child.id
        session.save()

        response = self.client.get(reverse('results:overview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Diya Patel')
        self.assertContains(response, 'Completed Assessment Reports')
        self.assertContains(response, '100.0%')
        self.assertContains(response, 'View Detailed Report')

    def test_aptitude_report_view_renders_correctly(self):
        """Verify complete Aptitude report rendering, metrics, disclaimers, and lack of answer leakage."""
        assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.apt_questions:
            Answer.objects.create(assessment=assessment, question=q, selected_option='A')

        # Authenticate session
        session = self.client.session
        session['active_child_id'] = self.child.id
        session.save()

        url = reverse('results:assessment_report', kwargs={'assessment_id': assessment.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'results/aptitude_report.html')
        self.assertContains(response, "Diya Patel's Aptitude Report")
        self.assertContains(response, '100.0%')
        self.assertContains(response, 'Correct Answers')
        self.assertContains(response, 'Out of 5 questions')
        self.assertContains(response, '1 of 1 Correct')
        self.assertContains(response, 'Logical Reasoning')
        self.assertContains(response, 'Numerical Ability')
        self.assertContains(response, 'Educational Disclaimer')

        # Critical security check: Never leak the correct_option field in frontend
        self.assertNotContains(response, 'correct_option')

    def test_interest_report_view_renders_correctly(self):
        """Verify complete Interest report rendering with distribution and top domains."""
        assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.int_questions:
            Answer.objects.create(assessment=assessment, question=q, selected_option='A')

        session = self.client.session
        session['active_child_id'] = self.child.id
        session.save()

        url = reverse('results:assessment_report', kwargs={'assessment_id': assessment.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'results/interest_report.html')
        self.assertContains(response, "Diya Patel's Interest Profile")
        self.assertContains(response, 'Science and Technology')
        self.assertContains(response, 'Arts and Creativity')
        self.assertContains(response, 'Preference Distribution')
        self.assertContains(response, 'Educational Disclaimer')

    def test_unauthorized_access_to_another_child_report_is_blocked(self):
        """Accessing another child's assessment report without matching session must return 403."""
        assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.apt_questions:
            Answer.objects.create(assessment=assessment, question=q, selected_option='A')

        # Session is set to other_child (Rohan)
        session = self.client.session
        session['active_child_id'] = self.other_child.id
        session.save()

        url = reverse('results:assessment_report', kwargs={'assessment_id': assessment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_pending_assessment_redirects_away_from_report(self):
        """Attempting to view report for an incomplete assessment redirects back to questionnaire."""
        assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.PENDING
        )

        session = self.client.session
        session['active_child_id'] = self.child.id
        session.save()

        url = reverse('results:assessment_report', kwargs={'assessment_id': assessment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/assessment/{assessment.id}/question/1/", response.url)

    def test_result_detail_redirects_to_canonical_report(self):
        """Detail URL redirects to the canonical assessment_report route."""
        assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.apt_questions:
            Answer.objects.create(assessment=assessment, question=q, selected_option='A')

        result = get_or_generate_result(assessment)
        session = self.client.session
        session['active_child_id'] = self.child.id
        session.save()

        url = reverse('results:detail', kwargs={'result_id': result.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('results:assessment_report', kwargs={'assessment_id': assessment.id}))


    def test_user_cannot_access_other_users_assessment_report(self):
        """User cannot view report for an assessment owned by another parent."""
        assessment_other = Assessment.objects.create(
            child=self.other_child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.apt_questions:
            Answer.objects.create(assessment=assessment_other, question=q, selected_option='A')

        url = reverse('results:assessment_report', kwargs={'assessment_id': assessment_other.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_access_unowned_assessment_report(self):
        """Strict ownership: accessing report whose child has owner=None must return 403."""
        unowned_child = Child.objects.create(
            name="Orphan Learner",
            age=10,
            gender=Child.Gender.OTHER,
            owner=None
        )
        assessment_unowned = Assessment.objects.create(
            child=unowned_child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.apt_questions:
            Answer.objects.create(assessment=assessment_unowned, question=q, selected_option='A')

        url = reverse('results:assessment_report', kwargs={'assessment_id': assessment_unowned.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_access_unowned_result_detail(self):
        """Direct access via result ID for an unowned child must return 403."""
        unowned_child = Child.objects.create(
            name="Unowned Detail Child",
            age=11,
            gender=Child.Gender.FEMALE,
            owner=None
        )
        assessment_unowned = Assessment.objects.create(
            child=unowned_child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.apt_questions:
            Answer.objects.create(assessment=assessment_unowned, question=q, selected_option='A')

        result_unowned = get_or_generate_result(assessment_unowned)
        url = reverse('results:detail', kwargs={'result_id': result_unowned.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_results_overview_strictly_filters_to_current_user_children(self):
        """Overview only surfaces children owned by the logged-in user, ignoring others and unowned."""
        # Completed assessment for current user's child
        assessment_own = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.apt_questions:
            Answer.objects.create(assessment=assessment_own, question=q, selected_option='A')

        # Completed assessment for other user's child
        assessment_other = Assessment.objects.create(
            child=self.other_child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.apt_questions:
            Answer.objects.create(assessment=assessment_other, question=q, selected_option='A')

        # Completed assessment for unowned child
        unowned_child = Child.objects.create(name="Unowned Ghost", age=8, gender=Child.Gender.MALE, owner=None)
        assessment_ghost = Assessment.objects.create(
            child=unowned_child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        for q in self.apt_questions:
            Answer.objects.create(assessment=assessment_ghost, question=q, selected_option='A')

        response = self.client.get(reverse('results:overview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Diya Patel')
        self.assertNotContains(response, 'Rohan Varma')
        self.assertNotContains(response, 'Unowned Ghost')
