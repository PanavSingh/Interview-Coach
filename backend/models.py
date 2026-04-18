from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=200, blank=True)
    skills = models.TextField(blank=True)
    experience = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} — {self.role}"


class InterviewSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    domain = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_questions = models.IntegerField(default=5)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Session {self.pk} — {self.user.username} — {self.domain}"


class Answer(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='answers')
    question_number = models.IntegerField()
    question_text = models.TextField()
    answer_text = models.TextField(blank=True)
    ai_feedback = models.TextField(blank=True)
    ai_score = models.IntegerField(null=True, blank=True)
    skipped = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question_number']
        unique_together = ['session', 'question_number']

    def __str__(self):
        return f"Q{self.question_number} — Session {self.session_id}"
