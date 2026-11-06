from django.contrib import admin
from .models import Assessment, Question, Answer


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'child', 'assessment_type', 'status', 'created_at', 'completed_at')
    list_filter = ('assessment_type', 'status', 'created_at')
    search_fields = ('child__name',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'assessment_type',
        'age_group',
        'difficulty',
        'category',
        'question_text_truncated',
        'correct_option',
        'is_active',
    )
    list_filter = (
        'assessment_type',
        'age_group',
        'difficulty',
        'category',
        'is_active',
    )
    search_fields = (
        'question_text',
        'category',
        'option_a',
        'option_b',
        'option_c',
        'option_d',
    )
    ordering = ('assessment_type', 'age_group', 'order', 'id')
    list_editable = ('order', 'is_active')

    @admin.display(description="Question Text")
    def question_text_truncated(self, obj):
        return obj.question_text[:60] + "..." if len(obj.question_text) > 60 else obj.question_text


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'assessment',
        'question_display',
        'selected_option',
        'is_correct_display',
        'created_at',
    )
    list_filter = (
        'assessment__assessment_type',
        'selected_option',
        'created_at',
    )
    search_fields = (
        'assessment__child__name',
        'question__question_text',
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    @admin.display(description="Question")
    def question_display(self, obj):
        return f"Q{obj.question.order}: {obj.question.category}"

    @admin.display(description="Is Correct (Aptitude)", boolean=True)
    def is_correct_display(self, obj):
        return obj.is_correct
