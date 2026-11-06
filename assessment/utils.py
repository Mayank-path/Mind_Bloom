"""
MindBloom - Assessment Utility Functions
Handles age-group classification and developmental stage mapping.
"""

AGE_GROUP_CHOICES = [
    ('GROUP_1', 'Early Exploration (Ages 5–8)'),
    ('GROUP_2', 'Developing Reasoning (Ages 9–13)'),
    ('GROUP_3', 'Advanced Exploration (Ages 14–18)'),
]

AGE_GROUP_LABELS = dict(AGE_GROUP_CHOICES)


def get_age_group(age):
    """
    Classifies a child's age into one of three developmental groups:
    - GROUP_1: 5–8 years (Early exploration)
    - GROUP_2: 9–13 years (Developing reasoning)
    - GROUP_3: 14–18 years (Advanced exploration)

    Boundaries handled:
    - 5 <= age <= 8 -> GROUP_1
    - 9 <= age <= 13 -> GROUP_2
    - 14 <= age <= 18 -> GROUP_3

    Raises:
        ValueError: If age is None, non-integer, or outside 5–18.
    """
    if age is None or isinstance(age, bool):
        raise ValueError("Child age cannot be None or boolean.")
    if not isinstance(age, int):
        raise ValueError(f"Age must be a valid integer, got {age!r}.")

    if age < 5 or age > 18:
        raise ValueError(f"Age {age} is outside the supported 5–18 years range.")

    if 5 <= age <= 8:
        return 'GROUP_1'
    elif 9 <= age <= 13:
        return 'GROUP_2'
    else:
        return 'GROUP_3'


def get_age_group_label(age):
    """
    Returns the human-friendly label for a child's age group.
    """
    group_key = get_age_group(age)
    return AGE_GROUP_LABELS.get(group_key, group_key)
