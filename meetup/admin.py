from django.contrib import admin
from .models import Participant, Section, Meeting
from adminsortable2.admin import SortableAdminMixin, SortableTabularInline


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_speaker')
    search_fields = ('name', 'company')
    list_filter = ('is_speaker',)


class MeetingInline(SortableTabularInline):
    model = Meeting
    extra = 1
    fields = ('order', 'title', 'content', 'speakers')


@admin.register(Section)
class SectionAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('title',)
    inlines = (MeetingInline,)


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    pass
