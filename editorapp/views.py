from flask import render_template, url_for, flash, redirect, request, session, g, abort
from editorapp import app, db, github
from flask_login import login_required
from wtforms import SelectField
from wtforms.validators import DataRequired
from .forms import StakeHoldersForm, ProjectForm, GoodsForm, FunctionalRequirementsForm, EditorForm, AccessForm, \
    HardGoalsForm, BbmForm, FlaskForm
from .models import Stakeholder, Users, lm, Projects, Good, FunctionalRequirement,\
    HardGoal, Role, BbMechanisms,  Assumptions, SubService, freq_serv
from flask_security import Security, SQLAlchemyUserDatastore, current_user
# from flask_security.utils import hash_password, verify_password, get_hmac
import flask_admin
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers
import requests


@app.before_first_request
def create_db_data():
    roles = Role.query.first()
    if not roles:
        user = Role(name='user', id=1)
        admin = Role(name= 'superuser', id=2)
        db.session.add(user)
        db.session.add(admin)
        db.session.commit()
    bbm = BbMechanisms.query.first()
    if not bbm:
        bbm_list = {'names':
                        ['Authentication Procedure',
                         'Asymmetric or Hybrid Encryption',
                         'Cryptographic Hash Function',
                         'Access Control',
                         'Digital Signature',
                         'Detection of Protection Worthy Image Areas',
                         'Anonymization of Protection Worthy Image Areas',
                         'Strong Authentication Procedure'],
                    'usages':
                        {'authenticity':
                             [True,
                              False,
                              True,
                              True,
                              True,
                              False,
                              False,
                              True],
                         'confidentiality':
                             [True,
                              True,
                              True,
                              True,
                              True,
                              False,
                              True,
                              True],
                         'integrity':
                             [False,
                              True,
                              True,
                              False,
                              False,
                              True,
                              True,
                              True]
                         }
                    }

        for ind, name in enumerate(bbm_list['names']):
            vals_dict = {}
            for use, vals in bbm_list['usages'].items():
                vals_dict[use] = vals[ind]
            kw = {'name': name, **vals_dict}
            bbmech = BbMechanisms(**kw)
            db.session.add(bbmech)
            db.session.commit()

    assumptions = Assumptions.query.first()
    if not assumptions:
        assumptions = [
            'Process Security',
            'Implementation Correctness',
            'Compiler Correctness',
            'Signature Key Trustworthiness',
            'Authentification Characteristics Authenticity'
        ]

        for assumption in assumptions:
            a = Assumptions(name=assumption)
            db.session.add(a)
        db.session.commit()



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
    g.project = None
    if 'user_id' in session:
        g.user = Users.query.get(session['user_id'])
    arguments = request.view_args
    if arguments is not None:
        if 'name' in arguments:
            if arguments['name'] is not 'New Project':
                g.page = arguments['name']
                session['current_project'] = arguments['name']
                g.project = Projects.query.filter_by(name=arguments['name']).first()
            else:
                g.page = 'Newproj'
                session['current_project'] = 'New Project'
        elif 'project' in arguments:
            g.page = arguments['project']
            session['current_project'] = arguments['project']
            g.project = Projects.query.filter_by(name=arguments['project']).first()
        else:
            g.page = 'Noproj'
            session['current_project'] = None
    else:
        g.page = 'Noproj'
        session['current_project'] = None


@app.route('/test', methods=['GET', 'POST'])
def test():
    form = HardGoalsForm()
    if form.validate_on_submit():
        print(form.test_case.data)
        print('did it')
        return redirect(url_for('test'))
    return render_template('test.html',
                           form=form)


@app.route('/')
@app.route('/index')
def index():
    access = False
    if g.user:
        for role in g.user.roles:
            if role == 'superuser':
                access = True
            else:
                access = False
    return render_template('index.html',
                           title='Home',
                           access=access)


@app.route('/stakeholders/<project>', methods=['GET', 'POST'])
@login_required
def stakeholders(project):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
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
    else:
        flash('You don\'t have permission to access this project.')
        return redirect(url_for('index'))


@app.route('/removesh/<project>/<desc>', methods=['GET', 'POST'])
@login_required
def removesh(project, desc):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        Stakeholder.query.filter_by(nickname=desc, project_id=project.id).delete()
        db.session.commit()
        flash('Stakeholder "{}" removed'.format(desc), 'error')
        return redirect(url_for('stakeholders', project=project.name))
    else:
        flash('You don\'t have permission to access this project.')
        return redirect(url_for('index'))


