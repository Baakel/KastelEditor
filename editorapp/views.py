from flask import render_template, url_for, flash, redirect, request, session
from editorapp import app, db
from .forms import StakeHoldersForm
from .models import Stakeholder

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