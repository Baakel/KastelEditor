from flask import render_template, url_for, flash, redirect, request, session
from editorapp import app, db
from .forms import StakeHoldersForm
from .models import Stakeholder, User, lm, OAuthSignIn
from flask_login import current_user, login_user

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

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    # if not current_user.is_anonymous():
    #     return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed')
        return redirect(url_for('index'))
    user = User.quey.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))