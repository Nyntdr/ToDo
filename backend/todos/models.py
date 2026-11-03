from django.db import models
from django.contrib.auth.models import User

class Todo(models.Model):
    # Foreign key linking the todo to a specific User
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Newest todos first

    def __str__(self):
        return self.title   #how the todo will be represented in the admin panel and other places