@app.route('/projects/<name>', methods=['GET', 'POST'])
@login_required
def projects(name):
    project = Projects.query.filter_by(name=name).first()
    form = ProjectForm()
    form2 = EditorForm()
    form3 = AccessForm()
    current_editors = []
    users = []
    usrs = Users.query.all()
    for usr in usrs:
        users.append(usr.nickname)
    if project is not None:
        for edtr in project.editors:
            current_editors.append(edtr.nickname)
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
        elif editor.nickname in current_editors:
            flash('User is already an editor', 'error')
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
            return redirect(url_for('projects', name=project.name))
        elif editor.nickname not in current_editors:
            flash('User is not an editor.', 'error')
            return redirect(url_for('projects', name=project.name))
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
    elif g.user in project.editors:
        bbms = BbMechanisms.query.all()
        return render_template('projects.html',
                               title=project.name,
                               form=form,
                               form2=form2,
                               form3=form3,
                               project=project,
                               user=g.user,
                               current_editors=current_editors,
                               users=users,
                               bbms=bbms)
    else:
        flash('You don\'t have permission to access this project.', 'error')
        return redirect(url_for('index'))


@app.route('/project/<project>', methods=['DELETE', 'GET'])
@login_required
def delete_project(project):
    project = Projects.query.filter_by(name=project).first()
    if g.user.id == project.creator:
        stakeholders = Stakeholder.query.filter_by(project_id=project.id).all()
        for stkhld in stakeholders:
            db.session.delete(stkhld)
            db.session.commit()
        softgoals = FunctionalRequirement.query.filter_by(project_id=project.id).all()
        for sftgl in softgoals:
            db.session.delete(sftgl)
            db.session.commit()
        goods = Good.query.filter_by(project_id=project.id).all()
        for gd in goods:
            db.session.delete(gd)
            db.session.commit()
        hard_goals = HardGoal.query.filter_by(project_id=project.id).all()
        for hg in hard_goals:
            for bbm in hg.bbmechanisms:
                hg.remove_bb(bbm)
            db.session.delete(hg)
            db.session.commit()
        for editor in project.editors:
            u = editor.revoke_access(project)
            db.session.add(u)
            db.session.commit()
        db.session.delete(project)
        db.session.commit()
        flash('Project %s deleted' % project.name)
        return redirect(url_for('index'))
    else:
        flash('Cannot delete projects you don\'t own', 'error')
        return redirect(url_for('projects', name=project.name))

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
        user = Users(id=u_id, nickname=nickname, contact=contact)
        alrdy_users = Users.query.first()
        if not alrdy_users:
            role = Role.query.filter_by(name='superuser').first()
        else:
            role= Role.query.filter_by(name='user').first()
        db.session.add(user)
        db.session.commit()
        r = user.user_register(role)
        db.session.add(r)
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
    if g.user in project.editors:
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
    else:
        flash('You don\'t have permission to access this project')
        return redirect(url_for('index'))


@app.route('/removeg/<project>/<desc>', methods=['GET', 'POST'])
@login_required
def removeg(project, desc):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        Good.query.filter_by(description=desc, project_id=project.id).delete()
        db.session.commit()
        flash('Good "{}" removed'.format(desc), 'error')
        return redirect(url_for('goods', project=project.name))
    else:
        flash('You don\'t have permission to access this project')
        return redirect(url_for('index'))


