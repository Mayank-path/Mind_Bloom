from django.test import TestCase, Client
from django.urls import reverse
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Child
from .forms import ChildRegistrationForm, UserRegistrationForm, MindBloomAuthenticationForm
from assessment.models import Assessment
from results.models import Result


class ChildModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="parent1",
            password="testpassword123",
            email="parent1@example.com"
        )

    def test_create_valid_child_with_owner(self):
        child = Child.objects.create(
            owner=self.user,
            name="Aarav Sharma",
            age=10,
            gender=Child.Gender.MALE,
            grade="Grade 5"
        )
        self.assertEqual(child.name, "Aarav Sharma")
        self.assertEqual(child.age, 10)
        self.assertEqual(child.gender, "MALE")
        self.assertEqual(child.grade, "Grade 5")
        self.assertEqual(child.owner, self.user)
        self.assertIn("Aarav Sharma", str(child))
        self.assertIn("10", str(child))

    def test_child_can_exist_without_owner_for_backward_compatibility(self):
        """Preserves existing records created before authentication was introduced."""
        child = Child.objects.create(
            name="Legacy Child",
            age=8,
            gender=Child.Gender.FEMALE
        )
        self.assertIsNone(child.owner)
        self.assertEqual(child.name, "Legacy Child")

    def test_empty_name_validation(self):
        child = Child(name="   ", age=10, gender=Child.Gender.FEMALE)
        with self.assertRaises(ValidationError):
            child.full_clean()

    def test_age_below_minimum_validation(self):
        child = Child(name="Little Sam", age=4, gender=Child.Gender.MALE)
        with self.assertRaises(ValidationError):
            child.full_clean()

    def test_age_above_maximum_validation(self):
        child = Child(name="Adult Sam", age=19, gender=Child.Gender.MALE)
        with self.assertRaises(ValidationError):
            child.full_clean()

    def test_invalid_gender_choice(self):
        child = Child(name="Sam", age=10, gender="INVALID_GENDER")
        with self.assertRaises(ValidationError):
            child.full_clean()


class ChildRegistrationFormTest(TestCase):
    def test_valid_form_data(self):
        form_data = {
            'name': 'Priya Patel',
            'age': 12,
            'gender': Child.Gender.FEMALE,
            'grade': 'Class 7'
        }
        form = ChildRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        child = form.save()
        self.assertEqual(child.name, 'Priya Patel')

    def test_missing_name_rejected(self):
        form = ChildRegistrationForm(data={'age': 10, 'gender': Child.Gender.MALE})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_invalid_age_rejected(self):
        form = ChildRegistrationForm(data={
            'name': 'Karan',
            'age': 3,
            'gender': Child.Gender.MALE
        })
        self.assertFalse(form.is_valid())
        self.assertIn('age', form.errors)

    def test_optional_grade_allowed_empty(self):
        form = ChildRegistrationForm(data={
            'name': 'Karan',
            'age': 8,
            'gender': Child.Gender.MALE,
            'grade': ''
        })
        self.assertTrue(form.is_valid())


class UserAuthenticationAndSessionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = "testparent"
        self.password = "ValidPassword123!"
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email="testparent@mindbloom.edu",
            first_name="Priya"
        )

    def test_user_registration_success(self):
        """New parent registers account and is automatically logged in."""
        reg_data = {
            'username': 'neweducator',
            'first_name': 'Anita Roy',
            'email': 'anita@example.com',
            'password1': 'SecurePass2026!',
            'password2': 'SecurePass2026!',
        }
        response = self.client.post(reverse('core:register'), data=reg_data)
        self.assertRedirects(response, reverse('assessment:register'))
        self.assertTrue(User.objects.filter(username='neweducator').exists())
        # Check user is logged in
        new_user = User.objects.get(username='neweducator')
        self.assertEqual(int(self.client.session['_auth_user_id']), new_user.id)

    def test_user_registration_mismatched_passwords(self):
        """Registration fails when password confirmation does not match."""
        reg_data = {
            'username': 'mismatchuser',
            'first_name': 'Test User',
            'email': 'mismatch@example.com',
            'password1': 'SecurePass2026!',
            'password2': 'DifferentPass!',
        }
        response = self.client.post(reverse('core:register'), data=reg_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatchuser').exists())

    def test_login_successful_with_valid_credentials(self):
        """Valid credentials authenticate user, start session, and redirect."""
        response = self.client.post(reverse('core:login'), {
            'username': self.username,
            'password': self.password,
        })
        self.assertRedirects(response, reverse('results:overview'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)

    def test_login_with_next_redirect(self):
        """When ?next= parameter is present, redirect to requested protected page."""
        target_url = reverse('assessment:register')
        login_url = f"{reverse('core:login')}?next={target_url}"
        response = self.client.post(login_url, {
            'username': self.username,
            'password': self.password,
            'next': target_url,
        })
        self.assertRedirects(response, target_url)

    def test_login_rejected_with_invalid_credentials(self):
        """Invalid credentials show error and do not establish a session."""
        response = self.client.post(reverse('core:login'), {
            'username': self.username,
            'password': 'WrongPassword123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/login.html')
        self.assertContains(response, 'Invalid username or password')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_clears_session_and_child_state(self):
        """Logout flushes authentication and active_child_id from session."""
        self.client.login(username=self.username, password=self.password)
        session = self.client.session
        session['active_child_id'] = 99
        session.save()

        response = self.client.get(reverse('core:logout'))
        self.assertRedirects(response, reverse('core:home'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertNotIn('active_child_id', self.client.session)


class CoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_view(self):
        url = reverse('core:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'MindBloom')

    def test_about_view(self):
        url = reverse('core:about')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/about.html')

    def test_contact_view(self):
        url = reverse('core:contact')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/contact.html')

    def test_register_redirect_unauthenticated(self):
        """Unauthenticated visitor to /register-child/ redirects to account register."""
        url = reverse('core:register_child')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('core:register'))


class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='parent_anita', password='Password123!', first_name='Anita')
        self.user2 = User.objects.create_user(username='parent_vikram', password='Password123!', first_name='Vikram')

        # User 1 has 2 children
        self.child1 = Child.objects.create(name="Rohan Roy", age=7, gender=Child.Gender.MALE, owner=self.user1, grade="Class 2")
        self.child2 = Child.objects.create(name="Ananya Roy", age=12, gender=Child.Gender.FEMALE, owner=self.user1, grade="Class 7")

        # User 2 has 1 child
        self.child_u2 = Child.objects.create(name="Kavya Verma", age=15, gender=Child.Gender.FEMALE, owner=self.user2)

        # Unowned child
        self.child_orphan = Child.objects.create(name="Unowned Child", age=9, gender=Child.Gender.OTHER, owner=None)

        # Assessments for User 1's children:
        # child1: 1 completed aptitude, 1 pending interest
        self.asmt1 = Assessment.objects.create(
            child=self.child1,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        self.res1 = Result.objects.create(
            assessment=self.asmt1,
            overall_percentage=80.0,
            total_questions=25,
            correct_answers=20
        )
        self.asmt2 = Assessment.objects.create(
            child=self.child1,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.PENDING
        )

        # child2: 1 completed interest
        self.asmt3 = Assessment.objects.create(
            child=self.child2,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        self.res3 = Result.objects.create(
            assessment=self.asmt3,
            total_questions=25,
            top_interest_categories=["Science and Technology", "Arts and Creativity"]
        )

        # Assessment for user2
        self.asmt_u2 = Assessment.objects.create(
            child=self.child_u2,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )

    def test_unauthenticated_visitor_redirected_to_login(self):
        """Visiting dashboard without authentication redirects to login."""
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_authenticated_parent_access_dashboard(self):
        """Authenticated parent can access dashboard successfully."""
        self.client.login(username='parent_anita', password='Password123!')
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/dashboard.html')
        self.assertContains(response, 'Welcome back, Anita!')

    def test_dashboard_displays_only_current_user_children(self):
        """Dashboard lists current user's children and excludes other users' and unowned children."""
        self.client.login(username='parent_anita', password='Password123!')
        response = self.client.get(reverse('core:dashboard'))
        self.assertContains(response, 'Rohan Roy')
        self.assertContains(response, 'Ananya Roy')
        self.assertNotContains(response, 'Kavya Verma')
        self.assertNotContains(response, 'Unowned Child')

    def test_dashboard_statistics_accurate(self):
        """Dashboard statistics strictly compute counts for the logged-in user's records."""
        self.client.login(username='parent_anita', password='Password123!')
        response = self.client.get(reverse('core:dashboard'))
        # user1 has: 2 children, 3 assessments (2 completed, 1 pending)
        self.assertEqual(response.context['total_children'], 2)
        self.assertEqual(response.context['total_assessments'], 3)
        self.assertEqual(response.context['completed_assessments_count'], 2)
        self.assertEqual(response.context['pending_assessments_count'], 1)

    def test_empty_dashboard_renders_correctly(self):
        """Parent with no registered children sees friendly empty state with action link."""
        empty_user = User.objects.create_user(username='new_parent', password='Password123!')
        self.client.login(username='new_parent', password='Password123!')
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_children'], 0)
        self.assertContains(response, 'No Children Registered Yet')
        self.assertContains(response, 'Add Your First Child')

    def test_multiple_child_profiles_display_correctly(self):
        """Dashboard renders multiple child cards with developmental stage and action buttons."""
        self.client.login(username='parent_anita', password='Password123!')
        response = self.client.get(reverse('core:dashboard'))
        self.assertContains(response, 'Early Exploration (Ages 5–8)')
        self.assertContains(response, 'Developing Reasoning (Ages 9–13)')
        self.assertContains(response, 'View Profile')
        self.assertContains(response, 'Start Assessment')


class ChildProfileAndManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='parent1', password='Password123!')
        self.user2 = User.objects.create_user(username='parent2', password='Password123!')
        self.child1 = Child.objects.create(
            name="Maya Patel",
            age=10,
            gender=Child.Gender.FEMALE,
            owner=self.user1,
            grade="Grade 5"
        )
        self.child2 = Child.objects.create(
            name="Kabir Joshi",
            age=14,
            gender=Child.Gender.MALE,
            owner=self.user2
        )
        self.child_unowned = Child.objects.create(
            name="Ghost Child",
            age=8,
            gender=Child.Gender.MALE,
            owner=None
        )
        self.client.login(username='parent1', password='Password123!')

    def test_parent_can_view_own_child_detail(self):
        """Parent can view their own child's detail page."""
        url = reverse('core:child_detail', kwargs={'child_id': self.child1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/child_detail.html')
        self.assertContains(response, 'Maya Patel')
        self.assertContains(response, 'Developing Reasoning (Ages 9–13)')

    def test_parent_cannot_view_other_users_child_detail_403(self):
        """Parent cannot view another user's child detail page; receives 403 Forbidden."""
        url = reverse('core:child_detail', kwargs={'child_id': self.child2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_parent_cannot_view_unowned_child_detail_403(self):
        """Accessing unowned child profile raises 403 Forbidden."""
        url = reverse('core:child_detail', kwargs={'child_id': self.child_unowned.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_parent_can_edit_own_child(self):
        """Parent can update their own child's information."""
        url = reverse('core:child_edit', kwargs={'child_id': self.child1.id})
        response = self.client.post(url, {
            'name': 'Maya Patel Updated',
            'age': 11,
            'gender': Child.Gender.FEMALE,
            'grade': 'Grade 6',
        })
        self.assertRedirects(response, reverse('core:child_detail', kwargs={'child_id': self.child1.id}))
        self.child1.refresh_from_db()
        self.assertEqual(self.child1.name, 'Maya Patel Updated')
        self.assertEqual(self.child1.age, 11)
        self.assertEqual(self.child1.grade, 'Grade 6')

    def test_parent_cannot_edit_other_users_child_403(self):
        """Parent cannot edit another user's child profile; receives 403 Forbidden."""
        url = reverse('core:child_edit', kwargs={'child_id': self.child2.id})
        response = self.client.post(url, {
            'name': 'Hacked Name',
            'age': 12,
            'gender': Child.Gender.MALE,
        })
        self.assertEqual(response.status_code, 403)
        self.child2.refresh_from_db()
        self.assertEqual(self.child2.name, 'Kabir Joshi')

    def test_parent_cannot_delete_other_users_child_403(self):
        """Parent cannot delete another user's child profile; receives 403 Forbidden."""
        url = reverse('core:child_delete', kwargs={'child_id': self.child2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Child.objects.filter(id=self.child2.id).exists())

    def test_parent_can_delete_own_child_with_cascade(self):
        """Parent can delete their child, cascading deletion across assessments and results."""
        asmt = Assessment.objects.create(
            child=self.child1,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED
        )
        res = Result.objects.create(assessment=asmt, overall_percentage=75.0)

        # GET confirms deletion page renders warning summary
        url = reverse('core:child_delete', kwargs={'child_id': self.child1.id})
        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, 'Confirm Deletion')

        # POST executes safe deletion
        post_resp = self.client.post(url)
        self.assertRedirects(post_resp, reverse('core:dashboard'))
        self.assertFalse(Child.objects.filter(id=self.child1.id).exists())
        self.assertFalse(Assessment.objects.filter(id=asmt.id).exists())
        self.assertFalse(Result.objects.filter(id=res.id).exists())

    def test_child_age_change_updates_age_group_display_without_affecting_historical_results(self):
        """Updating child age recalculates age_group property while preserving historical results."""
        # Create an assessment and result with initial age 10 (GROUP_2)
        asmt = Assessment.objects.create(
            child=self.child1,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED
        )
        res = Result.objects.create(assessment=asmt, overall_percentage=85.0)

        # Edit age from 10 to 15 (moving to GROUP_3: Advanced Exploration)
        url = reverse('core:child_edit', kwargs={'child_id': self.child1.id})
        self.client.post(url, {
            'name': 'Maya Patel',
            'age': 15,
            'gender': Child.Gender.FEMALE,
            'grade': 'Grade 10',
        })
        self.child1.refresh_from_db()
        self.assertEqual(self.child1.age, 15)
        self.assertEqual(self.child1.age_group, 'GROUP_3')
        self.assertIn('Advanced Exploration', self.child1.age_group_display)

        # Historical result remains identical and unchanged
        res.refresh_from_db()
        self.assertEqual(res.overall_percentage, 85.0)

    def test_child_add_creates_child_assigned_to_user(self):
        """Convenience child_add view creates child assigned to request.user."""
        url = reverse('core:child_add')
        response = self.client.post(url, {
            'name': 'Samarth Patel',
            'age': 6,
            'gender': Child.Gender.MALE,
            'grade': 'Class 1',
        })
        sam = Child.objects.get(name='Samarth Patel')
        self.assertEqual(sam.owner, self.user1)
        self.assertRedirects(response, reverse('core:child_detail', kwargs={'child_id': sam.id}))


class AssessmentHistoryAndComparisonTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='parent_deepa', password='Password123!')
        self.child = Child.objects.create(
            name="Deepa Child",
            age=10,
            gender=Child.Gender.FEMALE,
            owner=self.user
        )
        self.client.login(username='parent_deepa', password='Password123!')

    def test_completed_and_pending_assessments_in_history(self):
        """Assessment history lists completed attempts with results and pending attempts with continue link."""
        asmt_comp = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        Result.objects.create(assessment=asmt_comp, overall_percentage=76.0)

        asmt_pend = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.PENDING
        )

        url = reverse('core:child_detail', kwargs={'child_id': self.child.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '76.0%')
        self.assertContains(response, 'View Report')
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'Continue')

    def test_interest_assessment_does_not_display_aptitude_percentage(self):
        """Interest assessment history displays interest domains and never aptitude percentage."""
        asmt_int = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        Result.objects.create(
            assessment=asmt_int,
            top_interest_categories=["Arts and Creativity", "Nature and Exploration"]
        )

        url = reverse('core:child_detail', kwargs={'child_id': self.child.id})
        response = self.client.get(url)
        self.assertContains(response, 'Arts and Creativity')
        # Percentage format (e.g. %) must only belong to aptitude assessments
        # Check that result_display for interest item does not end in %
        history_items = response.context['history_items']
        int_item = next(item for item in history_items if item['assessment'].id == asmt_int.id)
        self.assertFalse(int_item['result_display'].endswith('%'))

    def test_empty_assessment_history_renders_gracefully(self):
        """Child with zero assessments displays encouraging empty state."""
        new_child = Child.objects.create(name="Fresh Learner", age=7, gender=Child.Gender.MALE, owner=self.user)
        url = reverse('core:child_detail', kwargs={'child_id': new_child.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No assessments have been recorded for Fresh Learner yet')

    def test_multiple_aptitude_attempts_compare_correctly(self):
        """When multiple aptitude assessments are completed, chronological score difference is computed."""
        t1 = timezone.now() - timezone.timedelta(days=7)
        t2 = timezone.now()

        asmt1 = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=t1
        )
        Result.objects.create(
            assessment=asmt1,
            overall_percentage=60.0,
            category_scores={'Logical Reasoning': {'percentage': 50.0}}
        )

        asmt2 = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=t2
        )
        Result.objects.create(
            assessment=asmt2,
            overall_percentage=80.0,
            category_scores={'Logical Reasoning': {'percentage': 75.0}}
        )

        url = reverse('core:child_detail', kwargs={'child_id': self.child.id})
        response = self.client.get(url)
        apt_comp = response.context['apt_comparison']
        self.assertIsNotNone(apt_comp)
        self.assertTrue(apt_comp['has_comparison'])
        self.assertEqual(apt_comp['prev_pct'], 60.0)
        self.assertEqual(apt_comp['curr_pct'], 80.0)
        self.assertEqual(apt_comp['diff'], 20.0)
        self.assertContains(response, '+20.0%')

    def test_multiple_interest_attempts_compare_correctly(self):
        """When multiple interest assessments are completed, distribution shifts are computed."""
        t1 = timezone.now() - timezone.timedelta(days=10)
        t2 = timezone.now()

        asmt1 = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=t1
        )
        Result.objects.create(
            assessment=asmt1,
            category_distribution={'Science and Technology': {'percentage': 20.0}}
        )

        asmt2 = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=t2
        )
        Result.objects.create(
            assessment=asmt2,
            category_distribution={'Science and Technology': {'percentage': 40.0}}
        )

        url = reverse('core:child_detail', kwargs={'child_id': self.child.id})
        response = self.client.get(url)
        int_comp = response.context['int_comparison']
        self.assertIsNotNone(int_comp)
        self.assertTrue(int_comp['has_comparison'])
        sci_cat = next(c for c in int_comp['categories'] if c['category'] == 'Science and Technology')
        self.assertEqual(sci_cat['prev_pct'], 20.0)
        self.assertEqual(sci_cat['curr_pct'], 40.0)
        self.assertEqual(sci_cat['diff'], 20.0)

    def test_single_attempt_state_renders_help_message_no_comparison(self):
        """When exactly one completed attempt exists, comparison displays unlock instruction message."""
        asmt = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        Result.objects.create(assessment=asmt, overall_percentage=72.0)

        url = reverse('core:child_detail', kwargs={'child_id': self.child.id})
        response = self.client.get(url)
        self.assertIsNone(response.context['apt_comparison'])
        self.assertContains(response, 'One Aptitude Assessment Completed')
        self.assertContains(response, 'Complete another Aptitude assessment in the future to unlock longitudinal score progression')

    def test_different_assessment_types_never_compared(self):
        """1 Aptitude + 1 Interest assessment do NOT trigger comparison because types differ."""
        asmt_apt = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.APTITUDE,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        Result.objects.create(assessment=asmt_apt, overall_percentage=80.0)

        asmt_int = Assessment.objects.create(
            child=self.child,
            assessment_type=Assessment.AssessmentType.INTEREST,
            status=Assessment.AssessmentStatus.COMPLETED,
            completed_at=timezone.now()
        )
        Result.objects.create(assessment=asmt_int, top_interest_categories=["Arts and Creativity"])

        url = reverse('core:child_detail', kwargs={'child_id': self.child.id})
        response = self.client.get(url)
        # Neither should have a comparison active
        self.assertIsNone(response.context['apt_comparison'])
        self.assertIsNone(response.context['int_comparison'])


class DemoDataCommandAndErrorPagesTest(TestCase):
    def test_setup_demo_data_command_execution_and_idempotency(self):
        """Management command setup_demo_data executes cleanly and is strictly idempotent."""
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command('setup_demo_data', stdout=out)
        self.assertIn("MindBloom demonstration dataset ready!", out.getvalue())

        # Verify demo user
        demo_user = User.objects.get(username='demo_parent')
        self.assertEqual(demo_user.email, 'parent@mindbloom.edu')
        self.assertTrue(demo_user.check_password('DemoPass2026!'))

        # Verify children with distinct age groups
        children = Child.objects.filter(owner=demo_user)
        self.assertGreaterEqual(children.count(), 2)
        age_groups = set(ch.age_group for ch in children)
        self.assertIn('GROUP_1', age_groups)
        self.assertIn('GROUP_2', age_groups)

        # Verify completed and pending assessments
        asmts = Assessment.objects.filter(child__owner=demo_user)
        self.assertTrue(asmts.filter(status=Assessment.AssessmentStatus.COMPLETED).exists())
        self.assertTrue(asmts.filter(status=Assessment.AssessmentStatus.PENDING).exists())

        # Second run: strict idempotency test (count must not change)
        count_before = (User.objects.count(), Child.objects.count(), Assessment.objects.count())
        call_command('setup_demo_data', stdout=out)
        count_after = (User.objects.count(), Child.objects.count(), Assessment.objects.count())
        self.assertEqual(count_before, count_after)

    def test_error_templates_rendered(self):
        """Custom user-friendly error templates exist and render without server failure."""
        from django.template.loader import render_to_string
        rendered_403 = render_to_string('403.html')
        rendered_404 = render_to_string('404.html')
        rendered_500 = render_to_string('500.html')

        self.assertIn('403 Forbidden', rendered_403)
        self.assertIn('Access Denied', rendered_403)
        self.assertIn('404 Not Found', rendered_404)
        self.assertIn('Page Not Found', rendered_404)
        self.assertIn('500 Internal Error', rendered_500)
        self.assertIn('An Unexpected Error Occurred', rendered_500)


