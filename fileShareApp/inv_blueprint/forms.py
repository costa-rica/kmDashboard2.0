from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed #used for image uploading
from wtforms import StringField, PasswordField, SubmitField, BooleanField, \
    TextAreaField, FloatField#DateTimeField, DateField, TimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField


# class EmployeeForm(FlaskForm):
    # name = StringField('Employee Name',validators=[DataRequired()])
    # submit = SubmitField('Add Employee')



# class AddRestaurantForm(FlaskForm):
    # name = StringField('Employee Name',validators=[DataRequired()])
    # submit = SubmitField('Add Restaurant')


class DatabaseForm(FlaskForm):
    excelFile = FileField('excelFile', validators = [FileAllowed(['xlsx'])])
    uploadExcel = SubmitField('Upload Excel File')

#not used:
# class AddRoleForm(FlaskForm):
    # role = StringField('Role')
    # wage = FloatField('Wage')
    # tipPercentage = FloatField('Tip Percentage')
    # notes = TextAreaField('notes')