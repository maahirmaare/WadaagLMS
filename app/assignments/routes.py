from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from time import time
import json

from app import db
from app.models import Course, Assignment, User_Assignment, Question, Course_User, Option
from app.assignments.forms import AssignmentForm
from app.assignments.utils import assignment_error_handler, new_assignment_error_handler, save_assignment, delete_assignment
from app.students.utils import calculate_grade
from app.middleware import course_auth, teacher_auth

assignments_ = Blueprint("assignments", __name__)

@assignments_.route('/dashboard/courses/<int:course_id>/assignments', methods=['GET'])
@login_required
@course_auth
def assignments(course_id):
    profile_image = url_for('static', filename=f"profile_images/{current_user.profile_image}")
    course = Course.query.get_or_404(course_id)
    assignments = sorted(Assignment.query.filter_by(course_id=course_id).all(), key=lambda a: a.duedate_time)

    user_assignments = []
    for a in assignments:
        ua = User_Assignment.query.filter_by(user_id=current_user.id, assignment_id=a.id).all()
        user_assignments.append(sorted(ua, key=lambda x: x.created_time)[-1] if ua else 0)

    return render_template('assignments.html',
                           profile_image=profile_image,
                           course=course,
                           assignments=assignments,
                           user_assignments=user_assignments,
                           current_time=time(),
                           title=f"{course.title} - Assignments")

@assignments_.route('/dashboard/courses/<int:course_id>/assignments/new', methods=['GET', 'POST'])
@login_required
@course_auth
@teacher_auth
def new_assignment(course_id):
    profile_image = url_for('static', filename=f"profile_images/{current_user.profile_image}")
    course = Course.query.get_or_404(course_id)
    assignments = sorted(Assignment.query.filter_by(course_id=course_id).all(), key=lambda a: a.id)
    form = AssignmentForm()

    if request.method == 'POST':
        form_data = request.form.to_dict()
        if "ajax" in form_data:
            return new_assignment_error_handler(form, form_data)

        if len(assignments) >= 20:
            flash("Max number of assignments allowed is 20", "danger")
            return redirect(url_for("assignments.assignments", course_id=course.id))

        errors = new_assignment_error_handler(form, form_data)
        if errors:
            flash("There was an error in creating that assignment.", "danger")
            return redirect(url_for("assignments.new_assignment", course_id=course.id))

        questions, options, q_ids = {}, {}, []
        for key, value in form_data.items():
            if "question_option" in key:
                options[key] = value
            elif "question_" in key:
                questions[key] = value

        for key in questions:
            q_id = key.split("_")[2]
            if q_id not in q_ids:
                q_ids.append(q_id)

        question_option_ids = [(k.split("_")[2], k.split("_")[3]) for k in options]
        q_ids.sort()

        dt = datetime.strptime(form.date_input.data.strftime('%Y-%m-%d'), '%Y-%m-%d')
        duedate_time = datetime(dt.year, dt.month, dt.day, int(form.hour.data), int(form.minute.data)).timestamp()
        duedate_ctime = datetime.fromtimestamp(duedate_time).isoformat() + "Z"

        assignment = Assignment(course_id=course.id, title=form.title.data, content=form.content.data,
                                type=form.type.data, tries=form.tries.data, points=form.points.data,
                                duedate_time=duedate_time, duedate_ctime=duedate_ctime)
        db.session.add(assignment)
        db.session.commit()

        for i, q_id in enumerate(q_ids):
            question = Question(assignment_id=assignment.id,
                                title=questions.get(f"question_title_{q_id}"),
                                content=questions.get(f"question_content_{q_id}"),
                                answer=questions.get(f"question_answer_{q_id}"),
                                points=questions.get(f"question_points_{q_id}"),
                                type=questions.get(f"question_type_{q_id}"))
            db.session.add(question)
            db.session.commit()

            for qk, ok in question_option_ids:
                if qk == q_id:
                    option = Option(question_id=question.id,
                                    content=options.get(f"question_option_{qk}_{ok}"))
                    db.session.add(option)
                    db.session.commit()

        flash("Assignment was created successfully!", "success")
        return redirect(url_for("assignments.assignments", course_id=course.id))

    return render_template('new_assignment.html', profile_image=profile_image, course=course,
                           assignmentform=form, title=f"{course.title} - New Assignment")