@app.route('/functional_req/<project>', methods=['GET', 'POST'])
@login_required
def functional_req(project):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        form = FunctionalRequirementsForm()
        if request.method == 'POST' and request.form.get('freqbtn'):
            if form.freq.data is not '':
                fr = FunctionalRequirement.query.filter_by(description=form.freq.data, project_id=project.id).first()
                if fr is None:
                    freq = FunctionalRequirement(description=form.freq.data, project_id=project.id)
                    db.session.add(freq)
                    db.session.commit()
                    flash('Functional Requirement Added to the Database', 'succ')
                    return redirect(url_for('functional_req', project=project.name))
                else:
                    flash('Functional Requirement already exists', 'error')
            else:
                flash('Functional Requirement field can\'t be empty', 'error')

        elif request.method == 'POST' and request.form.get('servbtn'):
            if form.subserv.data is not '':
                sub = SubService.query.filter_by(name=form.subserv.data, project_id=project.id).first()
                if sub is None:
                    sb = SubService(name=form.subserv.data, project_id=project.id)
                    db.session.add(sb)
                    db.session.commit()
                    flash('Service Added to the Database', 'succ')
                    return redirect(url_for('functional_req', project=project.name))
                else:
                    flash('Service Already Exists', 'error')
            else:
                flash('Service Field can\'t be empty', 'error')
        elif request.method == 'POST' and request.form.get('updatech'):
            chbx_list = request.form.getlist('chbpx')
            freqs = FunctionalRequirement.query.filter_by(project_id=project.id).all()
            current_services_list = []
            for fr in freqs:
                for serv in fr.services:
                    if serv in fr.services:
                        curr_serv = '{}-{}'.format(fr.id, serv.id)
                        current_services_list.append(curr_serv)
            for item in chbx_list:
                if item in current_services_list:
                    current_services_list.remove(item)
                freq_id, serv_id = item.split('-')
                frq = FunctionalRequirement.query.filter_by(id=freq_id).first()
                serv = SubService.query.filter_by(id=serv_id).first()
                frq.add_serv(serv)
                db.session.commit()
                for remaining in current_services_list:
                    rem_freq_id, rem_serv_id = remaining.split('-')
                    rem_frq = FunctionalRequirement.query.filter_by(id=rem_freq_id).first()
                    rem_serv = SubService.query.filter_by(id=rem_serv_id).first()
                    rem_frq.remove_serv(rem_serv)
                    db.session.commit()
            flash('Functional Requirements and Sub-services Table Updated', 'succ')
            return redirect(url_for('functional_req', project=project.name))

        return render_template('funcreq.html',
                               title=project.name,
                               form=form,
                               project=project)
    else:
        flash('You don\'t have permission to access this project.')
        return redirect(url_for('index'))


@app.route('/removefr/<project>/<desc>', methods=['GET', 'POST'])
@login_required
def removefr(project, desc):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        fr = FunctionalRequirement.query.filter_by(description=desc, project_id=project.id).first()
        for serv in fr.services:
            fr.remove_serv(serv)
        db.session.commit()
        FunctionalRequirement.query.filter_by(description=desc, project_id=project.id).delete()
        db.session.commit()
        flash('Functional Requirement "{}" removed'.format(desc), 'error')
        return redirect(url_for('functional_req', project=project.name))
    else:
        flash('You don\'t have permission to access this project.')
        return redirect(url_for('index'))


@app.route('/removesub/<project>/<id>', methods=['GET', 'POST'])
@login_required
def removesub(project, id):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        ss = SubService.query.filter_by(id=id, project_id=project.id).first()
        name = ss.name
        for serv in ss.functionalreqs:
            serv.remove_serv(ss)
        db.session.commit()
        SubService.query.filter_by(id=id, project_id=project.id).delete()
        db.session.commit()
        flash('Sub-Service "{}" removed'.format(name), 'error')
        return redirect(url_for('functional_req', project=project.name))
    else:
        flash('You don\'t have permission to access this project.')
        return redirect(url_for('index'))


