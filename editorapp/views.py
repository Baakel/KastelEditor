from flask import render_template, url_for, flash, redirect, request, session, g
from editorapp import app, db, github
from flask_login import login_required
from .forms import StakeHoldersForm
from .models import Stakeholder, Users, lm, Projects
import requests

@app.errorhandler(401)
def unauthorized_error(error):
    flash('Please log in first.')
    return redirect(url_for('index'))

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = Users.query.get(session['user_id'])

@app.route('/')
@app.route('/index')
def index():
    cprojects = Projects.query().all()
    return render_template('index.html',
                           title='Home',
                           projects=cprojects)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
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

@app.route('/projects/<name>', methods=['GET', 'POST'])
@login_required
def projects(name):
    project = Projects.query.filter_by(name=name).first()
    if project == None:
        return render_template('projects.html',
                               title=name,
                               project=None,
                               user=g.user)
    else:
        return render_template('projects.html',
                           title=project.name,
                           project=project.id,
                                user=g.user)

@lm.user_loader
def load_user(id):
    return Users.query.get(int(id))

@app.route('/login')
def login():
    return github.authorize(scope='user:email')

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
    if r.json()['email'] == None:
        emailurl = "https://api.github.com/user/emails?access_token=" + oauth_token
        r = requests.get(emailurl)
        v = 0
        for i in r.json():
            if r.json()[v]['primary'] == True:
                contact = r.json()[v]['email']
            else:
                v += 1
    else:
        contact = r.json()['email']
    user = Users.query.filter_by(nickname=nickname).first()
    if user is None:
        user = Users(id=u_id, oaccess_token=oauth_token, nickname=nickname, contact=contact)
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