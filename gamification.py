from flask import Flask, render_template, flash, request, redirect, url_for
from datetime import datetime 
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exists, select
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from webforms import UserForm, LoginForm,  SearchForm, NamerForm, PasswordForm,NewPostForm,NewCommentForm
from flask_ckeditor import CKEditor
from models import db,User,Course,Enrollment,QuizSet,QuizQuestion,QuizSubmission,Post,Comment

#export FLASK_ENV=development
#export FLASK_APP=gamification.py


#create a Flask instance
app = Flask(__name__)
#Add CKEditor
ckeditor = CKEditor(app)
#Old SQLite Database
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
#New MySQL DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/gamification'

#Secret Key
app.config['SECRET_KEY'] = "@45665Fdsdss456kl"
#Initialize the Database
db.init_app(app)
migrate=Migrate(app,db)
app.app_context().push()

# Flask Login configurations
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view= 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Pass stuff to Navbar
@app.context_processor
def base():
    form=SearchForm()
    return dict(form=form)

# Create a route decorator
@app.route('/')
def index():
    return render_template('index.html')  

@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            #Hash the Password!!
            hashed_pw = generate_password_hash(form.password_hash.data, "pbkdf2:sha256")
            user = User(first_name=form.first_name.data, last_name=form.last_name.data, username=form.username.data, email=form.email.data, role= 'student', password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.username.data                               #change: name to username and also in the template
        form.first_name.data = ''
        form.last_name.data = ''
        form.username.data = ''
        form.email.data = ''
        form.password_hash.data=''
        flash("Registration has been completed successfully. Please log in!")
        return redirect(url_for('login'))

    our_users = User.query.order_by(User.date_added)
    return render_template('add_user.html', 
                           form=form,
                           name=name,
                           our_users=our_users)         #change: need to redirect to the login page                


#Update Database Record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form=UserForm()
    user_to_update=User.query.get_or_404(id)
    if request.method == 'POST':
        user_to_update.first_name =  request.form['first_name']
        user_to_update.last_name =  request.form['last_name']
        user_to_update.username =  request.form['username']
        user_to_update.email =  request.form['email']
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("update.html", 
                                    form=form,
                                    user_to_update=user_to_update)

        except:
            flash("Looks like there was a problem....try again!")
            return render_template("update.html", 
                                    form=form,
                                    user_to_update=user_to_update)
    else:
        return render_template("update.html", 
                                    form=form,
                                    user_to_update=user_to_update)

#Delete Database Record
@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    name = None
    form = UserForm()
    user_to_delete=User.query.get_or_404(id)
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User Deleted Successfully!")

        our_users = User.query.order_by(User.date_added)
        return render_template('add_user.html', 
                                form=form,
                                name=name,
                                our_users=our_users) 
    except:
        flash("Whoops! There was a problem deleting user, try again.... ")
        return render_template('add_user.html', 
                                form=form,
                                name=name,
                                our_users=our_users)


#Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            # Check the hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Successful!")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong Password - Try Again!")
        else:
            flash("That User Doesn't Exist! Try Again")


    return render_template('login.html', form=form)

#Create Logout Page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out! Thanks")
    return redirect(url_for('login'))


#Create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form=UserForm()
    id = current_user.id
    enrolled_courses = get_enrolled_courses(id)
    user_to_update=User.query.get_or_404(id)
    total_score = QuizSubmission.query.filter_by(user_id=id, is_correct_answer=True).count()
    marks_level = [50, 100, 200, 500, 1000]
    next_target = next_higher_number(total_score, marks_level)


    if request.method == 'POST':
        user_to_update.first_name =  request.form['first_name']
        user_to_update.last_name =  request.form['last_name']
        user_to_update.username =  request.form['username']
        user_to_update.email =  request.form['email']
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("dashboard.html", 
                                    form=form,
                                    user_to_update=user_to_update,
                                    total_score=total_score,
                                    next_target = next_target,
                                    enrolled_courses=enrolled_courses)

        except:
            flash("Looks like there was a problem....try again!")
            return render_template("dashboard.html", 
                                    form=form,
                                    user_to_update=user_to_update,
                                    total_score=total_score,
                                    next_target=next_target)
    else:
        return render_template("dashboard.html", 
                                    form=form,
                                    user_to_update=user_to_update,
                                    total_score=total_score,
                                    next_target=next_target,
                                    enrolled_courses=enrolled_courses)

    return render_template('dashboard.html')


#Create custome error pages
#Invalid URL 
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

#Internal Server Error 
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

# Quiz Page
@login_required
@app.route('/quiz')
def quiz():
    #id=current_user.id
    enrolled_courses = current_user.courses

    return render_template('quiz.html', 
                            enrolled_courses=enrolled_courses )


# Forum Selection Page
@login_required
@app.route('/forum' , methods=['GET', 'POST'])
def forum_list():
    id=current_user.id
    enrolled_courses = get_courses_to_enroll(id)

    return render_template('forum_list.html', 
                            enrolled_courses=enrolled_courses )

# Selected Forum Page
@login_required
@app.route('/forum/<int:id>', methods=['GET', 'POST'])
def forum_page(id):
    post_form = NewPostForm()
    comment_form = NewCommentForm()
    posts = Post.query.filter_by(discussion_forum_id=id).all()
    comments = Comment.query.join(Post).filter(Post.discussion_forum_id == id).all()

    if post_form.validate_on_submit() and post_form.submit.data:
        post = Post(
            discussion_forum_id=id,
            user_id=current_user.id,
            posted_date=datetime.now(),
            content = post_form.question.data
        )

        db.session.add(post)
        db.session.commit()

        return redirect(url_for('forum_page', id=id))

    if comment_form.validate_on_submit() and comment_form.submit.data:
        comment = Comment(
            post_id=request.form.get('post_id'),
            user_id=current_user.id,
            commented_date=datetime.now(),
            content = comment_form.comment.data
        )

        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('forum_page', id=id))

    return render_template('forum.html', posts = posts, comments =comments, id=id, post_form = post_form, comment_form = comment_form)

