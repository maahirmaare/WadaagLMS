from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SubmitField)
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed

class NewLectureForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    url = StringField('Video Url', validators=[DataRequired()])
    description = TextAreaField('Video Url', validators=[DataRequired()])
    lecture_file = FileField('Upload Lecture File (PDF/DOCX)', 
                            validators=[FileAllowed(['pdf', 'docx', 'doc', 'pptx'], 
                            'Only PDF, DOCX, DOC, and PPTX files allowed!')])
    submit = SubmitField('Submit')