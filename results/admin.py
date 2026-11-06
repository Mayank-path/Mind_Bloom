from django.contrib import admin
from .models import Result


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'child_name',
        'assessment_type',
        'overall_score_display',
        'created_at',
    )
    list_filter = (
        'assessment__assessment_type',
        'created_at',
    )
    search_fields = (
        'assessment__child__name',
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    @admin.display(description="Child Name")
    def child_name(self, obj):
        return obj.assessment.child.name

    @admin.display(description="Assessment Type")
    def assessment_type(self, obj):
        return obj.assessment.get_assessment_type_display()

    @admin.display(description="Overall Score / Key Metric")
    def overall_score_display(self, obj):
        if obj.assessment.assessment_type == 'APTITUDE':
            return f"{obj.overall_percentage:.1f}% ({obj.correct_answers}/{obj.total_questions})"
        top_cats = ", ".join(obj.top_interest_categories[:2])
        return f"Top Interests: {top_cats}" if top_cats else "Recorded"
