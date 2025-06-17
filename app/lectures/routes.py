from flask import (
    Blueprint, request, render_template, redirect,
    url_for, flash, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from datetime import datetime
from app.lectures.forms import NewLectureForm
from app.filters import autoversion
from app.middleware import course_auth, teacher_auth
from app.models import Course, Lecture
from app import db

lectures_ = Blueprint("lectures", __name__)

UPLOAD_FOLDER = os.path.join('app', 'static', 'lectures')

# ✅ View All Lectures
@lectures_.route('/dashboard/courses/<int:course_id>/lectures', methods=['GET', 'POST'])
@login_required
@course_auth
def lectures(course_id):
    profile_image = url_for('static', filename="profile_images/" + current_user.profile_image)
    course = Course.query.get(course_id)
    lectures = Lecture.query.filter_by(course_id=course_id).order_by(Lecture.created_time).all()

    return render_template("lectures.html",
                           profile_image=profile_image,
                           course=course,
                           lectures=lectures,
                           title=f"{course.title} - Lectures")


# ✅ Create New Lecture (with file upload)
@lectures_.route('/dashboard/courses/<int:course_id>/lectures/new', methods=['GET', 'POST'])
@login_required
@course_auth
@teacher_auth
def new_lecture(course_id):
    profile_image = url_for('static', filename="profile_images/" + current_user.profile_image)
    course = Course.query.get(course_id)
    form = NewLectureForm()

    if form.validate_on_submit():
        # YouTube embed fix
        url = form.url.data.strip()
        if "watch?v=" in url:
            video_id = url.split("watch?v=")[-1].split("&")[0]
            url = f"https://www.youtube.com/embed/{video_id}"
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[-1].split("?")[0]
            url = f"https://www.youtube.com/embed/{video_id}"
        elif "embed/" in url:
            # already in correct format
            pass
        else:
            flash("Please enter a valid YouTube URL.", "danger")
            return redirect(request.url)
        # Handle file upload
        filename = None
        if form.lecture_file.data:
            uploaded_file = form.lecture_file.data
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(file_path)

        # Save lecture to DB
        lecture = Lecture(
            course_id=course.id,
            title=form.title.data,
            url=url,
            description=form.description.data,
            file=filename,
            created_time=datetime.utcnow(),
            created_ctime=datetime.utcnow()
        )
        db.session.add(lecture)
        db.session.commit()

        flash("Lecture uploaded successfully.", "success")
        return redirect(url_for("lectures.lectures", course_id=course.id))

    return render_template("new_lecture.html",
                           profile_image=profile_image,
                           course=course,
                           form=form,
                           title=f"{course.title} - New Lecture",
                           header="\\ New Lecture")


# ✅ View Single Lecture + Delete
@lectures_.route('/dashboard/courses/<int:course_id>/lectures/<int:lecture_id>', methods=['GET', 'POST'])
@login_required
@course_auth
def lecture(course_id, lecture_id):
    profile_image = url_for('static', filename="profile_images/" + current_user.profile_image)
    course = Course.query.get(course_id)
    lecture = Lecture.query.get(lecture_id)
    is_teacher = (course.teacher_id == current_user.id)

    if request.method == 'POST' and is_teacher:
        # Delete file if exists
        if lecture.file:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, lecture.file))
            except:
                pass
        db.session.delete(lecture)
        db.session.commit()
        flash("Lecture deleted.", "success")
        return redirect(url_for("lectures.lectures", course_id=course.id))

    return render_template("lecture.html",
                           profile_image=profile_image,
                           course=course,
                           lecture=lecture,
                           title=f"{course.title} - Lecture",
                           header="\\ " + lecture.title)


# ✅ Download Lecture File
@lectures_.route('/lectures/download/<filename>')
@login_required
def download_lecture_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)