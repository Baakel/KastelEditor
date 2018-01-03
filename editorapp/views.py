from flask import render_template, url_for, flash, redirect, request, session, g
from editorapp import app, db, github
from .forms import StakeHoldersForm
from .models import Stakeholder, User, lm #  OAuthSignIn
# from flask_login import current_user, login_user
from flask_github import GitHub
import requests

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])

@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'John'}
    projects = [
        {'author': {'nicknames': ['John','Diego']},
         'description': 'first test project'},
        {'author': {'nicknames': 'David'},
         'description': 'second test project'}
    ]
    return render_template('index.html',
                           title='Home',
                           user=user,
                           projects=projects)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    form = StakeHoldersForm()
    if form.validate_on_submit():
        stakeholder = Stakeholder(nickname=form.stakeholder.data)
        db.session.add(stakeholder)
        db.session.commit()
        flash('Stakeholder Added to the Database')
        return redirect(url_for('edit'))
    stakeholders = Stakeholder.query.all()
    return render_template('editor.html',
                           title='Project',
                           form=form,
                           stakeholders=stakeholders)

# @app.route('/authorize/<provider>')
# def oauth_authorize(provider):
#     # if not current_user.is_anonymous():
#     #     return redirect(url_for('index'))
#     oauth = OAuthSignIn.get_provider(provider)
#     return oauth.authorize()

# @app.route('/callback/<provider>')
# def oauth_callback(provider):
#     if not current_user.is_anonymous():
#         return redirect(url_for('index'))
#     oauth = OAuthSignIn.get_provider(provider)
#     social_id, username, email = oauth.callback()
#     if social_id is None:
#         flash('Authentication failed')
#         return redirect(url_for('index'))
#     user = User.quey.filter_by(social_id=social_id).first()
#     if not user:
#         user = User(social_id=social_id, nickname=username, email=email)
#         db.session.add(user)
#         db.session.commit()
#     login_user(user, True)
#     return redirect(url_for('index'))

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login')
def login():
    return github.authorize()

@app.route('/github-callback')
@github.authorized_handler
def authorized(oauth_token):
    next_url = request.args.get('next') or url_for('index')
    if oauth_token is None:
        flash('Authorization failed.')
        return redirect(next_url)

    user = User.query.filter_by(oaccess_token=oauth_token).first()
    if user is None:
        emailurl = "https://api.github.com/user?access_token=" + oauth_token
        print(emailurl)
        r = requests.get(emailurl)
        print(r.text)
        st_pos = r.text.find('email":"') + len('email":"')
        print(st_pos)
        end_pos = r.text[st_pos:].find(',') + st_pos - 1
        print(end_pos)
        email = r.text[st_pos:end_pos].split('"')
        print(email)
        # user = User(social_id=oauth_token, nickname='test 2', email='test@example.com')
        # db.session.add(user)
        # db.session.commit()

    # session['user_id'] = user.id
    return redirect(next_url)


@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))