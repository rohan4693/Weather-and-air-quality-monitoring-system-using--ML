from flask import Flask, url_for, render_template, request, redirect, session, flash, jsonify

from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime,timedelta,timezone
from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField
from wtforms.validators import DataRequired, NumberRange
from forms import CarbonFootPrintForm,RegistrationForm,LoginForm
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import requests
import joblib  



app = Flask(__name__)
app.secret_key = 'your_secret_key_here' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy()
db.init_app(app)

MODEL_PATH = "carbon_footprint_model.pkl"
ENCODERS_PATH = "label_encoders.pkl"
SCALER_PATH = "scaler.pkl"

model  = joblib.load(MODEL_PATH)
label_encoders = joblib.load(ENCODERS_PATH)
scaler = joblib.load(SCALER_PATH)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, email, password, name, city, is_admin=False):
        self.email = email
        self.password = password
        self.name = name
        self.city = city
        self.is_admin = is_admin

def create_admin_user():
    admin_user = User.query.filter_by(email="admin27@gmail.com").first()
    if not admin_user:
        admin_user = User(
            name="admin", 
            email="admin27@gmail.com", 
            password="123", 
            city="trichy", 
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()


historical_data = pd.DataFrame(columns=['Date','Carbon Emission'])
 
class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    carbon_emission = db.Column(db.Float, nullable=False)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('leaderboard_entries', lazy=True))




@app.route('/form', methods=['GET', 'POST'])
def form():
    form = CarbonFootPrintForm()  
    if form.validate_on_submit(): 
        input_data = {
            'Body Type':form.body_type.data,
            'Sex':form.sex.data,
            'Diet':form.diet.data,
            'How Often Shower':form.shower.data,
            'Heating Energy Source':form.heating_energy_source.data,
            'Transport':form.transport.data,
            'Vehicle Type':form.vehicle_type.data,
            'Social Activity':form.social_activity.data,
            'Monthly Grocery Bill':form.grocery_bill.data,
            'Frequency of Traveling by Air':form.air_travel.data,
            'Vehicle Monthly Distance Km':form.vehicle_distance.data,
            'Waste Bag Size':form.waste_bag_size.data,
            'Waste Bag Weekly Count':form.waste_bag_count.data,
            'How Long TV PC Daily Hour':form.tv_pc_hours.data,
            'How Many New Clothes Monthly':form.new_clothes.data,
            'How Long Internet Daily Hour':form.internet_hours.data,
            'Energy efficiency':form.energy_efficiency.data,
        }
        df = pd.DataFrame([input_data])
        mappings={'How Often Shower':{'daily':5,'more frequently':15,'less frequently':2,'twice a day':10},
            'Social Activity':{'often':3,'sometimes':2,'rarely':1,'never':0},
            'Frequency of Traveling by Air':{'very frequently':4,'frequently':3,'rarely':2,'never':1},
            'Waste Bag Size':{'small':1,'medium':2,'large':3,'extra large':4},
            'Energy efficiency':{'No':0,'Sometimes':1,'Yes':2},
        }
        for column,mapping in mappings.items():
            if column in df.columns:
                df[column]=df[column].map(mapping)
        categorical_columns = ['Body Type','Sex','Diet','Transport','Vehicle Type','How Often Shower','Heating Energy Source']
        for col in categorical_columns:
            if col in label_encoders:
                df[col]=label_encoders[col].transform(df[col].astype(str))
        numerical_columns = ['Monthly Grocery Bill','Vehicle Monthly Distance Km','Waste Bag Weekly Count',
                         'How Long TV PC Daily Hour','How Many New Clothes Monthly','How Long Internet Daily Hour']
        df[numerical_columns]=scaler.transform(df[numerical_columns])
        prediction = model.predict(df)[0]
    
        global historical_data
        historical_data=pd.concat(
            [historical_data,pd.DataFrame({'Date':[pd.Timestamp.now()],'Carbon Emission':[prediction]})],
            ignore_index=True
        )
        return redirect(url_for('result',emission=prediction))
    return render_template('form.html', form=form) 

