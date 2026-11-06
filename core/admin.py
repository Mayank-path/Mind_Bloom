from django.contrib import admin
from .models import Child


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'gender', 'grade', 'owner', 'created_at')
    list_filter = ('owner', 'gender', 'age', 'created_at')
    search_fields = ('name', 'grade', 'owner__username', 'owner__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
