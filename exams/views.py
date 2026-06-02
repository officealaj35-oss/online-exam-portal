import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from .models import Question, StudentAnswer, ExamResult

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.user.is_authenticated:
        if ExamResult.objects.filter(student=request.user).exists():
            return redirect('result')
        return redirect('home')

    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if ExamResult.objects.filter(student=user).exists():
                return redirect('result')
            return redirect('home')
        else:
            error_message = "Invalid username or password."

    return render(request, 'login.html', {'error': error_message})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def exam_view(request):
    user = request.user
    
    if ExamResult.objects.filter(student=user).exists():
        return redirect('result')
        
    questions = Question.objects.all().order_by('id')
    if not questions.exists():
        return render(request, 'exam.html', {'no_questions': True})
        
    now = timezone.now()
    exam_duration_seconds = 3600
    
    if 'exam_start_time' not in request.session:
        request.session['exam_start_time'] = now.isoformat()
        time_left = exam_duration_seconds
    else:
        start_time = timezone.datetime.fromisoformat(request.session['exam_start_time'])
        elapsed = (now - start_time).total_seconds()
        time_left = max(0, int(exam_duration_seconds - elapsed))
        
        if time_left <= 0:
            return auto_submit_exam(request)
            
    existing_answers = {
        ans.question_id: ans.selected_answer
        for ans in StudentAnswer.objects.filter(student=user)
    }
    
    questions_list = []
    for idx, q in enumerate(questions, 1):
        questions_list.append({
            'id': q.id,
            'number': idx,
            'question': q.question,
            'option1': q.option1,
            'option2': q.option2,
            'option3': q.option3,
            'option4': q.option4,
            'saved_answer': existing_answers.get(q.id, '')
        })

    context = {
        'questions': questions_list,
        'time_left': time_left,
        'username': user.username
    }
    return render(request, 'exam.html', context)

@login_required
def save_answer_api(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method'}, status=405)
        
    user = request.user
    if ExamResult.objects.filter(student=user).exists():
        return JsonResponse({'status': 'error', 'message': 'Exam already submitted'}, status=403)
        
    try:
        data = json.loads(request.body)
        question_id = int(data.get('question_id'))
        selected_answer = data.get('selected_answer', '').strip()
        
        if not selected_answer:
            StudentAnswer.objects.filter(student=user, question_id=question_id).delete()
            return JsonResponse({'status': 'success', 'cleared': True})
            
        with transaction.atomic():
            question = Question.objects.get(id=question_id)
            StudentAnswer.objects.update_or_create(
                student=user,
                question=question,
                defaults={'selected_answer': selected_answer}
            )
            
        return JsonResponse({'status': 'success'})
        
    except Question.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Question not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def submit_exam_api(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method'}, status=405)
        
    user = request.user
    if ExamResult.objects.filter(student=user).exists():
        return JsonResponse({'status': 'error', 'message': 'Exam already submitted'}, status=403)
        
    result = calculate_and_save_result(user)
    
    if 'exam_start_time' in request.session:
        del request.session['exam_start_time']
        
    return JsonResponse({
        'status': 'success', 
        'redirect_url': '/result/'
    })

def auto_submit_exam(request):
    user = request.user
    if not ExamResult.objects.filter(student=user).exists():
        calculate_and_save_result(user)
    if 'exam_start_time' in request.session:
        del request.session['exam_start_time']
    return redirect('result')

def calculate_and_save_result(user):
    questions = Question.objects.all()
    total_questions = questions.count()
    
    student_answers = {
        ans.question_id: ans.selected_answer
        for ans in StudentAnswer.objects.filter(student=user)
    }
    
    score = 0
    for q in questions:
        selected = student_answers.get(q.id)
        if selected == q.correct_answer:
            score += 1
            
    percentage = 0.00
    if total_questions > 0:
        percentage = round((score / total_questions) * 100, 2)
        
    with transaction.atomic():
        result, created = ExamResult.objects.get_or_create(
            student=user,
            defaults={
                'score': score,
                'total_questions': total_questions,
                'percentage': percentage
            }
        )
        
    return result

@login_required
def result_view(request):
    user = request.user
    try:
        result = ExamResult.objects.get(student=user)
        passed = result.percentage >= 50.00
        context = {
            'result': result,
            'passed': passed,
            'username': user.username
        }
        return render(request, 'result.html', context)
    except ExamResult.DoesNotExist:
        return redirect('home')