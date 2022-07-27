from django.contrib import admin
from .models import Participant, Section, Meeting


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_speaker')
    search_fields = ('name', 'company')
    list_filter = ('is_speaker',)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title',)