@app.route('/hard_goals/<project>', methods=['GET', 'POST'])
@login_required
def hard_goals(project):
    access_granted = check_permission(project)
    if access_granted:
        project = Projects.query.filter_by(name=project).first()
        hardgoalz = HardGoal.query.filter_by(project_id=project.id).all()
        hardgs = []
        for hg in hardgoalz:
            if hg.description is not None:
                hardgs.append(hg.description)
        if request.method == 'POST' and request.form.get('subb') == 'pressed':

            for good in project.goods:
                for goal in request.form.getlist('authenticity%s' % good.id):
                    auth_desc = goal + " of " + good.description
                    cb_value = 'authenticity%s' % good.id
                    HG = HardGoal.query.filter_by(authenticity=auth_desc, project_id=project.id).first()
                    if HG is None:
                        auth = HardGoal(authenticity=auth_desc, project_id=project.id, cb_value=cb_value)
                        db.session.add(auth)
                        db.session.commit()
                        flash('Protection Goals updated', 'succ')

                for goal in request.form.getlist('confidentiality%s' % good.id):
                    conf_desc = goal + " of " + good.description
                    cb_value = 'confidentiality%s' % good.id
                    HG = HardGoal.query.filter_by(confidentiality=conf_desc, project_id=project.id).first()
                    if HG is None:
                        conf = HardGoal(confidentiality=conf_desc, project_id=project.id, cb_value=cb_value)
                        db.session.add(conf)
                        db.session.commit()
                        flash('Protection Goals updated', 'succ')

                for goal in request.form.getlist('integrity%s' % good.id):
                    integ_desc = goal + " of " + good.description
                    cb_value = 'integrity%s' % good.id
                    HG = HardGoal.query.filter_by(integrity=integ_desc, project_id=project.id).first()
                    if HG is None:
                        integ = HardGoal(integrity=integ_desc, project_id=project.id, cb_value=cb_value)
                        db.session.add(integ)
                        db.session.commit()
                        flash('Protection Goals updated', 'succ')

            for hgoal in project.hard_goals:
                test = request.form.getlist('Hgoal%s' % hgoal.id)
                if test and hgoal.description is None:
                    hgoal.priority = True
                    db.session.add(hgoal)
                    db.session.commit()
                elif not test and hgoal.description is None:
                    hgoal.priority = False
                    db.session.add(hgoal)
                    db.session.commit()
                gen = (hgl for hgl in project.hard_goals if hgl.description is not None)
                for hgl in gen:
                    if test:
                        if hgoal.authenticity is not None and hgoal.authenticity in hgl.description:
                            hgl.priority = True
                            db.session.add(hgl)
                            db.session.commit()
                        elif hgoal.confidentiality is not None and hgoal.confidentiality in hgl.description:
                            hgl.priority = True
                            db.session.add(hgl)
                            db.session.commit()
                        elif hgoal.integrity is not None and hgoal.integrity in hgl.description:
                            hgl.priority = True
                            db.session.add(hgl)
                            db.session.commit()
                    else:
                        if hgoal.authenticity is not None and hgoal.authenticity in hgl.description:
                            hgl.priority = False
                            db.session.add(hgl)
                            db.session.commit()
                        elif hgoal.confidentiality is not None and hgoal.confidentiality in hgl.description:
                            hgl.priority = False
                            db.session.add(hgl)
                            db.session.commit()
                        elif hgoal.integrity is not None and hgoal.integrity in hgl.description:
                            hgl.priority = False
                            db.session.add(hgl)
                            db.session.commit()

            current_req = []
            for i in request.form:
                current_req.append(i)
            hardgoals = HardGoal.query.filter_by(project_id=project.id).all()
            db_values = []
            for hgoal in hardgoals:
                if hgoal.cb_value:
                    db_values.append(hgoal.cb_value)

            for val in db_values:
                if val not in current_req:
                    HardGoal.query.filter_by(cb_value=val, project_id=project.id).delete()
                    db.session.commit()
                    flash('Item(s) removed from the database', 'error')

            return redirect(url_for('hard_goals', project=project.name))

        elif request.method == 'POST' and request.form.get('sub2') == 'pressed2':
            callback_list = request.form.getlist('hglist')
            if callback_list != []:
                for item in callback_list:
                    item_parts = item.split('¡')
                    final_string = '{} ensures the {} during the {}'.format(item_parts[0], item_parts[2], item_parts[1])
                    nhg = HardGoal.query.filter_by(description=final_string).first()
                    if nhg is None:
                        new_hg = HardGoal(project_id=project.id, description=final_string)
                        current_hgs = HardGoal.query.filter_by(project_id=project.id, priority=True).all()
                        for chg in current_hgs:
                            if chg.authenticity:
                                if item_parts[2] == chg.authenticity:
                                    new_hg.priority = True
                            elif chg.confidentiality:
                                if item_parts[2] == chg.confidentiality:
                                    new_hg.priority = True
                            elif chg.integrity:
                                if item_parts[2] == chg.integrity:
                                    new_hg.priority = True
                        if 'Authenticity' in final_string:
                            new_hg.authenticity = 'yes'
                        elif 'Confidentiality' in final_string:
                            new_hg.confidentiality = 'yes'
                        elif 'Integrity' in final_string:
                            new_hg.integrity = 'yes'
                        db.session.add(new_hg)
                        db.session.commit()
                    if final_string in hardgs:
                        hardgs.remove(final_string)
                for remaining_hg in hardgs:
                    HardGoal.query.filter_by(project_id=project.id, description=remaining_hg).delete()
                    db.session.commit()
            else:
                for remaining_hg in hardgs:
                    HardGoal.query.filter_by(project_id=project.id, description=remaining_hg).delete()
                    db.session.commit()
            flash('Hard Goals Database Updated', 'succ')
            return redirect(url_for('hard_goals', project=project.name))

        return render_template('hardgoals.html',
                               title=project.name,
                               project=project,
                               hardgs=hardgs)
    else:
        flash('You don\'t have permission to access this project.')
        return redirect(url_for('index'))


