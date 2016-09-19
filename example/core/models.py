from django.db import models


class DocumentTemplate(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return 'pk:{} - {}'.format(self.pk, self.name)