@app.route('/result', methods=['GET', 'POST'])
def result():
    emission = request.args.get('emission', None)
    if emission:  
        emission = float(emission)  
    else:
        emission = 0.0  
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            leaderboard_entry = Leaderboard(user_id=user.id, carbon_emission=emission)
            db.session.add(leaderboard_entry)
            db.session.commit()
        else:
            print(f"Error: User ID {session['user_id']} does not exist in the database.")
            flash("Error: User not found. Could not save emission.", "error")
    else:
        print("Error: No user ID in session.")
        flash("Error: You must be logged in to save your results.", "error")
    return render_template('result.html', emission=emission)


@app.route('/leaderboard')
def leaderboard():
    leaderboard_query = db.session.query(
        Leaderboard.user_id, db.func.avg(Leaderboard.carbon_emission).label('avg_emission')
    ).join(User, User.id == Leaderboard.user_id).group_by(Leaderboard.user_id).order_by(db.func.avg(Leaderboard.carbon_emission).asc()).all()
    leaderboard = []
    for idx, (user_id, avg_emission) in enumerate(leaderboard_query):
        user = User.query.get(user_id)
        if user:
            name = session.get('name', user.name if user.name else "Anonymous")
            city = session.get('city', user.city if user.city else "Unknown")
            leaderboard.append({
                "rank": idx + 1,
                "name": name,
                "city": city,
                "carbon_emission": round(avg_emission, 2),  
            })
    return render_template('leaderboard.html', leaderboard=leaderboard)


@app.route('/visualize')
def visualize():
    if 'user_id' not in session:
        flash("You need to be logged in to view your emission history.", "error")
        return redirect(url_for('login'))
    user_id = session['user_id']
    historical_data = Leaderboard.query.filter_by(user_id=user_id).order_by(Leaderboard.date_recorded).all()
    if not historical_data:
        return "No data available for Visualization!"
    data = {
        'Date': [entry.date_recorded for entry in historical_data], 
        'Carbon Emission': [entry.carbon_emission for entry in historical_data] 
    }
    df = pd.DataFrame(data)
    fig = px.line(df, x='Date', y='Carbon Emission', title='Carbon Emission Trends Over Time')
    fig_html = fig.to_html(full_html=False)
    return render_template('visualize.html', plot_html=fig_html)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index')
def welcome():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

    



@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        city = request.form['city']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "error")
            return redirect(url_for('register'))  
        
        new_user = User(email=email, password=password,name=name,city=city)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))  
        except Exception as e:
            flash("An error occurred during registration.", "error")
            return redirect(url_for('register'))  
    return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session['user_id'] = user.id
            session['logged_in'] = True  
            return redirect(url_for('dashboard')) 
        else:
            return render_template('login.html', message="Incorrect email or password.")
    
    return render_template('login.html')


@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    # Admin login logic
    if session.get('is_admin'):
        return redirect(url_for('dashboard'))  # If already logged in, go to dashboard

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Find user in the database by email
        user = User.query.filter_by(email=email).first()

        # Check if the user exists and if the password matches (without hashing)
        if user and user.password == password and user.is_admin:
            session['is_admin'] = True
            session['user_id'] = user.id  
            flash("Admin login successful!", "success")
            return redirect(url_for('dashboard'))  # Redirect to admin dashboard
        else:
            flash("Invalid login credentials or you're not an admin.", "error")
            return redirect(url_for('login_admin'))  # Redirect back to the login page

    return render_template('login_admin.html')




@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()  
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))  

openWeatherMapApiKey = "bffc5fc92fa543a0bf98ae2ca5021958"
aqiApikey = "132f67be1b7c0decb2f2135bafb77d0f692bec9a"
newsApiKey="pub_60937ae5db9716aa757954c39442745da32ba"


