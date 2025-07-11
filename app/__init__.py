from dotenv import load_dotenv
load_dotenv()  # 🔥 This will load .env before anything else

from flask_migrate import Migrate
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from app.config import Config
import os

app = Flask(__name__)
# toolbar = DebugToolbarExtension()
limiter = Limiter(key_func=get_remote_address,
                default_limits=['1000 per day', '200 per hour'])
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
moment = Moment()

login_manager = LoginManager()
login_manager.login_message = ""
login_manager.login_message_category = "warning"
login_manager.login_view = 'home.login'

mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config['MAX_CONTENT_LENGTH'] = 400000000

    limiter.init_app(app)
    app.app_context().push()
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from app.home.routes import home_
    from app.assignments.routes import assignments_
    from app.courses.routes import courses_
    from app.deadlines.routes import deadlines_
    from app.errors.routes import errors
    from app.inbox.routes import inbox_
    from app.lectures.routes import lectures_
    from app.profile.routes import profile_
    from app.students.routes import students_
    from app.users.routes import users

    app.register_blueprint(home_)
    app.register_blueprint(assignments_)
    app.register_blueprint(courses_)
    app.register_blueprint(deadlines_)
    app.register_blueprint(errors)
    app.register_blueprint(inbox_)
    app.register_blueprint(lectures_)
    app.register_blueprint(profile_)
    app.register_blueprint(students_)
    app.register_blueprint(users)

    return app
