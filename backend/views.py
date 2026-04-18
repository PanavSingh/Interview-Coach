from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import UserProfile, InterviewSession, Answer
from .ai_service import generate_questions, evaluate_answer

DOMAINS = [
    {"id": "hr",     "label": "Human Resources", "icon": "🤝", "sub": "People & Culture"},
    {"id": "tech",   "label": "Technology",       "icon": "💻", "sub": "Engineering & IT"},
    {"id": "biz",    "label": "Business",          "icon": "📊", "sub": "Strategy & Ops"},
    {"id": "mkt",    "label": "Marketing",         "icon": "📣", "sub": "Growth & Brand"},
    {"id": "health", "label": "Healthcare",        "icon": "🏥", "sub": "Medicine & Care"},
    {"id": "edu",    "label": "Education",         "icon": "🎓", "sub": "Learning & Dev"},
]


def login_view(request):
    error = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'guest':
            request.session.flush()
            request.session['is_guest'] = True
            return redirect('domain')

        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        if not email or not password:
            error = "Please enter both your email and password."
        else:
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                return redirect('domain')
            if not User.objects.filter(username=email).exists():
                user = User.objects.create_user(username=email, email=email, password=password)
                UserProfile.objects.create(user=user)
                login(request, user)
                return redirect('domain')
            error = "Invalid credentials. Please try again."

    return render(request, 'interview/login.html', {'error': error})


def logout_view(request):
    request.session.flush()
    logout(request)
    return redirect('login')


def _is_logged_in(request):
    return request.user.is_authenticated or request.session.get('is_guest')


def domain_view(request):
    if not _is_logged_in(request):
        return redirect('login')
    error = None
    if request.method == 'POST':
        domain = request.POST.get('domain', '').strip()
        custom = request.POST.get('custom_domain', '').strip()
        chosen = custom if custom else domain
        if not chosen:
            error = "Please select or enter a domain."
        else:
            request.session['domain'] = chosen
            return redirect('profile')
    return render(request, 'interview/domain.html', {
        'domains': DOMAINS,
        'error': error,
        'selected': request.session.get('domain', ''),
    })


def profile_view(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not request.session.get('domain'):
        return redirect('domain')

    profile_data = {}
    if request.user.is_authenticated:
        up = getattr(request.user, 'profile', None)
        if up:
            profile_data = {'role': up.role, 'skills': up.skills, 'experience': up.experience}

    error = None
    if request.method == 'POST':
        role = request.POST.get('role', '').strip()
        skills = request.POST.get('skills', '').strip()
        exp = request.POST.get('experience', '').strip()
        if not role:
            error = "Please enter your target role."
        else:
            profile_data = {'role': role, 'skills': skills, 'experience': exp}
            request.session['profile'] = profile_data

            if request.user.is_authenticated:
                up, _ = UserProfile.objects.get_or_create(user=request.user)
                up.role, up.skills, up.experience = role, skills, exp
                up.save()

            domain = request.session['domain']
            questions = generate_questions(domain, role, skills, exp)
            request.session['questions'] = questions
            request.session['question_number'] = 1
            request.session['answers'] = {}

            if request.user.is_authenticated:
                session_obj = InterviewSession.objects.create(
                    user=request.user, domain=domain, role=role,
                    total_questions=len(questions),
                )
                request.session['session_id'] = session_obj.pk

            return redirect('interview')

    return render(request, 'interview/profile.html', {
        'domain': request.session['domain'],
        'profile': profile_data if profile_data.get('role') else request.session.get('profile', {}),
        'error': error,
    })


def interview_view(request):
    if not _is_logged_in(request):
        return redirect('login')
    if not request.session.get('domain'):
        return redirect('domain')
    if not request.session.get('profile'):
        return redirect('profile')

    questions = request.session.get('questions', [])
    if not questions:
        return redirect('profile')

    qn = request.session.get('question_number', 1)
    total = len(questions)

    error = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'next':
            answer_text = request.POST.get('answer', '').strip()
            if not answer_text:
                error = "Please type an answer or click Skip."
        if action in ('next', 'skip') and not error:
            answer_text = request.POST.get('answer', '').strip() if action == 'next' else ''
            skipped = action == 'skip'

            feedback_data = {}
            if not skipped and answer_text:
                feedback_data = evaluate_answer(
                    questions[qn - 1], answer_text,
                    request.session.get('domain', ''),
                    request.session.get('profile', {}).get('role', ''),
                )

            answers = request.session.get('answers', {})
            answers[str(qn)] = {
                'text': answer_text,
                'skipped': skipped,
                'feedback': feedback_data.get('feedback', ''),
                'score': feedback_data.get('score'),
            }
            request.session['answers'] = answers

            session_id = request.session.get('session_id')
            if session_id:
                Answer.objects.update_or_create(
                    session_id=session_id, question_number=qn,
                    defaults={
                        'question_text': questions[qn - 1],
                        'answer_text': answer_text,
                        'skipped': skipped,
                        'ai_feedback': feedback_data.get('feedback', ''),
                        'ai_score': feedback_data.get('score'),
                    },
                )

            if qn >= total:
                if session_id:
                    InterviewSession.objects.filter(pk=session_id).update(
                        completed_at=timezone.now()
                    )
                request.session['question_number'] = 1
                return redirect('complete')

            request.session['question_number'] = qn + 1
            return redirect('interview')

    question = questions[qn - 1]
    pct = round((qn / total) * 100)
    prev_feedback = request.session.get('answers', {}).get(str(qn), {})

    return render(request, 'interview/interview.html', {
        'question': question,
        'question_number': qn,
        'total': total,
        'percent': pct,
        'domain': request.session.get('domain'),
        'profile': request.session.get('profile', {}),
        'prev_feedback': prev_feedback,
        'error': error,
    })


def complete_view(request):
    if not _is_logged_in(request):
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'restart':
            request.session['question_number'] = 1
            request.session['answers'] = {}
            request.session.pop('questions', None)
            return redirect('profile')
        return redirect('domain')

    answers = request.session.get('answers', {})
    questions = request.session.get('questions', [])
    answered_count = sum(1 for a in answers.values() if not a.get('skipped'))
    total_score = sum(a.get('score', 0) or 0 for a in answers.values())
    max_score = len(questions) * 10
    avg_score = round((total_score / max_score) * 10, 1) if max_score else None

    return render(request, 'interview/complete.html', {
        'domain': request.session.get('domain', ''),
        'profile': request.session.get('profile', {}),
        'answers': answers,
        'questions': questions,
        'total': len(questions),
        'answered_count': answered_count,
        'total_score': total_score,
        'max_score': max_score,
    })


@require_POST
def evaluate_api(request):
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    question = data.get('question', '')
    answer = data.get('answer', '')
    domain = request.session.get('domain', '')
    role = request.session.get('profile', {}).get('role', '')

    if not answer.strip():
        return JsonResponse({"error": "Empty answer"}, status=400)

    result = evaluate_answer(question, answer, domain, role)
    return JsonResponse(result)