def check_permission(project):
    current_project = Projects.query.filter_by(name=project).first()
    if g.user in current_project.editors:
        return True
    else:
        return False


@app.route('/bbm/<project>', methods=['GET', 'POST'])
@login_required
def bbm(project):
    project = Projects.query.filter_by(name=project).first()
    blackbox_mechanisms = BbMechanisms.query.all()
    choices_tuples = [(bbm.id, bbm.name) for bbm in blackbox_mechanisms]
    table_list = [[],[],[]]
    count = 0
    class MultipleSelects(FlaskForm):
        pass

    hgoals = HardGoal.query.filter_by(project_id=project.id).all()
    for hg in hgoals:
        if hg.description:
            table_list[0].append(count)
            count += 1
            table_list[1].append(hg.description)
            bbms = [bbm.id for bbm in hg.bbmechanisms]
            if bbms:
                default_bbm = bbms[0]
            else:
                default_bbm = 1
            if hg.authenticity == 'yes':
                choices_tuples = [(bbma.id, bbma.name) for bbma in blackbox_mechanisms if bbma.authenticity]
            if hg.confidentiality == 'yes':
                choices_tuples = [(bbmc.id, bbmc.name) for bbmc in blackbox_mechanisms if bbmc.confidentiality]
            if hg.integrity == 'yes':
                choices_tuples = [(bbmi.id, bbmi.name) for bbmi in blackbox_mechanisms if bbmi.authenticity]
            setattr(MultipleSelects, str(hg.id), SelectField('Desired Mechanism', choices=choices_tuples, default=default_bbm, validators=[DataRequired()]))
            table_list[2].append('{}'.format(hg.id))

    form2 = MultipleSelects()

    if request.method == 'POST' and request.form.get('sub') == 'pressed':
        for key,value in form2.data.items():
            if key != 'csrf_token':
                hardG = HardGoal.query.filter_by(id=key).first()
                blbxm = BbMechanisms.query.filter_by(id=value).first()
                hardG.add_bb(blbxm)
                db.session.commit()
        flash('Black Box mechanisms updated', 'succ')
    elif request.method == 'POST' and request.form.get('sub') != 'pressed':
        if request.form.get('rmbbm'):
            data = request.form.get('rmbbm').split('-')
            hg = HardGoal.query.filter_by(id=data[0]).first()
            blbm = BbMechanisms.query.filter_by(id=data[1]).first()
            hg.remove_bb(blbm)
            db.session.commit()
            flash('Black Box Mechanism "{}" successfully removed for Hard Goal "{}"'.format(blbm.name, hg.description), 'succ')
            return redirect(url_for('bbm', project=project.name))

    return render_template('bbm.html',
                           title=project.name,
                           project=project,
                           form2=form2,
                           blackbox_mechanisms=blackbox_mechanisms,
                           choices_tuples=choices_tuples,
                           table_list=table_list)


@app.route('/bbmech/<project>', methods=['POST', 'GET'])
@login_required
def bbmech(project):
    access = check_permission(project)
    project = Projects.query.filter_by(name=project).first()
    if access:
        bbms = BbMechanisms.query.all()
        return render_template('bbmech.html',
                               title=project.name,
                               project=project,
                               bbms=bbms)
    else:
        flash('You don\'t have permission to access this project', 'error')
        return redirect(abort(404))


# Setting up Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, Users, Role)
security = Security(app, user_datastore)

class MyModelView(sqla.ModelView):

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated():
                flash('You don\'t have permission to access this page.', 'error')
                return redirect(url_for('index'))
            else:
                return redirect(url_for('security.login', next=request.url))


admin = flask_admin.Admin(
    app,
    'Kastel Editor',
    base_template='bbmdb.html',
    template_mode='bootstrap3'
)

admin.add_view(MyModelView(Role, db.session))
admin.add_view(MyModelView(Users, db.session))
admin.add_view(MyModelView(Projects, db.session))
admin.add_view(MyModelView(BbMechanisms, db.session))


@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for,
    )