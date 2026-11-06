from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Child(models.Model):
    """
    Represents a child taking an aptitude or interest assessment.
    Each child profile is managed by an authenticated parent or educator account.
    """
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'
        PREFER_NOT_TO_SAY = 'PREFER_NOT_TO_SAY', 'Prefer not to say'

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
        verbose_name="Parent / Educator Account",
        help_text="The registered user account that manages this child profile."
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Child's Full Name",
        help_text="Enter the full name of the child (max 100 characters)."
    )
    age = models.PositiveIntegerField(
        validators=[
            MinValueValidator(5, message="Age must be at least 5 years."),
            MaxValueValidator(18, message="Age must not exceed 18 years.")
        ],
        verbose_name="Age (Years)",
        help_text="Age must be between 5 and 18 years."
    )
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        verbose_name="Gender"
    )
    grade = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Grade / Class (Optional)",
        help_text="e.g. Grade 4, 6th Standard, etc."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Registration Date"
    )

    class Meta:
        verbose_name = "Child Profile"
        verbose_name_plural = "Child Profiles"
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        if self.name is not None and not self.name.strip():
            raise ValidationError({'name': 'Name cannot be empty or blank.'})
        if self.age is not None and (self.age < 5 or self.age > 18):
            raise ValidationError({'age': 'Age must be between 5 and 18.'})

    def __str__(self):
        return f"{self.name} (Age: {self.age})"

    @property
    def age_group(self):
        """Returns the developmental age group key ('GROUP_1', 'GROUP_2', 'GROUP_3')."""
        from assessment.utils import get_age_group
        return get_age_group(self.age)

    @property
    def age_group_display(self):
        """Returns human-friendly label for the child's age group."""
        from assessment.utils import get_age_group_label
        return get_age_group_label(self.age)
