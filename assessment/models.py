from django.db import models
from core.models import Child


class Assessment(models.Model):
    """
    Represents an assessment attempt for a registered child.
    """
    class AssessmentType(models.TextChoices):
        APTITUDE = 'APTITUDE', 'Aptitude Assessment'
        INTEREST = 'INTEREST', 'Interest Assessment'

    class AssessmentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'

    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name="Child"
    )
    assessment_type = models.CharField(
        max_length=20,
        choices=AssessmentType.choices,
        verbose_name="Assessment Type"
    )
    status = models.CharField(
        max_length=20,
        choices=AssessmentStatus.choices,
        default=AssessmentStatus.PENDING,
        verbose_name="Status"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Completed At"
    )

    class Meta:
        verbose_name = "Assessment Attempt"
        verbose_name_plural = "Assessment Attempts"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_assessment_type_display()} - {self.child.name} ({self.get_status_display()})"


class Question(models.Model):
    """
    Model storing aptitude and interest questions with four multiple-choice options,
    categorized by developmental age group and difficulty level.
    """
    class OptionChoice(models.TextChoices):
        A = 'A', 'Option A'
        B = 'B', 'Option B'
        C = 'C', 'Option C'
        D = 'D', 'Option D'

    class AgeGroup(models.TextChoices):
        GROUP_1 = 'GROUP_1', 'Early Exploration (Ages 5–8)'
        GROUP_2 = 'GROUP_2', 'Developing Reasoning (Ages 9–13)'
        GROUP_3 = 'GROUP_3', 'Advanced Exploration (Ages 14–18)'

    class Difficulty(models.TextChoices):
        EASY = 'EASY', 'Easy'
        MEDIUM = 'MEDIUM', 'Medium'
        HARD = 'HARD', 'Hard'

    assessment_type = models.CharField(
        max_length=20,
        choices=Assessment.AssessmentType.choices,
        verbose_name="Assessment Type",
        help_text="Specifies if question belongs to Aptitude or Interest assessment."
    )
    age_group = models.CharField(
        max_length=20,
        choices=AgeGroup.choices,
        default=AgeGroup.GROUP_2,
        verbose_name="Target Age Group",
        help_text="Developmental stage targeted by this question."
    )
    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM,
        verbose_name="Difficulty Level",
        help_text="Cognitive challenge level for aptitude questions."
    )
    category = models.CharField(
        max_length=100,
        verbose_name="Category / Domain",
        help_text="e.g. Logical Reasoning, Numerical Ability, Science and Technology, etc."
    )
    question_text = models.TextField(
        verbose_name="Question Text"
    )
    option_a = models.CharField(max_length=255, verbose_name="Option A")
    option_b = models.CharField(max_length=255, verbose_name="Option B")
    option_c = models.CharField(max_length=255, verbose_name="Option C")
    option_d = models.CharField(max_length=255, verbose_name="Option D")
    order = models.PositiveIntegerField(
        default=1,
        verbose_name="Display Order",
        help_text="Sequence number of the question."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Only active questions are displayed in the questionnaire."
    )

    # Scoring Design:
    # Aptitude: single correct option (A, B, C, D)
    correct_option = models.CharField(
        max_length=1,
        choices=OptionChoice.choices,
        blank=True,
        null=True,
        verbose_name="Correct Option (Aptitude Only)",
        help_text="Single correct answer for aptitude questions. Leave blank for interest questions."
    )

    # Interest: option category mappings
    option_a_category = models.CharField(max_length=100, blank=True, default="", verbose_name="Option A Category")
    option_b_category = models.CharField(max_length=100, blank=True, default="", verbose_name="Option B Category")
    option_c_category = models.CharField(max_length=100, blank=True, default="", verbose_name="Option C Category")
    option_d_category = models.CharField(max_length=100, blank=True, default="", verbose_name="Option D Category")

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['assessment_type', 'age_group', 'order', 'id']

    def __str__(self):
        return f"[{self.get_assessment_type_display()} - {self.age_group}] {self.category} - Q{self.order}: {self.question_text[:40]}..."

    def get_option_text(self, option_key):
        """Returns the text for a given option key ('A', 'B', 'C', 'D')."""
        key = str(option_key).upper()
        mapping = {
            'A': self.option_a,
            'B': self.option_b,
            'C': self.option_c,
            'D': self.option_d,
        }
        return mapping.get(key, '')

    def get_option_category(self, option_key):
        """Returns the interest category aligned with a given option key ('A', 'B', 'C', 'D')."""
        key = str(option_key).upper()
        mapping = {
            'A': self.option_a_category or self.category,
            'B': self.option_b_category or self.category,
            'C': self.option_c_category or self.category,
            'D': self.option_d_category or self.category,
        }
        return mapping.get(key, self.category)


class Answer(models.Model):
    """
    Model recording a child's selected response to a question within an assessment attempt.
    Enforces a uniqueness constraint so only one answer exists per question per assessment.
    """
    class OptionChoice(models.TextChoices):
        A = 'A', 'Option A'
        B = 'B', 'Option B'
        C = 'C', 'Option C'
        D = 'D', 'Option D'

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="Assessment Attempt"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="Question"
    )
    selected_option = models.CharField(
        max_length=1,
        choices=OptionChoice.choices,
        verbose_name="Selected Option"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Recorded At"
    )

    class Meta:
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        constraints = [
            models.UniqueConstraint(
                fields=['assessment', 'question'],
                name='unique_assessment_question_answer'
            )
        ]
        ordering = ['question__order', 'created_at']

    def __str__(self):
        return f"Assessment #{self.assessment_id} - Q{self.question.order}: Option {self.selected_option}"

    @property
    def is_correct(self):
        """For aptitude assessment: checks if selected option matches question's correct option."""
        if self.question.assessment_type == Assessment.AssessmentType.APTITUDE:
            return bool(self.question.correct_option and self.selected_option.upper() == self.question.correct_option.upper())
        return None

    @property
    def contributed_category(self):
        """For interest assessment: returns the category aligned with the child's selection."""
        return self.question.get_option_category(self.selected_option)


# Re-export Child for backward/cross-import convenience
__all__ = ['Child', 'Assessment', 'Question', 'Answer']
