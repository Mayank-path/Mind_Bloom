from django.db import models
from assessment.models import Assessment


class Result(models.Model):
    """
    Stores calculated evaluation metrics for a completed assessment attempt.
    Enforces a strict one-to-one relationship with the Assessment.
    """
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name="Assessment Attempt"
    )

    # Aptitude Assessment Metrics
    total_questions = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Questions"
    )
    correct_answers = models.PositiveIntegerField(
        default=0,
        verbose_name="Correct Answers"
    )
    incorrect_answers = models.PositiveIntegerField(
        default=0,
        verbose_name="Incorrect Answers"
    )
    overall_percentage = models.FloatField(
        default=0.0,
        verbose_name="Overall Percentage"
    )
    category_scores = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Category Breakdown",
        help_text="Detailed category scores: correct, total, and percentage."
    )
    strongest_categories = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Strongest Categories"
    )
    growth_categories = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Growth Opportunities"
    )

    # Interest Assessment Metrics
    category_distribution = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Interest Distribution",
        help_text="Selection counts and percentages for each interest domain."
    )
    top_interest_categories = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Top Interest Domains"
    )
    secondary_interest_categories = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Secondary Interest Domains"
    )

    # Narrative Summary
    summary = models.TextField(
        blank=True,
        default="",
        verbose_name="Constructive Feedback Summary"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Calculated At"
    )

    class Meta:
        verbose_name = "Assessment Result"
        verbose_name_plural = "Assessment Results"
        ordering = ['-created_at']

    def __str__(self):
        return f"Result #{self.id} for {self.assessment.child.name} ({self.assessment.get_assessment_type_display()})"