@app.route('/api/weather', methods=['GET'])
def api_weather():
    city = request.args.get('city', 'Bhimavaram')
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={openWeatherMapApiKey}&units=metric"
    weather_response = requests.get(weather_url)
    
    if weather_response.status_code != 200:
        return jsonify({'error': 'Could not fetch weather data'}), 500
    
    weather_data = weather_response.json()

    try:
        
        aqi_url = f"https://api.waqi.info/feed/{city}/?token={aqiApikey}"
        aqi_response = requests.get(aqi_url)
        aqi_json = aqi_response.json()

      
        print("AQI Response:", aqi_json)  

        if aqi_json.get('status') == "ok":
            aqi_data = aqi_json.get('data', {})
            aqi = aqi_data.get('aqi', 'N/A')

            if aqi != 'N/A':
                if aqi <= 50:
                    aqi_status = f"{aqi} (Good)"
                elif aqi <= 100:
                    aqi_status = f"{aqi} (Moderate)"
                elif aqi <= 150:
                    aqi_status = f"{aqi} (Unhealthy for Sensitive Groups)"
                elif aqi <= 200:
                    aqi_status = f"{aqi} (Unhealthy)"
                elif aqi <= 300:
                    aqi_status = f"{aqi} (Very Unhealthy)"
                else:
                    aqi_status = f"{aqi} (Hazardous)"
            else:
                aqi_status = "N/A"
        else:
            print(f"Error: {aqi_json.get('data', 'Unknown error')}")
            aqi_status = "N/A"

    except Exception as e:
        aqi_status = "N/A"
        print(f"Error fetching AQI: {e}")

    weather_data['aqi_status'] = aqi_status
    print("Final Weather Data:", weather_data)  

    return jsonify(weather_data)



@app.route('/api/news')
def get_news():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City is required"}), 400

 
    url = f"https://newsdata.io/api/1/latest?apikey=pub_60937ae5db9716aa757954c39442745da32ba&q={city}"

   
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch news"}), 500


    news_data = response.json()

    processed_results = []

    for article in news_data.get("results", []):
        processed_results.append({
            "title": article.get("title", "No Title"),
            "description": article.get("description", "No Description"),
            "link": article.get("link", "#"),
            "image_url": article.get("image_url", None)  # Add image_url here
        })
    return jsonify({"results": processed_results})




class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    author = db.relationship('User', backref=db.backref('posts', lazy=True))
    likes = db.relationship('Like', backref='post', lazy='dynamic')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('likes', lazy='dynamic'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref=db.backref('comments', lazy=True))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('comments', lazy=True))




@app.route('/community', methods=["GET", "POST"])
def community():
    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        user_id = session.get('user_id')
        new_post = Post(title=title, content=content, author_id=user_id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('community'))
    if 'is_admin' in session and session['is_admin']:
        posts = Post.query.all() 
    else:
        posts = Post.query.all()
    return render_template('community.html', posts=posts)


@app.route('/post/<int:post_id>', methods=["GET", "POST"])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    user_id = session.get('user_id') 
    if not user_id:
        return redirect(url_for('login'))
    if request.method == "POST":
        if 'like' in request.form:
            existing_like = Like.query.filter_by(post_id=post.id, user_id=user_id).first()
            if existing_like:
                db.session.delete(existing_like)
            else:
                new_like = Like(post_id=post.id, user_id=user_id)
                db.session.add(new_like)
            db.session.commit()
        else:
            content = request.form['content']
            new_comment = Comment(content=content, post_id=post_id, author_id=user_id)
            db.session.add(new_comment)
            db.session.commit()
    user_likes = Like.query.filter_by(post_id=post.id, user_id=user_id).all()
    likes_count = len(user_likes) 
    user_has_liked = len(user_likes) > 0 
    all_likes_count = post.likes.count() 

    return render_template('post.html', post=post, likes_count=all_likes_count, 
                           user_has_liked=user_has_liked)

@app.route('/admin/delete_post/<int:post_id>')
@app.route('/admin/delete_post/<int:post_id>')
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post:
        likes = Like.query.filter_by(post_id=post.id).all()
        for like in likes:
            db.session.delete(like)
        for comment in post.comments:
            db.session.delete(comment)

        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('community'))
    else:
        return redirect(url_for('error_page'))

@app.route('/admin/delete_comment/<int:comment_id>')
def delete_comment(comment_id):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('home'))  
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('post', post_id=comment.post_id))




@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
        create_admin_user() 
    app.run(debug=True,host='0.0.0.0',port=5000)                                                                                                                                    





    
 


