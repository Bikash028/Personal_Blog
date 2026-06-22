from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from models import db, User, Post
from forms import RegisterForm, LoginForm, PostForm

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

app = Flask(__name__)

app.config['SECRET_KEY'] = 'blog-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    posts = Post.query.order_by(
        Post.created_at.desc()
    ).all()

    return render_template(
        'index.html',
        posts=posts
    )


@app.route('/register', methods=['GET', 'POST'])
def register():

    form = RegisterForm()

    if form.validate_on_submit():

        existing_user = User.query.filter_by(
            email=form.email.data
        ).first()

        if existing_user:
            flash('Email already exists')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(
            form.password.data
        )

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash('Registration Successful')
        return redirect(url_for('login'))

    return render_template(
        'register.html',
        form=form
    )


@app.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(
            email=form.email.data
        ).first()

        if user and check_password_hash(
            user.password,
            form.password.data
        ):

            login_user(user)
            flash('Login Successful')

            return redirect(url_for('home'))

        flash('Invalid Credentials')

    return render_template(
        'login.html',
        form=form
    )


@app.route('/logout')
@login_required
def logout():

    logout_user()
    flash('Logged Out')

    return redirect(url_for('home'))


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():

    form = PostForm()

    if form.validate_on_submit():

        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id
        )

        db.session.add(post)
        db.session.commit()

        flash('Post Created')

        return redirect(url_for('home'))

    return render_template(
        'create_post.html',
        form=form
    )

@app.route('/post/<int:post_id>')
def view_post(post_id):

    post = Post.query.get_or_404(post_id)

    return render_template(
        'post.html',
        post=post
    )


@app.route('/edit/<int:post_id>',
methods=['GET', 'POST'])
@login_required
def edit_post(post_id):

    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for('home'))

    form = PostForm(obj=post)

    if form.validate_on_submit():

        post.title = form.title.data
        post.content = form.content.data

        db.session.commit()

        flash("Post Updated")

        return redirect(
            url_for('view_post',
            post_id=post.id)
        )

    return render_template(
        'edit_post.html',
        form=form
    )


@app.route('/delete/<int:post_id>')
@login_required
def delete_post(post_id):

    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for('home'))

    db.session.delete(post)
    db.session.commit()

    flash("Post Deleted")

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)