from django.test import TestCase, Client
from django.urls import reverse
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError
from core.models import Child
from .models import Assessment, Question, Answer
from .utils import get_age_group, get_age_group_label
from .seed_data import load_initial_questions


class AgeGroupClassificationTest(TestCase):
    def test_age_group_boundaries_group_1(self):
        """Ages 5 through 8 map to GROUP_1 (Early exploration)."""
        for age in [5, 6, 7, 8]:
            self.assertEqual(get_age_group(age), Question.AgeGroup.GROUP_1)
            self.assertIn("Early Exploration", get_age_group_label(age))

    def test_age_group_boundaries_group_2(self):
        """Ages 9 through 13 map to GROUP_2 (Developing reasoning)."""
        for age in [9, 10, 11, 12, 13]:
            self.assertEqual(get_age_group(age), Question.AgeGroup.GROUP_2)
            self.assertIn("Developing Reasoning", get_age_group_label(age))

    def test_age_group_boundaries_group_3(self):
        """Ages 14 through 18 map to GROUP_3 (Advanced exploration)."""
        for age in [14, 15, 16, 17, 18]:
            self.assertEqual(get_age_group(age), Question.AgeGroup.GROUP_3)
            self.assertIn("Advanced Exploration", get_age_group_label(age))

    def test_invalid_age_raises_value_error(self):
        """Ages outside 5-18, None, or invalid types raise ValueError."""
        invalid_ages = [4, 19, 0, -1, 100, None, "ten", 7.5]
        for age in invalid_ages:
            with self.assertRaises(ValueError):
                get_age_group(age)
            with self.assertRaises(ValueError):
                get_age_group_label(age)

    def test_child_model_age_group_property(self):
        """Child model properties .age_group and .age_group_display work correctly."""
        c1 = Child(name="Toddler", age=6, gender=Child.Gender.MALE)
        c2 = Child(name="Tween", age=11, gender=Child.Gender.FEMALE)
        c3 = Child(name="Teen", age=16, gender=Child.Gender.OTHER)

        self.assertEqual(c1.age_group, Question.AgeGroup.GROUP_1)
        self.assertEqual(c2.age_group, Question.AgeGroup.GROUP_2)
        self.assertEqual(c3.age_group, Question.AgeGroup.GROUP_3)

        self.assertIn("Ages 5–8", c1.age_group_display)
        self.assertIn("Ages 9–13", c2.age_group_display)
        self.assertIn("Ages 14–18", c3.age_group_display)


class QuestionModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_initial_questions()

    def test_question_bank_counts_and_types(self):
        # 150 questions total: 75 aptitude and 75 interest
        aptitude_qs = Question.objects.filter(assessment_type=Assessment.AssessmentType.APTITUDE)
        interest_qs = Question.objects.filter(assessment_type=Assessment.AssessmentType.INTEREST)
        self.assertEqual(aptitude_qs.count(), 75)
        self.assertEqual(interest_qs.count(), 75)
        self.assertEqual(Question.objects.count(), 150)

        # 25 questions per age group per type
        for group in [Question.AgeGroup.GROUP_1, Question.AgeGroup.GROUP_2, Question.AgeGroup.GROUP_3]:
            self.assertEqual(aptitude_qs.filter(age_group=group).count(), 25)
            self.assertEqual(interest_qs.filter(age_group=group).count(), 25)

    def test_aptitude_questions_categories_and_answers(self):
        categories = set(Question.objects.filter(
            assessment_type=Assessment.AssessmentType.APTITUDE
        ).values_list('category', flat=True))
        expected_categories = {
            'Logical Reasoning',
            'Numerical Ability',
            'Spatial Reasoning',
            'Pattern Recognition',
            'Problem Solving'
        }
        self.assertEqual(categories, expected_categories)

        valid_difficulties = {Question.Difficulty.EASY, Question.Difficulty.MEDIUM, Question.Difficulty.HARD}

        for q in Question.objects.filter(assessment_type=Assessment.AssessmentType.APTITUDE):
            self.assertIn(q.correct_option, ['A', 'B', 'C', 'D'])
            self.assertIn(q.difficulty, valid_difficulties)
            self.assertTrue(q.option_a)
            self.assertTrue(q.option_b)
            self.assertTrue(q.option_c)
            self.assertTrue(q.option_d)
            self.assertTrue(q.is_active)

    def test_interest_questions_categories(self):
        categories = set(Question.objects.filter(
            assessment_type=Assessment.AssessmentType.INTEREST
        ).values_list('category', flat=True))
        expected_categories = {
            'Science and Technology',
            'Arts and Creativity',
            'Social Activities',
            'Nature and Exploration',
            'Sports and Physical Activities'
        }
        self.assertEqual(categories, expected_categories)

        for q in Question.objects.filter(assessment_type=Assessment.AssessmentType.INTEREST):
            self.assertIsNone(q.correct_option)
            self.assertIn(q.option_a_category, expected_categories)
            self.assertIn(q.option_b_category, expected_categories)
            self.assertIn(q.option_c_category, expected_categories)
            self.assertIn(q.option_d_category, expected_categories)
            self.assertTrue(q.is_active)

    def test_inactive_questions_excluded(self):
        q = Question.objects.filter(assessment_type=Assessment.AssessmentType.APTITUDE).first()
        q.is_active = False
        q.save()

        active_qs = Question.objects.filter(
            assessment_type=Assessment.AssessmentType.APTITUDE,
            is_active=True
        )
        self.assertEqual(active_qs.count(), 74)


class AnswerModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_initial_questions()

    def setUp(self):
        self.child = Child.objects.create(name="Kabir Mehra", age=10, gender=Child.Gender.MALE)
        self.assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.PENDING
        )
        self.question = Question.objects.filter(
            assessment_type=Assessment.AssessmentType.APTITUDE,
            order=1
        ).first()

    def test_store_answer_and_correctness(self):
        answer = Answer.objects.create(
            assessment=self.assessment,
            question=self.question,
            selected_option=self.question.correct_option
        )
        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.selected_option, self.question.correct_option)

    def test_incorrect_answer_evaluation(self):
        wrong_option = 'A' if self.question.correct_option != 'A' else 'D'
        answer = Answer.objects.create(
            assessment=self.assessment,
            question=self.question,
            selected_option=wrong_option
        )
        self.assertFalse(answer.is_correct)

    def test_prevent_duplicate_answers_unique_constraint(self):
        Answer.objects.create(
            assessment=self.assessment,
            question=self.question,
            selected_option='A'
        )
        # Attempting to insert a duplicate answer for the same assessment and question raises IntegrityError
        with self.assertRaises(IntegrityError):
            Answer.objects.create(
                assessment=self.assessment,
                question=self.question,
                selected_option='B'
            )

    def test_interest_answer_category_mapping(self):
        interest_assessment = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.PENDING
        )
        interest_q = Question.objects.filter(
            assessment_type=Assessment.AssessmentType.INTEREST,
            order=1
        ).first()
        ans = Answer.objects.create(
            assessment=interest_assessment,
            question=interest_q,
            selected_option='A'
        )
        self.assertIsNone(ans.is_correct)
        self.assertEqual(ans.contributed_category, interest_q.option_a_category)


class QuestionnaireWorkflowTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_initial_questions()

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='parent1', password='password123')
        self.user2 = User.objects.create_user(username='parent2', password='password123')
        self.child1 = Child.objects.create(name="Aanya Sen", age=9, gender=Child.Gender.FEMALE, owner=self.user1)
        self.child2 = Child.objects.create(name="Dev Sharma", age=12, gender=Child.Gender.MALE, owner=self.user2)
        self.assessment1 = Assessment.objects.create(
            child=self.child1,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.PENDING
        )
        self.assessment2 = Assessment.objects.create(
            child=self.child2,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.PENDING
        )
        self.client.login(username='parent1', password='password123')

    def test_unauthenticated_user_redirected_to_login(self):
        """Unauthenticated requests to assessment views redirect to login."""
        self.client.logout()
        url = reverse('assessment:register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_child_registration_assigns_owner(self):
        """When logged-in user registers a child, child.owner is set to request.user."""
        url = reverse('assessment:register')
        post_data = {
            'name': 'Vivaan Roy',
            'age': 7,
            'gender': Child.Gender.MALE,
            'grade': 'Class 2'
        }
        response = self.client.post(url, data=post_data)
        vivaan = Child.objects.get(name='Vivaan Roy')
        self.assertEqual(vivaan.owner, self.user1)
        self.assertRedirects(response, reverse('assessment:selection', kwargs={'child_id': vivaan.id}))

    def test_user_cannot_access_other_users_child_selection(self):
        """User cannot access assessment selection for another user's child profile."""
        url = reverse('assessment:selection', kwargs={'child_id': self.child2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_questionnaire_view_get_first_question(self):
        # Set session to child1 (age 9, GROUP_2)
        session = self.client.session
        session['active_child_id'] = self.child1.id
        session.save()

        url = reverse('assessment:question', kwargs={'assessment_id': self.assessment1.id, 'question_index': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assessment/questionnaire.html')
        self.assertContains(response, 'Aanya Sen')
        self.assertContains(response, 'Question 1 of 25')
        self.assertContains(response, 'Ages 9–13')
        # Aptitude questions show difficulty badge
        self.assertContains(response, 'difficulty-badge')
        self.assertContains(response, 'Save &amp; Next')
        self.assertNotContains(response, 'Complete &amp; Submit Assessment')

    def test_interest_questionnaire_has_no_difficulty_badge(self):
        """Interest assessment questionnaire never displays a difficulty badge."""
        interest_assessment = Assessment.objects.create(
            child=self.child1,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.PENDING
        )
        session = self.client.session
        session['active_child_id'] = self.child1.id
        session.save()

        url = reverse('assessment:question', kwargs={'assessment_id': interest_assessment.id, 'question_index': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Question 1 of 25')
        self.assertNotContains(response, 'difficulty-badge')
        self.assertNotContains(response, 'Easy')
        self.assertNotContains(response, 'Medium')
        self.assertNotContains(response, 'Hard')

    def test_answer_submission_and_navigation(self):
        session = self.client.session
        session['active_child_id'] = self.child1.id
        session.save()

        url_q1 = reverse('assessment:question', kwargs={'assessment_id': self.assessment1.id, 'question_index': 1})
        response = self.client.post(url_q1, {'selected_option': 'B', 'action': 'next'})
        self.assertRedirects(
            response,
            reverse('assessment:question', kwargs={'assessment_id': self.assessment1.id, 'question_index': 2})
        )
        self.assertEqual(self.assessment1.answers.count(), 1)
        self.assertEqual(self.assessment1.answers.first().selected_option, 'B')

    def test_previous_navigation_preserves_answer(self):
        session = self.client.session
        session['active_child_id'] = self.child1.id
        session.save()

        # Answer Q1
        url_q1 = reverse('assessment:question', kwargs={'assessment_id': self.assessment1.id, 'question_index': 1})
        self.client.post(url_q1, {'selected_option': 'C', 'action': 'next'})

        # On Q2, click previous
        url_q2 = reverse('assessment:question', kwargs={'assessment_id': self.assessment1.id, 'question_index': 2})
        response = self.client.post(url_q2, {'action': 'prev'})
        self.assertRedirects(response, url_q1)

        # Inspect Q1 page, selected_value should be 'C'
        resp_q1 = self.client.get(url_q1)
        self.assertContains(resp_q1, 'value="C"')

    def test_prevent_accidental_premature_submission(self):
        session = self.client.session
        session['active_child_id'] = self.child1.id
        session.save()

        # Try submitting on question 5 instead of 25
        url_q5 = reverse('assessment:question', kwargs={'assessment_id': self.assessment1.id, 'question_index': 5})
        response = self.client.post(url_q5, {'selected_option': 'A', 'action': 'submit'})
        self.assertRedirects(response, url_q5)
        self.assessment1.refresh_from_db()
        self.assertEqual(self.assessment1.status, Assessment.AssessmentStatus.PENDING)

    def test_complete_all_questions_and_submit(self):
        session = self.client.session
        session['active_child_id'] = self.child1.id
        session.save()

        # Answer questions 1 through 24
        for idx in range(1, 25):
            url = reverse('assessment:question', kwargs={'assessment_id': self.assessment1.id, 'question_index': idx})
            self.client.post(url, {'selected_option': 'B', 'action': 'next'})

        # Submit on final question 25
        url_25 = reverse('assessment:question', kwargs={'assessment_id': self.assessment1.id, 'question_index': 25})
        response = self.client.post(url_25, {'selected_option': 'B', 'action': 'submit'})
        self.assertRedirects(
            response,
            reverse('assessment:completion', kwargs={'assessment_id': self.assessment1.id})
        )

        self.assessment1.refresh_from_db()
        self.assertEqual(self.assessment1.status, Assessment.AssessmentStatus.COMPLETED)
        self.assertIsNotNone(self.assessment1.completed_at)
        self.assertEqual(self.assessment1.answers.count(), 25)

    def test_age_group_question_scoping_no_cross_age_leakage(self):
        """Children in different age groups receive only their age-appropriate questions."""
        child_g1 = Child.objects.create(name="Little Sam", age=6, gender=Child.Gender.MALE, owner=self.user1)
        child_g3 = Child.objects.create(name="Teen Tara", age=16, gender=Child.Gender.FEMALE, owner=self.user1)

        asmt_g1 = Assessment.objects.create(
            child=child_g1,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.PENDING
        )
        asmt_g3 = Assessment.objects.create(
            child=child_g3,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.PENDING
        )

        session = self.client.session

        # Check Child G1 (Age 6) - first question
        session['active_child_id'] = child_g1.id
        session.save()
        resp_g1 = self.client.get(reverse('assessment:question', kwargs={'assessment_id': asmt_g1.id, 'question_index': 1}))
        self.assertEqual(resp_g1.status_code, 200)
        self.assertEqual(resp_g1.context['question'].age_group, Question.AgeGroup.GROUP_1)
        self.assertContains(resp_g1, 'Ages 5–8')
        self.assertEqual(resp_g1.context['total_questions'], 25)

        # Check Child G3 (Age 16) - first question
        session['active_child_id'] = child_g3.id
        session.save()
        resp_g3 = self.client.get(reverse('assessment:question', kwargs={'assessment_id': asmt_g3.id, 'question_index': 1}))
        self.assertEqual(resp_g3.status_code, 200)
        self.assertEqual(resp_g3.context['question'].age_group, Question.AgeGroup.GROUP_3)
        self.assertContains(resp_g3, 'Ages 14–18')
        self.assertEqual(resp_g3.context['total_questions'], 25)

        # Confirm the two children get distinct questions at index 1
        self.assertNotEqual(resp_g1.context['question'].id, resp_g3.context['question'].id)

    def test_child_cannot_access_another_child_assessment_by_url_change(self):
        # Session set to child1
        session = self.client.session
        session['active_child_id'] = self.child1.id
        session.save()

        # Attempt to access child2's assessment
        url_other = reverse('assessment:question', kwargs={'assessment_id': self.assessment2.id, 'question_index': 1})
        response = self.client.get(url_other)
        # Should be rejected with 403 Forbidden
        self.assertEqual(response.status_code, 403)


class AdminRegistrationTest(TestCase):
    def test_admin_registrations(self):
        self.assertIn(Question, admin.site._registry)
        self.assertIn(Answer, admin.site._registry)


class ChildOwnershipHardeningTest(TestCase):
    """
    Security verification tests for strict Child and Assessment ownership enforcement.
    Ensures unowned records (owner=None) and cross-user records cannot be accessed.
    """
    @classmethod
    def setUpTestData(cls):
        load_initial_questions()

    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username='parent_alice', password='password123')
        self.user_b = User.objects.create_user(username='parent_bob', password='password123')

        # Child and assessment for User A
        self.child_a = Child.objects.create(name="Alice Child", age=10, gender=Child.Gender.FEMALE, owner=self.user_a)
        self.assessment_a = Assessment.objects.create(
            child=self.child_a,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.PENDING
        )

        # Child and assessment for User B
        self.child_b = Child.objects.create(name="Bob Child", age=11, gender=Child.Gender.MALE, owner=self.user_b)
        self.assessment_b = Assessment.objects.create(
            child=self.child_b,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.PENDING
        )

        # Unowned child and assessment (owner=None)
        self.child_unowned = Child.objects.create(name="Orphan Child", age=9, gender=Child.Gender.OTHER, owner=None)
        self.assessment_unowned = Assessment.objects.create(
            child=self.child_unowned,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.PENDING
        )

    def test_user_a_cannot_access_user_b_child_selection(self):
        """User A attempting to view User B's child profile via URL ID is blocked."""
        self.client.login(username='parent_alice', password='password123')
        url = reverse('assessment:selection', kwargs={'child_id': self.child_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_user_a_cannot_initiate_assessment_for_user_b_child(self):
        """User A attempting to start an assessment for User B's child is blocked."""
        self.client.login(username='parent_alice', password='password123')
        url = reverse('assessment:initiate_assessment', kwargs={'child_id': self.child_b.id, 'assessment_type': 'APTITUDE'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_user_a_cannot_access_user_b_questionnaire(self):
        """User A attempting to access User B's questionnaire questions is blocked."""
        self.client.login(username='parent_alice', password='password123')
        url = reverse('assessment:question', kwargs={'assessment_id': self.assessment_b.id, 'question_index': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_cannot_access_unowned_child_selection(self):
        """Strict ownership: accessing a child with owner=None must return 403 Forbidden."""
        self.client.login(username='parent_alice', password='password123')
        url = reverse('assessment:selection', kwargs={'child_id': self.child_unowned.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_cannot_initiate_unowned_child_assessment(self):
        """Strict ownership: starting assessment for unowned child must return 403 Forbidden."""
        self.client.login(username='parent_alice', password='password123')
        url = reverse('assessment:initiate_assessment', kwargs={'child_id': self.child_unowned.id, 'assessment_type': 'APTITUDE'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_cannot_access_unowned_assessment_questionnaire(self):
        """Strict ownership: questionnaire for assessment with unowned child must return 403."""
        self.client.login(username='parent_alice', password='password123')
        url = reverse('assessment:question', kwargs={'assessment_id': self.assessment_unowned.id, 'question_index': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_cannot_access_unowned_assessment_completion(self):
        """Strict ownership: completion view for assessment with unowned child must return 403."""
        self.client.login(username='parent_alice', password='password123')
        url = reverse('assessment:completion', kwargs={'assessment_id': self.assessment_unowned.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_legitimate_owner_can_access_own_child_and_questionnaire(self):
        """Legitimate owner can freely access their child's tracks and questions."""
        self.client.login(username='parent_alice', password='password123')
        url_sel = reverse('assessment:selection', kwargs={'child_id': self.child_a.id})
        resp_sel = self.client.get(url_sel)
        self.assertEqual(resp_sel.status_code, 200)

        url_q = reverse('assessment:question', kwargs={'assessment_id': self.assessment_a.id, 'question_index': 1})
        resp_q = self.client.get(url_q)
        self.assertEqual(resp_q.status_code, 200)
