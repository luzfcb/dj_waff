from django.contrib import admin

from . import models


@admin.register(models.DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    pass
