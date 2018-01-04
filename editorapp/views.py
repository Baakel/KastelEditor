from flask import render_template, url_for, flash, redirect, request, session, g
from editorapp import app, db, github
from .forms import StakeHoldersForm
from .models import Stakeholder, User, lm
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

    emailurl = "https://api.github.com/user?access_token=" + oauth_token
    r = requests.get(emailurl)
    nickname = r.json()['login']
    u_id = r.json()['id']
    if r.json()['email'] == 'null':
        contact = r.json()['url']
    else:
        contact = r.json()['email']
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        user = User(id=u_id, oaccess_token=oauth_token, nickname=nickname, contact=contact)
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
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