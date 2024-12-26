from flask_wtf import FlaskForm
from wtforms import StringField,SelectField,FloatField,SubmitField,IntegerField
from wtforms.validators import DataRequired
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import DataRequired,Email,EqualTo,Length


class CarbonFootPrintForm(FlaskForm):
    body_type = SelectField('Body Type', choices=[
        ('underweight', 'Underweight'),
        ('obese', 'Obese'),
        ('normal', 'Normal')
    ], validators=[DataRequired()])
    
    # Sex selection
    sex = SelectField('Sex', choices=[
        ('female', 'Female'),
        ('male', 'Male')
    ], validators=[DataRequired()])
    
    # Diet selection
    diet = SelectField('Diet', choices=[
        ('pescatarian', 'Pescatarian'),
        ('vegan', 'Vegan'),
        ('omnivore', 'Omnivore'),
        ('vegetarian', 'Vegetarian')
    ], validators=[DataRequired()])
    
    # Shower frequency selection
    shower = SelectField('How Often Shower (days)', choices=[
        ('daily', 'Daily'),
        ('twice a day', 'Twice a day'),
        ('less frequently', 'Less frequently'),
        ('more frequently', 'More frequently')
    ], validators=[DataRequired()])
    
    # Heating energy source selection
    heating_energy_source = SelectField('Heating Energy Source', choices=[
        ('electricity', 'Electricity'),
        ('coal', 'Coal'),
        ('wood', 'Wood'),
        ('natural gas', 'Natural gas')
    ], validators=[DataRequired()])
    
    # Transport selection
    transport = SelectField('Transport', choices=[
        ('walk/bicycle', 'Walk/Bicycle'),
        ('public', 'Public'),
        ('private', 'Private')
    ], validators=[DataRequired()])
    
    # Vehicle type input (string field because it's free text)
    vehicle_type = SelectField('Vehicle Type', choices=[
        ('lpg', 'LPG'),
        ('electric', 'Electric'),
        ('petrol', 'Petrol'),
        ('hybrid', 'Hybrid'),
        ('diesel', 'Diesel')
    ],validators=[DataRequired()])
    
    # Social activity selection
    social_activity = SelectField(
        'Social Activity',
        choices=[('often', 'Often'), ('sometimes', 'Sometimes'), ('rarely', 'Rarely'), ('never', 'Never')],
        validators=[DataRequired()]
    )
    
    # Monthly grocery bill input
    grocery_bill = FloatField('Monthly Grocery Bill', validators=[DataRequired()])
    
    # Frequency of traveling by air selection
    air_travel = SelectField(
        'Frequency of Traveling by Air',
        choices=[('very frequently', 'Very Frequently'), ('frequently', 'Frequently'), ('rarely', 'Rarely'), ('never', 'Never')],
        validators=[DataRequired()]
    )
    
    # Monthly vehicle distance input
    vehicle_distance = FloatField('Vehicle Monthly Distance (KM)', validators=[DataRequired()])
    
    # Waste bag size selection
    waste_bag_size = SelectField(
        'Waste Bag Size',
        choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large'), ('extra large', 'Extra Large')],
        validators=[DataRequired()]
    )
    
    # Weekly waste bag count input
    waste_bag_count = FloatField('Waste Bag Weekly Count', validators=[DataRequired()])
    
    # TV/PC daily hours input
    tv_pc_hours = FloatField('How Long TV/PC Daily (hours)', validators=[DataRequired()])
    
    # Monthly new clothes count input
    new_clothes = FloatField('How Many New Clothes Monthly', validators=[DataRequired()])
    
    # Internet daily hours input
    internet_hours = FloatField('How Long Internet Daily (hours)', validators=[DataRequired()])
    
    # Energy efficiency selection
    energy_efficiency = SelectField(
        'Energy Efficiency',
        choices=[('No', 'No'), ('Sometimes', 'Sometimes'), ('Yes', 'Yes')],
        validators=[DataRequired()]
    )
    
    # Submit button
    submit = SubmitField('Predict')
