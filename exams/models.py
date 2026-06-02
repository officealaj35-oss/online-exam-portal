from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    question = models.TextField(help_text="The exam question text")
    option1 = models.CharField(max_length=255, help_text="First multiple choice option")
    option2 = models.CharField(max_length=255, help_text="Second multiple choice option")
    option3 = models.CharField(max_length=255, help_text="Third multiple choice option")
    option4 = models.CharField(max_length=255, help_text="Fourth multiple choice option")
    
    CORRECT_ANSWER_CHOICES = [
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        ('option3', 'Option 3'),
        ('option4', 'Option 4'),
    ]
    correct_answer = models.CharField(
        max_length=10, 
        choices=CORRECT_ANSWER_CHOICES, 
        help_text="The correct option key"
    )

    def __str__(self):
        return f"Q{self.id}: {self.question[:50]}..."

class StudentAnswer(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    selected_answer = models.CharField(max_length=10, help_text="The option code selected (option1/2/3/4)")
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'question')

    def __str__(self):
        return f"{self.student.username} - Q{self.question.id}: {self.selected_answer}"

class ExamResult(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='exam_result')
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - Score: {self.score}/{self.total_questions} ({self.percentage}%)"