from flask import render_template, url_for, flash, redirect, request, session, g
from editorapp import app, db, github
from flask_login import login_required
from .forms import StakeHoldersForm, ProjectForm, GoodsForm, SoftGoalsForm, EditorForm, AccessForm
from .models import Stakeholder, Users, lm, Projects, Good, SoftGoal
import requests


@app.errorhandler(401)
def unauthorized_error(error):
    flash('Please log in first.')
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = Users.query.get(session['user_id'])


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',
                           title='Home')


@app.route('/stakeholders/<project>', methods=['GET', 'POST'])
@login_required
def stakeholders(project):
    project = Projects.query.filter_by(name=project).first()
    form = StakeHoldersForm()
    if form.validate_on_submit():
        stkhld = Stakeholder.query.filter_by(nickname=form.stakeholder.data, project_id=project.id).first()
        if stkhld is None:
            stakeholder = Stakeholder(nickname=form.stakeholder.data, project_id=project.id)
            db.session.add(stakeholder)
            db.session.commit()
            flash('Stakeholder Added to the Database', 'succ')
            return redirect(url_for('stakeholders', project=project.name))
        else:
            flash('Stakeholder already exists', 'error')
    stakeholders = Stakeholder.query.filter_by(project_id=project.id).all()
    return render_template('editor.html',
                           title=project.name,
                           form=form,
                           stakeholders=stakeholders,
                           project=project)


@app.route('/removesh/<project>/<desc>', methods=['GET', 'POST'])
@login_required
def removesh(project, desc):
    cproj = Projects.query.filter_by(name=project).first()
    Stakeholder.query.filter_by(nickname=desc, project_id=cproj.id).delete()
    db.session.commit()
    flash('Stakeholder removed', 'error')
    return redirect(url_for('stakeholders', project=project))


@app.route('/projects/<name>', methods=['GET', 'POST'])
@login_required
def projects(name):
    project = Projects.query.filter_by(name=name).first()
    form = ProjectForm()
    form2 = EditorForm()
    form3 = AccessForm()
    if form.validate_on_submit():
        projn = Projects.make_unique_name(form.project.data)
        projname = Projects(name=projn, creator=g.user.id)
        db.session.add(projname)
        db.session.commit()
        db.session.add(g.user.contribute(projname))
        db.session.commit()
        if form.law.data is True:
            projid = Projects.query.filter_by(name=projname.name).first()
            law = Stakeholder(nickname='Law', project_id=projid.id)
            db.session.add(law)
            db.session.commit()
        flash('Project created.', 'succ')
        return redirect(url_for('projects', name=projname.name))
    if form2.validate_on_submit():
        editor = Users.query.filter_by(nickname=form2.editor.data).first()
        if editor is None:
            flash('User does not exist', 'error')
            return redirect(url_for('projects', name=project.name))
        elif editor == g.user:
            flash('Can\'t add yourself as an editor', 'error')
            return redirect(url_for('projects', name=project.name))
        else:
            u = editor.contribute(project)
            db.session.add(u)
            db.session.commit()
            flash('User added as editor for ' + project.name, 'succ')
            return redirect(url_for('projects', name=project.name))
    if form3.validate_on_submit():
        editor = Users.query.filter_by(nickname=form3.revoke.data).first()
        if editor is None:
            flash('User does not exist', 'error')
            return redirect(url_for('projects', name=project.name))
        elif editor == g.user:
            flash('Can\'t revoke access to yourself', 'error')
            return redirect(url_for('projects', name=project.name))
        elif editor.id == project.creator:
            flash('Can\'t revoke access to the project creator', 'error')
        else:
            u = editor.revoke_access(project)
            db.session.add(u)
            db.session.commit()
            flash('Access revoked for user ' + editor.nickname, 'succ')
            return redirect(url_for('projects', name=project.name))
    if project == None:
        return render_template('projects.html',
                               title=name,
                               form=form,
                               form2=form2,
                               form3=form3,
                               project=None,
                               user=g.user)
    else:
        return render_template('projects.html',
                               title=project.name,
                               form=form,
                               form2=form2,
                               form3=form3,
                               project=project,
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
    if r.json()['email'] is None:
        emailurl = "https://api.github.com/user/emails?access_token=" + oauth_token
        r = requests.get(emailurl)
        v = 0
        for i in r.json():
            if r.json()[v]['primary'] is True:
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


@app.route('/goods/<project>', methods=['GET', 'POST'])
@login_required
def goods(project):
    project = Projects.query.filter_by(name=project).first()
    form = GoodsForm()
    if form.validate_on_submit():
        gd = Good.query.filter_by(description=form.goods.data, project_id=project.id).first()
        if gd is None:
            good = Good(description=form.goods.data, project_id=project.id)
            db.session.add(good)
            db.session.commit()
            flash('Good Added to the Database', 'succ')
            return redirect(url_for('goods', project=project.name))
        else:
            flash('Good already exists', 'error')
    goods = Good.query.filter_by(project_id=project.id).all()
    return render_template('goods.html',
                           title=project.name,
                           form=form,
                           goods=goods,
                           project=project)


@app.route('/removeg/<project>/<desc>', methods=['GET', 'POST'])
@login_required
def removeg(project, desc):
    cproj = Projects.query.filter_by(name=project).first()
    Good.query.filter_by(description=desc, project_id=cproj.id).delete()
    db.session.commit()
    flash('Good removed', 'error')
    return redirect(url_for('goods', project=project))


@app.route('/soft_goals/<project>', methods=['GET', 'POST'])
@login_required
def soft_goals(project):
    project = Projects.query.filter_by(name=project).first()
    form = SoftGoalsForm()
    if form.validate_on_submit():
        sg = SoftGoal.query.filter_by(description=form.sgoals.data, project_id=project.id).first()
        if sg is None:
            sgoal = SoftGoal(description=form.sgoals.data, project_id=project.id, priority=form.priority.data)
            db.session.add(sgoal)
            db.session.commit()
            flash('Soft Goal Added to the Database', 'succ')
            return redirect(url_for('soft_goals', project=project.name))
        else:
            flash('Soft Goal already exists', 'error')
    sgoals = SoftGoal.query.filter_by(project_id=project.id).all()
    return render_template('sgoals.html',
                           title=project.name,
                           form=form,
                           sgoals=sgoals,
                           project=project)


@app.route('/removesg/<project>/<desc>', methods=['GET', 'POST'])
@login_required
def removesg(project, desc):
    cproj = Projects.query.filter_by(name=project).first()
    SoftGoal.query.filter_by(description=desc, project_id=cproj.id).delete()
    db.session.commit()
    flash('Soft goal removed', 'error')
    return redirect(url_for('soft_goals', project=project))