@app.route('/enrol/<int:id>', methods=['GET', 'POST'])
@login_required
def enroll(id):
    if request.method == 'POST':
        user_id = current_user.id 
        course_id = request.form.get('course_id')

        course = Course.query.get(course_id)
        

        if current_user and course:
            enrollment = Enrollment(
                user_id=user_id,
                course_id=course_id,
                enrollmentDate=datetime.now(),
            )

            db.session.add(enrollment)
            db.session.commit()

            return redirect(url_for('dashboard'))

        else:
            return "Student or COurse not found"
    courses = Course.query.all()
    enrolled_courses = get_courses_to_enroll(id)
    return render_template('enrolment.html', 
                            courses=courses , enrolled_courses=enrolled_courses)

# Quiz Selection Page
@login_required
@app.route('/quiz-selection/<int:course_id>')
def quiz_selection(course_id):
    #quiz_sets = QuizSet.query.filter_by(course_id=course_id)
    #results = QuizSet.query.filter_by(course_id=course_id).with_entities(QuizSet.id, QuizSet.name, QuizSet.attribute1).add_columns("value_for_attribute2").all()

    from sqlalchemy import exists



    # Define a subquery to check if the quiz_set_id exists in the quiz_submission table
    subquery = exists().where((QuizSubmission.quiz_set_id == QuizSet.id) &(QuizSubmission.user_id == current_user.id))

    # Filter QuizSet records by course_id and add a new attribute indicating if the quiz_set_id exists in the quiz_submission table
    quiz_sets = (
        QuizSet.query
        .filter_by(course_id=course_id)
        .add_columns(subquery.label('is_quiz_taken'))
        .all()
    )
    

    return render_template('quiz_selection.html', 
                            quiz_sets=quiz_sets
                            )   

# Quiz Questions
@login_required  
@app.route('/quiz-exam/<int:quiz_set_id>', methods=['GET', 'POST'])                    
def quiz_exam(quiz_set_id):
    quiz_questions=QuizQuestion.query.filter_by(quiz_set_id=quiz_set_id)
    quiz_question_count = quiz_questions.count()
    quiz_set = QuizSet.query.get_or_404(quiz_set_id);
    current_user_id = current_user.id
    total_correct_answer =  QuizSubmission.query.filter_by(user_id=current_user_id, quiz_set_id=quiz_set_id, is_correct_answer=True).count()
    if request.method == 'POST':
        for quiz_question in quiz_questions:
            given_answer = given_answer = int(request.form[f'question-{quiz_question.id}']) if request.form.get(f'question-{quiz_question.id}') is not None else 0
            if given_answer ==  quiz_question.correct_answer:
                is_correct_answer = True
                total_correct_answer=total_correct_answer+1
            else:
                is_correct_answer = False
            quiz_submission = QuizSubmission(user_id=current_user_id, quiz_set_id=quiz_set_id, quiz_question_id=quiz_question.id,given_answer=given_answer, is_correct_answer=is_correct_answer)
            db.session.add(quiz_submission)
        try:   
            db.session.commit()
            flash("Yor Quiz Exam is Over! Thank You.") 
            return render_template('quiz_exam.html',
                            quiz_set_id=quiz_set_id,
                            quiz_set=quiz_set,
                            quiz_questions=quiz_questions,
                            quiz_question_count = quiz_question_count,
                            total_correct_answer=total_correct_answer)
        except:
            flash("Looks like there was a problem submitting your exam....try again!") 
            return render_template('quiz_exam.html',
                            quiz_set_id=quiz_set_id,
                            quiz_set=quiz_set,
                            quiz_questions=quiz_questions,
                            quiz_question_count = quiz_question_count,
                            total_correct_answer=total_correct_answer)

    return render_template('quiz_exam.html',
                            quiz_set_id=quiz_set_id,
                            quiz_set=quiz_set,
                            quiz_questions=quiz_questions,
                            quiz_question_count = quiz_question_count,
                            total_correct_answer=total_correct_answer)




# Create Admin
@app.route('/admin')
@login_required
def admin():
    current_user_email = current_user.email
    if current_user_email == 'admin@gmail.com':
        our_users = User.query.order_by(User.date_added)
        return render_template('admin.html',
                               our_users=our_users)  
    else:
        flash("Sorry you must be the Admin to access the admin page...")
        return redirect(url_for('dashboard'))
    

def next_higher_number(number, marks_level):
    for mark in marks_level:
        if mark > number:
            return mark
    return 0    



def get_enrolled_courses(user_id):
    user = User.query.get(user_id)
    if user:
        return [enrollment.course.name for enrollment in user.enrolments]
    else:
        return []
    
def get_courses_to_enroll(user_id):
    user = User.query.get(user_id)
    courses = Course.query.all()
    enrolled_courses = [enrollment.course for enrollment in user.enrolments]
    if user:
        return enrolled_courses 
    else:
        return []

if __name__ == '__main__':
    app.run(debug=True)



