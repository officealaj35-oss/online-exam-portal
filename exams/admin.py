import csv
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from .models import Question, StudentAnswer, ExamResult

@admin.action(description="Export Selected Results to CSV")
def export_results_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="samyak_exam_results.csv"'
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Email', 'Score', 'Total Questions', 'Percentage', 'Submission Time'])
    for result in queryset:
        writer.writerow([
            result.student.username,
            result.student.email,
            result.score,
            result.total_questions,
            f"{result.percentage}%",
            result.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    return response

class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    readonly_fields = ('question', 'selected_answer', 'correct_answer_display')
    can_delete = False
    
    def correct_answer_display(self, obj):
        if obj.question:
            return obj.question.correct_answer
        return "-"
    correct_answer_display.short_description = "Correct Answer"

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_preview', 'correct_answer')
    list_filter = ('correct_answer',)
    search_fields = ('question', 'option1', 'option2', 'option3', 'option4')
    ordering = ('id',)

    def question_preview(self, obj):
        return obj.question[:75] + "..." if len(obj.question) > 75 else obj.question
    question_preview.short_description = "Question"

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student_display', 'score', 'total_questions', 'percentage_display', 'pass_status_display', 'submitted_at', 'view_answers_link')
    list_filter = ('submitted_at',)
    search_fields = ('student__username', 'student__email')
    actions = [export_results_csv]
    readonly_fields = ('student', 'score', 'total_questions', 'percentage', 'submitted_at')
    
    def student_display(self, obj):
        return obj.student.username
    student_display.short_description = "Student Name"

    def percentage_display(self, obj):
        return f"{obj.percentage}%"
    percentage_display.short_description = "Percentage"

    def pass_status_display(self, obj):
        passed = obj.percentage >= 50.0
        color = "#10b981" if passed else "#ef4444"
        text = "PASS" if passed else "FAIL"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, text)
    pass_status_display.short_description = "Status"

    def view_answers_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.student.id])
        return format_html('<a href="{}" target="_blank">View Student Answers & Profile</a>', url)
    view_answers_link.short_description = "Actions"

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('student', 'question_preview', 'selected_answer', 'correct_answer_display', 'is_correct_display')
    list_filter = ('student', 'selected_answer')
    search_fields = ('student__username', 'question__question')
    readonly_fields = ('student', 'question', 'selected_answer')

    def question_preview(self, obj):
        return obj.question.question[:60] + "..." if len(obj.question.question) > 60 else obj.question.question
    question_preview.short_description = "Question"

    def correct_answer_display(self, obj):
        return obj.question.correct_answer
    correct_answer_display.short_description = "Correct Answer"

    def is_correct_display(self, obj):
        is_correct = obj.selected_answer == obj.question.correct_answer
        color = "#10b981" if is_correct else "#ef4444"
        text = "Correct" if is_correct else "Incorrect"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, text)
    is_correct_display.short_description = "Verification"