@assignments_.route('/dashboard/courses/<int:course_id>/assignments/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
@course_auth
def assignment(course_id, assignment_id):
    profile_image = url_for('static', filename=f"profile_images/{current_user.profile_image}")
    file = request.files.get("file")
    form_data = request.form.to_dict()

    course = Course.query.get_or_404(course_id)
    assignment = Assignment.query.get_or_404(assignment_id)
    user_assignments = sorted(User_Assignment.query.filter_by(user_id=current_user.id, assignment_id=assignment.id).all(), key=lambda a: a.created_time)
    questions = sorted(Question.query.filter_by(assignment_id=assignment.id).all(), key=lambda q: q.id)
    options_dict = {str(q.id): q.options for q in questions}
    user_assignment = user_assignments[-1] if user_assignments else ''
    tries = user_assignment.tries if user_assignment else 0

    if request.method == 'POST':
        if "ajax" in form_data:
            return assignment_error_handler(form_data)

        if request.form.get("upload") and assignment.type == "Instructions":
            if tries < assignment.tries:
                course_user = Course_User.query.filter_by(user_id=current_user.id, course_id=course.id).first()
                filename = save_assignment(file)
                if filename:
                    for ua in user_assignments:
                        delete_assignment(ua.filename)
                        db.session.delete(ua)
                    user_assignment = User_Assignment(user_id=current_user.id, assignment_id=assignment.id,
                                                     filename=filename, tries=tries+1, points=0,
                                                     type=assignment.type)
                    db.session.add(user_assignment)
                    db.session.commit()
                    calculate_grade(course_user, assignment, 0)
                    flash("Assignment has been successfully submitted.", "success")
                else:
                    flash("That file type is not allowed or file uploading has been disabled.", "warning")
            else:
                flash("You have already reached your max tries.", "warning")
            return redirect(url_for('assignments.assignment', course_id=course.id, assignment_id=assignment.id))

        if request.form.get("delete") and current_user.id == course.teacher_id:
            course_users = Course_User.query.filter_by(course_id=course.id).all()
            for user in course_users:
                ua = User_Assignment.query.filter_by(user_id=user.user_id, assignment_id=assignment.id).all()
                if ua:
                    ua_sorted = sorted(ua, key=lambda a: a.created_time)
                    last_ua = ua_sorted[-1]
                    ad = json.loads(user.assignments_done)
                    ad.pop(str(assignment.id), None)
                    user.assignments_done = json.dumps(ad)
                    user.points -= last_ua.points
                    total_points = sum(a.points for a in Assignment.query.filter_by(course_id=course.id).all() if a.id != assignment.id)
                    user.grade = '{:.2%}'.format(user.points / total_points if total_points else 0)
            db.session.delete(assignment)
            db.session.commit()
            flash("Assignment was deleted successfully!", "success")
            return redirect(url_for("assignments.assignments", course_id=course.id))

        if current_user.profession == "Student" and tries < assignment.tries:
            errors = assignment_error_handler(form_data)
            if errors:
                flash("There was an error in submitting this assignment.", "danger")
                return redirect(url_for("assignments.assignment", course_id=course.id, assignment_id=assignment.id))

            course_user = Course_User.query.filter_by(user_id=current_user.id, course_id=course.id).first()
            answers = [v for k, v in form_data.items() if "question_" in k]
            points = sum(q.points for i, q in enumerate(questions) if q.answer == answers[i])
            calculate_grade(course_user, assignment, points)

            user_assignment = User_Assignment(user_id=current_user.id, assignment_id=assignment.id, filename="",
                                             answers=answers, points=points, tries=tries + 1, type=assignment.type)
            db.session.add(user_assignment)
            db.session.commit()
            flash("Assignment turned in!", "success")
            return redirect(url_for("assignments.assignment", course_id=course.id, assignment_id=assignment.id))

        flash("You can no longer redo this assignment.", "danger")
        return redirect(url_for("assignments.assignment", course_id=course.id, assignment_id=assignment.id))

    return render_template('assignment.html', profile_image=profile_image, course=course, assignment=assignment,
                           current_time=time(), user_assignment=user_assignment, questions=questions,
                           options_dict=options_dict, redo=request.args.get("redo"), tries=tries,
                           title=f"{course.title} - {assignment.title}")
