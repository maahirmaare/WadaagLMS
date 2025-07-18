from flask import current_app
from datetime import datetime
from time import time
from app import db, login_manager
from flask_login import UserMixin
import jwt

# gets the user from the db and logs them in/ties it with their session
@login_manager.user_loader
def load_user(user_id):
    return User_Account.query.get(int(user_id))

# time in readable format UTC
def time_readable():
    return datetime.fromtimestamp(time()).isoformat() + "Z"

# Association/Join Tables
class Conversation_User(db.Model):
    __tablename__ = 'conversation_user'
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), primary_key=True)
    read = db.Column(db.Boolean, default=False)
    conversation = db.relationship('Conversation', backref=db.backref('conversation_users'))

class Course_User(db.Model):
    # SQLAlchemy creates tablenames by default unless specified inside class
    __tablename__ = 'course_user'
    # Two primary keys come together to create a composite primary key
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), primary_key=True)
    points = db.Column(db.Integer, default=0)
    grade = db.Column(db.String(120))
    # saved as (Assignment, Points)
    assignments_done = db.Column(db.JSON, default="{}")
    course = db.relationship('Course', backref=db.backref('course_users', passive_deletes=True))

    def __repr__(self):
        return f"Course_User('{self.user_id}', '{self.course_id}', '{self.grade}')"

class User_Assignment(db.Model):
    __tablename__ = 'user_assignment'
    # user can turn assignment in more than once,
    # thus a unique primary key is needed rather than a composite primary key
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete='CASCADE'))
    # if student uploads assignment
    filename = db.Column(db.String(20))
    answers = db.Column(db.ARRAY(db.Text))
    points = db.Column(db.Integer)
    tries = db.Column(db.Integer, nullable=False)
    type = type = db.Column(db.String(120), nullable=False)
    # used incase student resubmits / latest is the one that is graded
    created_time = db.Column(db.Float, nullable=False, default=time)
    created_ctime = db.Column(db.DateTime, nullable=False, default=time_readable)
    assignment = db.relationship('Assignment', backref=db.backref('user_assignments', passive_deletes=True))

    def __repr__(self):
        return f"User_Assignment('{self.user_id}', '{self.assignment_id}', '{self.filename}', '{self.answers}', '{self.points}')"

# UserMixin adds classes used to represent users for login
# SECTION 1. User Schema
class User_Account(db.Model, UserMixin):
    __tablename__ = 'user_account'

    def get_token(self, expires_in=None):
        payload = {'user': self.id}
        if expires_in:
            payload['exp'] = time() + expires_in
        return jwt.encode(payload,
                        current_app.config["SECRET_KEY"],
                        algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        try:
            id = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=['HS256'])['user']
        except:
            return
        return User_Account.query.get(id)

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    profession = db.Column(db.String(10), nullable=False)
    biography = db.Column(db.Text)
    profile_image = db.Column(db.String(20), nullable=False, default='default.png')
    password = db.Column(db.String(60), nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    messages = db.relationship('Message', backref='user')
    conversations = db.relationship('Conversation_User', backref='user')
    courses = db.relationship('Course', backref='teacher')
    classes = db.relationship('Course_User')
    assignments = db.relationship('User_Assignment', backref='student')

    def __repr__(self):
        return f"User('{self.first_name} {self.last_name}', '{self.email}', '{self.profession}', '{self.profile_image}')"


# SECTION 2. Messaging Schema
class Conversation(db.Model):
    __tablename__ = 'conversation'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    messages = db.relationship('Message', backref='conversation')

    def __repr__(self):
        return f"Conversation('{self.id}', '{self.title}')"

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # Other type is "left"
    msg_type = db.Column(db.String(40), default="regular")
    created_time = db.Column(db.Float, nullable=False, default=time)
    created_ctime = db.Column(db.DateTime, nullable=False, default=time_readable)

    def __repr__(self):
        return f"Message('{self.id}', '{self.conversation_id}', '{self.user_id}', '{self.content}')"

    def rendering_dict(self):
        return {"id": f"{self.id}",
                "user_id": f"{self.user.id}",
                "name": f"{self.user.first_name} {self.user.last_name}",
                "profession": self.user.profession,
                "profile_img": self.user.profile_image,
                "message": self.content,
                "created_ctime": f'{self.created_ctime}',
                "timestamp": self.created_time,
                "type": self.msg_type}


# SECTION 3. Course Schema
class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    title = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(20), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    syllabus = db.Column(db.Text)
    code = db.Column(db.String(120))
    join = db.Column(db.Boolean, nullable=False, default=False)
    dropped = db.Column(db.ARRAY(db.Text), default=[])
    assignments = db.relationship('Assignment', backref='course', passive_deletes=True)
    lectures = db.relationship('Lecture', backref='course', passive_deletes=True)

    def __repr__(self):
        return f"Course('{self.id}', '{self.teacher_id}', '{self.title}', '{self.subject}', '{self.points}')"

class Assignment(db.Model):
    __tablename__ = 'assignment'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'))
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(120), nullable=False)
    tries = db.Column(db.Integer, nullable=False)
    created_time = db.Column(db.Float, nullable=False, default=time)
    created_ctime = db.Column(db.DateTime, nullable=False, default=time_readable)
    duedate_time = db.Column(db.Float)
    duedate_ctime = db.Column(db.DateTime)
    questions = db.relationship('Question', backref='assignment', passive_deletes=True)

    def __repr__(self):
        return f"Assignment(id: {self.id}, course_id: {self.course_id}, title:{self.title})"

class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id', ondelete='CASCADE'))
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(120), nullable=False)
    answer = db.Column(db.String(120))
    points = db.Column(db.Integer, nullable=False)
    options = db.relationship('Option', backref='question', passive_deletes=True)

    def __repr__(self):
        return f"Question('{self.id}', '{self.assignment_id}', '{self.title}')"

class Option(db.Model):
    __tablename__ = 'option'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id', ondelete='CASCADE'))
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Option('{self.id}', '{self.question_id}', '{self.content}')"


# SECTION 4. Lectures
class Lecture(db.Model):
    __tablename__ = 'lecture'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    url = db.Column(db.String(255))
    description = db.Column(db.Text)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    created_time = db.Column(db.DateTime)
    created_ctime = db.Column(db.DateTime)
    file = db.Column(db.String(255))  # <-- Make sure this exists

    def __repr__(self):
        return f"Lecture('{self.id}', '{self.course_id}', '{self.title}', '{self.description}', '{self.url}')"
