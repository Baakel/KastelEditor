from random import sample
from flask import render_template, url_for, flash, redirect, request, session, g, abort, jsonify
from editorapp import app, db, github
from flask_login import login_required
from wtforms import SelectField
from wtforms.validators import DataRequired
from .forms import StakeHoldersForm, ProjectForm, GoodsForm, FunctionalRequirementsForm, EditorForm, AccessForm, \
    HardGoalsForm, BbmForm, FlaskForm
from .models import Stakeholder, Users, lm, Projects, Good, FunctionalRequirement,\
    HardGoal, Role, BbMechanisms,  Assumptions, SubService, freq_serv, hard_mechanism
from flask_security import Security, SQLAlchemyUserDatastore, current_user
# from flask_security.utils import hash_password, verify_password, get_hmac
import flask_admin
from flask_admin.contrib.sqla.form import InlineModelConverter
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers
import requests
import json


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
            if bbmech.name == 'Asymmetric or Hybrid Encryption':
                bbmech.extra_hg = 'Authenticity of the Encrypted Material'
            db.session.add(bbmech)
            db.session.commit()

    assumptions = Assumptions.query.first()
    if not assumptions:
        assumptions = [
            'Process Security',
            'Implementation Correctness',
            'Signature Key Trustworthiness',
            'Authenticity of the Authentication Characteristics',
            'Security of the Runtime Environment',
            'Encryption keys Authenticity',
            'Private Key Secrecy',
            'Protection fo the Shared Secret'
        ]

        for assumption in assumptions:
            a = Assumptions(name=assumption)
            db.session.add(a)
        db.session.commit()

        for ass in Assumptions.query.all():
            if ass.name == 'Process Security':
                bbm = BbMechanisms.query.filter_by(name='Authentication Procedure').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Asymmetric or Hybrid Encryption').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Cryptographic Hash Function').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Strong Authentication Procedure').first()
                bbm.add_ass(ass)

            if ass.name == 'Implementation Correctness':
                bbm = BbMechanisms.query.filter_by(name='Authentication Procedure').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Asymmetric or Hybrid Encryption').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Cryptographic Hash Function').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Access Control').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Digital Signature').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Detection of Protection Worthy Image Areas').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Anonymization of Protection Worthy Image Areas').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Strong Authentication Procedure').first()
                bbm.add_ass(ass)

            if ass.name == 'Signature Key Trustworthiness':
                bbm = BbMechanisms.query.filter_by(name='Access Control').first()
                bbm.add_ass(ass)
                bbm = BbMechanisms.query.filter_by(name='Digital Signature').first()
                bbm.add_ass(ass)

            if ass.name == 'Authenticity of the Authentication Characteristics':
                bbm = BbMechanisms.query.filter_by(name='Strong Authentication Procedure').first()
                bbm.add_ass(ass)

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


@app.route('/<project>/export')
@login_required
def export(project):
    proj = Projects.query.filter_by(name=project).first()
    if proj.public or g.user in proj.editors:
        project_dict = {}
        project_dict['Project'] = proj.name
        creator = Users.query.filter_by(id=proj.creator).first()
        project_dict['Project Creator'] = creator.nickname
        project_dict['Contact Info'] = creator.contact
        editor_list = []
        for i, editor in enumerate(proj.editors):
            editor_list.append(str(editor))
        project_dict['Project Editors'] = editor_list
        project_dict['Public'] = proj.public
        project_dict['Final Assumptions Signed'] = proj.final_assumptions
        assets = []
        for asset in proj.goods:
            assets.append(asset.description)
        project_dict['Assets'] = assets
        stakeholders = []
        for stakeholder in proj.stake_holders:
            stakeholders.append(stakeholder.nickname)
        project_dict['Stakeholders'] = stakeholders
        asset_stakeholder_relationship = {}
        for asset in proj.goods:
            asset_stakeholder_relationship[asset.description] = []
            for stakeholder in asset.stakeholders:
                asset_stakeholder_relationship[asset.description].append(stakeholder.nickname)
        project_dict['Asset and Stakeholder Relationships'] = asset_stakeholder_relationship
        functional_requirements = []
        for fr in proj.functional_req:
            functional_requirements.append(fr.description)
        project_dict['Functional Requirements'] = functional_requirements
        functional_requirements_services_relationship = {}
        for fr in proj.functional_req:
            functional_requirements_services_relationship[fr.description] = []
            for serv in fr.services:
                functional_requirements_services_relationship[fr.description].append(serv.name)
        project_dict['Functional Requirements and Services Relationships'] = functional_requirements_services_relationship
        services = []
        for service in proj.sub_services:
            services.append(service.name)
        project_dict['Services'] = services
        soft_goals = [sg for sg in proj.hard_goals if not sg.description]
        soft_goals_dict = {}
        for sg in soft_goals:
            if sg.integrity:
                soft_goals_dict[sg.integrity] = {'priority': sg.priority, 'cb_value': sg.cb_value}
        for sg in soft_goals:
            if sg.authenticity:
                soft_goals_dict[sg.authenticity] = {'priority': sg.priority, 'cb_value': sg.cb_value}
        for sg in soft_goals:
            if sg.confidentiality:
                soft_goals_dict[sg.confidentiality] = {'priority': sg.priority, 'cb_value': sg.cb_value}
        project_dict['Soft Goals'] = soft_goals_dict
        hard_goals = [hg for hg in proj.hard_goals if hg.description]
        hard_goals_dict = {}
        hard_bb_mechanism_relationship = {}
        for hg in hard_goals:
            if hg.authenticity:
                if hg.original_hg:
                    original = HardGoal.query.filter_by(id=hg.original_hg).first()
                    hard_goals_dict[hg.description] = {
                        'authenticity': hg.authenticity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                        'extra_hg': hg.extra_hg, 'original_hg': original.description}
                else:
                    hard_goals_dict[hg.description] = {
                        'authenticity': hg.authenticity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                        'extra_hg': hg.extra_hg, 'original_hg': None}
            if hg.confidentiality:
                if hg.original_hg:
                    original = HardGoal.query.filter_by(id=hg.original_hg).first()
                    hard_goals_dict[hg.description] = {
                        'confidentiality': hg.confidentiality, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                        'extra_hg': hg.extra_hg, 'original_hg': original.description}
                else:
                    hard_goals_dict[hg.description] = {
                        'confidentiality': hg.confidentiality, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                        'extra_hg': hg.extra_hg, 'original_hg': None}
            if hg.integrity:
                if hg.original_hg:
                    original = HardGoal.query.filter_by(id=hg.original_hg).first()
                    hard_goals_dict[hg.description] = {
                        'integrity': hg.integrity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                        'extra_hg': hg.extra_hg, 'original_hg': original.description}
                else:
                    hard_goals_dict[hg.description] = {
                        'integrity': hg.integrity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                        'extra_hg': hg.extra_hg, 'original_hg': None}
            for bbm in hg.bbmechanisms:
                hard_bb_mechanism_relationship[hg.description] = bbm.name
        project_dict['Hard Mechanism Relationship']  = hard_bb_mechanism_relationship
        project_dict['Hard Goals'] = hard_goals_dict
        black_box_mechanisms_dict = {}
        for bb in BbMechanisms.query.all():
            black_box_mechanisms_dict[bb.name] = {'authenticity': bb.authenticity, 'integrity': bb.integrity,
                                                  'confidentiality': bb.confidentiality,
                                                  'extra_hg': bb.extra_hg}
        project_dict['Black Box Mechanisms'] = black_box_mechanisms_dict
        assumptions = []
        for ass in Assumptions.query.all():
            assumptions.append(ass.name)
        project_dict['Assumptions'] = assumptions
        black_box_assumptions_dict = {}
        for bb in BbMechanisms.query.all():
            black_box_assumptions_dict[bb.name] = []
            for assumption in bb.assumptions:
                black_box_assumptions_dict[bb.name].append(assumption.name)
        project_dict['Black Box And Assumptions Relationship'] = black_box_assumptions_dict
        return jsonify(project_dict)
    else:
        flash('You don\'t have permission to do that', 'error')
        return redirect(url_for('index'))


@app.route('/import', methods=['POST'])
@login_required
def import_project():
    try:
        file = request.files['inputFile']
        read_file = file.read()
        decoded_file = read_file.decode('utf-8')
        json_data = json.loads(decoded_file)
        project_name = Projects.make_unique_name(json_data['Project'])
        new_project = Projects(creator=g.user.id, name=project_name,
                               final_assumptions=json_data['Final Assumptions Signed'], public=json_data['Public'])
        db.session.add(new_project)
        db.session.commit()
        curr_project = Projects.query.filter_by(name=project_name).first()
        for editor in json_data['Project Editors']:
            ed = Users.query.filter_by(nickname=editor).first()
            if ed:
                ed.contribute(curr_project)
        for stakeholder in json_data['Stakeholders']:
            stk = Stakeholder(nickname=stakeholder, project_id=curr_project.id)
            db.session.add(stk)
            db.session.commit()
        for asset in json_data['Assets']:
            ass = Good(description=asset, project_id=curr_project.id)
            db.session.add(ass)
            db.session.commit()
        for asset in json_data['Asset and Stakeholder Relationships']:
            ass = Good.query.filter_by(description=asset, project_id=curr_project.id).first()
            for stakeholder in json_data['Asset and Stakeholder Relationships'][asset]:
                stk = Stakeholder.query.filter_by(nickname=stakeholder, project_id=curr_project.id).first()
                ass.add_stakeholder(stk)
            db.session.commit()
        for functional_requirement in json_data['Functional Requirements']:
            fr = FunctionalRequirement(description=functional_requirement, project_id=curr_project.id)
            db.session.add(fr)
            db.session.commit()
        for service in json_data['Services']:
            sv = SubService(name=service, project_id=curr_project.id)
            db.session.add(sv)
            db.session.commit()
        for functional_requirement in json_data['Functional Requirements and Services Relationships']:
            fr = FunctionalRequirement.query.filter_by(description=functional_requirement, project_id=curr_project.id).first()
            for service in json_data['Functional Requirements and Services Relationships'][functional_requirement]:
                sv = SubService.query.filter_by(name=service, project_id=curr_project.id).first()
                fr.add_serv(sv)
            db.session.commit()
        for soft_goals in json_data['Soft Goals']:
            if 'authenticity' in json_data['Soft Goals'][soft_goals]['cb_value']:
                hg = HardGoal(priority=json_data['Soft Goals'][soft_goals]['priority'],
                              cb_value=json_data['Soft Goals'][soft_goals]['cb_value'],
                              authenticity=soft_goals, project_id=curr_project.id)
                db.session.add(hg)
                db.session.commit()
            elif 'confidentiality' in json_data['Soft Goals'][soft_goals]['cb_value']:
                hg = HardGoal(priority=json_data['Soft Goals'][soft_goals]['priority'],
                              cb_value=json_data['Soft Goals'][soft_goals]['cb_value'],
                              confidentiality=soft_goals, project_id=curr_project.id)
                db.session.add(hg)
                db.session.commit()
            elif 'integrity' in json_data['Soft Goals'][soft_goals]['cb_value']:
                hg = HardGoal(priority=json_data['Soft Goals'][soft_goals]['priority'],
                              cb_value=json_data['Soft Goals'][soft_goals]['cb_value'],
                              integrity=soft_goals, project_id=curr_project.id)
                db.session.add(hg)
                db.session.commit()
        for hard_goal in json_data['Hard Goals']:
            hg = HardGoal(description=hard_goal, project_id=curr_project.id, **json_data['Hard Goals'][hard_goal])
            db.session.add(hg)
            db.session.commit()
        for hard_goal in json_data['Hard Goals']:
            if json_data['Hard Goals'][hard_goal]['original_hg']:
                original_hg_obj = HardGoal.query.filter_by(description=json_data['Hard Goals'][hard_goal]['original_hg'],
                                                           project_id=curr_project.id).first()
            else:
                original_hg_obj = None
            hg = HardGoal.query.filter_by(description=hard_goal, project_id=curr_project.id).first()
            if original_hg_obj:
                hg.original_hg = original_hg_obj.id
            else:
                hg.original_hg = None
            db.session.commit()
        for bbm in json_data['Black Box Mechanisms']:
            bb = BbMechanisms.query.filter_by(name=bbm, **json_data['Black Box Mechanisms'][bbm]).first()
            if bb is None:
                bb = BbMechanisms(name=bbm, **json_data['Black Box Mechanisms'][bbm])
                db.session.add(bb)
                db.session.commit()
        for assumption in json_data['Assumptions']:
            ass = Assumptions.query.filter_by(name=assumption).first()
            if ass is None:
                ass = Assumptions(name=assumption)
                db.session.add(ass)
                db.session.commit()
        for bbm in json_data['Black Box And Assumptions Relationship']:
            bb = BbMechanisms.query.filter_by(name=bbm).first()
            for assumption in json_data['Black Box And Assumptions Relationship'][bbm]:
                ass = Assumptions.query.filter_by(name=assumption).first()
                if not bb.alrdy_used(ass):
                    bb.add_ass(ass)
        for hard_goal in json_data['Hard Mechanism Relationship']:
            hg = HardGoal.query.filter_by(description=hard_goal, project_id=curr_project.id).first()
            bbm = BbMechanisms.query.filter_by(name=json_data['Hard Mechanism Relationship'][hard_goal]).first()
            if bbm:
                hg.add_bb(bbm)
            db.session.commit()
        return redirect(url_for('projects', name=project_name))
    except Exception as e:
        print(e)
        flash('An error occurred while importing project. Information might not be complete', 'error')
        return redirect(url_for('index'))


@app.route('/tree/<project>', methods=['GET', 'POST'])
@login_required
def tree(project):
    proj = Projects.query.filter_by(name=project).first()
    if g.user in proj.editors or proj.public:
        return render_template('tree.html',
                               project=proj,
                               title=proj.name)
    else:
        flash('You don\'t have permission to see that.', 'error')
        return redirect(url_for('index'))


@app.route('/testdata')
def testdata():
    proj = request.args.get('project')
    project = Projects.query.filter_by(name=proj).first()
    dictionary = {
        'chart': {
            'container': '#tree-simple',
            'animateOnInt': True,
            'node': {
                'collapsable': False,
                'HTMLclass': 'proj'
            },
            'animation': {
                'nodeAnimation': 'easeInOutSine',
                'nodeSpeed': 700
            },
            'rootOrientation': 'WEST',
            'connectors': {
                'type': 'curve'
            },
            'drawLineThrough': True
        },
        'nodeStructure': {
            'text': {'name': project.name, 'desc': 'Project'},
            'children': [

            ]
        }

    }
    auth_gen = (sg for sg in project.hard_goals if sg.authenticity and sg.description == None)
    for softg in auth_gen:
        curr_dict = { 'text': {'name': softg.authenticity, 'desc': 'Soft Goal'},
                      'children': [],
                      'HTMLclass': 'yellow',
                      'collapsable': True}
        for asset in project.goods:
            if asset.description in softg.authenticity:
                for stakeholder in asset.stakeholders:
                    children_dict = {'text': {'name': stakeholder.nickname, 'desc': 'Important to:'},
                                     'children': [],
                                     'HTMLclass': 'red'}
                    curr_dict['children'].append(children_dict)
        auth_hg_gen = (hg for hg in project.hard_goals if hg.description and softg.authenticity in hg.description)
        for hardg in auth_hg_gen:
            if hardg.priority:
                hg_dict = {'text': {'name': hardg.description, 'desc': 'Hard Goal'},
                           'children': [],
                           'HTMLclass': 'blue'}
            else:
                hg_dict = {'text': {'name': hardg.description, 'desc': 'Hard Goal'},
                           'children': [],
                           'HTMLclass': 'grey'}
            for bbm in hardg.bbmechanisms:
                bbm_dict = { 'text': {'name': bbm.name, 'desc': 'Black Box Mechanism'},
                             'children': [],
                             'HTMLclass': 'dark',
                             'collapsable': True}
                for ass in bbm.assumptions:
                    ass_dict = {'text': {'name': ass.name, 'desc': 'Assumptions'},
                                'children': [],
                                'HTMLclass': 'green'}
                    bbm_dict['children'].append(ass_dict)

                hg_dict['children'].append(bbm_dict)

            curr_dict['children'].append(hg_dict)

        dictionary['nodeStructure']['children'].append(curr_dict)

    conf_gen = (sg for sg in project.hard_goals if sg.confidentiality and sg.description == None)
    for softg in conf_gen:
        curr_dict = {'text': {'name': softg.confidentiality, 'desc': 'Soft Goal'},
                     'children': [],
                     'HTMLclass': 'yellow',
                     'collapsable': True}
        for asset in project.goods:
            if asset.description in softg.confidentiality:
                for stakeholder in asset.stakeholders:
                    children_dict = {'text': {'name': stakeholder.nickname, 'desc': 'Important to:'},
                                     'children': [],
                                     'HTMLclass': 'red'}
                    curr_dict['children'].append(children_dict)
        conf_hg_gen = (hg for hg in project.hard_goals if hg.description and softg.confidentiality in hg.description)
        for hardg in conf_hg_gen:
            if hardg.priority:
                hg_dict = {'text': {'name': hardg.description, 'desc': 'Hard Goal'},
                           'children': [],
                           'HTMLclass': 'blue'}
            else:
                hg_dict = {'text': {'name': hardg.description, 'desc': 'Hard Goal'},
                           'children': [],
                           'HTMLclass': 'grey'}
            for bbm in hardg.bbmechanisms:
                bbm_dict = {'text': {'name': bbm.name, 'desc': 'Black Box Mechanism'},
                            'children': [],
                            'HTMLclass': 'dark',
                            'collapsable': True}
                for ass in bbm.assumptions:
                    ass_dict = {'text': {'name': ass.name, 'desc': 'Assumptions'},
                                'children': [],
                                'HTMLclass': 'green'}
                    bbm_dict['children'].append(ass_dict)

                hg_dict['children'].append(bbm_dict)

            curr_dict['children'].append(hg_dict)

        dictionary['nodeStructure']['children'].append(curr_dict)

    int_gen = (sg for sg in project.hard_goals if sg.integrity and sg.description == None)
    for softg in int_gen:
        curr_dict = {'text': {'name': softg.integrity, 'desc': 'Soft Goal'},
                     'children': [],
                     'HTMLclass': 'yellow',
                     'collapsable': True}
        for asset in project.goods:
            if asset.description in softg.integrity:
                for stakeholder in asset.stakeholders:
                    children_dict = {'text': {'name': stakeholder.nickname, 'desc': 'Important to:'},
                                     'children': [],
                                     'HTMLclass': 'red'}
                    curr_dict['children'].append(children_dict)
        int_hg_gen = (hg for hg in project.hard_goals if hg.description and softg.integrity in hg.description)
        for hardg in int_hg_gen:
            if hardg.priority:
                hg_dict = {'text': {'name': hardg.description, 'desc': 'Hard Goal'},
                           'children': [],
                           'HTMLclass': 'blue'}
            else:
                hg_dict = {'text': {'name': hardg.description, 'desc': 'Hard Goal'},
                           'children': [],
                           'HTMLclass': 'grey'}
            for bbm in hardg.bbmechanisms:
                bbm_dict = {'text': {'name': bbm.name, 'desc': 'Black Box Mechanism'},
                            'children': [],
                            'HTMLclass': 'dark',
                            'collapsable': True}
                for ass in bbm.assumptions:
                    ass_dict = {'text': {'name': ass.name, 'desc': 'Assumptions'},
                                'children': [],
                                'HTMLclass': 'green'}
                    bbm_dict['children'].append(ass_dict)

                hg_dict['children'].append(bbm_dict)

            curr_dict['children'].append(hg_dict)

        dictionary['nodeStructure']['children'].append(curr_dict)
    return jsonify(dictionary)
    # return jsonify({'results': sample(range(1,10), 5)})


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

        projects_list = Projects.query.all()
    else:
        projects_list = []
    return render_template('index.html',
                           title='Home',
                           access=access,
                           projects_list=projects_list)


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
        flash('You don\'t have permission to access this project.', 'error')
        return redirect(url_for('index'))


@app.route('/removesh/<project>/<desc>', methods=['GET', 'POST'])
@login_required
def removesh(project, desc):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        sh = Stakeholder.query.filter_by(nickname=desc, project_id=project.id).first()
        name = sh.nickname
        for sth in sh.goods:
            sth.remove_stakeholder(sh)
        db.session.commit()
        Stakeholder.query.filter_by(nickname=desc, project_id=project.id).delete()
        db.session.commit()
        flash('Stakeholder "{}" removed'.format(name), 'error')
        return redirect(url_for('stakeholders', project=project.name))
    else:
        flash('You don\'t have permission to access this project.', 'error')
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
    if project is None:
        return render_template('projects.html',
                               title=name,
                               form=form,
                               form2=form2,
                               form3=form3,
                               project=None,
                               user=g.user)
    elif g.user in project.editors or project.public:
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


@app.route('/project/<project>/public')
@login_required
def make_public_project(project):
    project = Projects.query.filter_by(name=project).first()
    if g.user.id == project.creator:
        if project.public:
            project.public = False
            db.session.commit()
        else:
            project.public = True
            db.session.commit()
        return redirect(url_for('projects', name=project.name))
    else:
        flash('You don\'t have permission to do that', 'error')
        return redirect(url_for('projects', name=project.name))


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
            # assumptions = Assumptions.query.filter_by(project_id=project.id, hg_id=hg.id).all()
            # for ass in assumptions:
            #     Assumptions.query.filter_by(id=ass.id).delete()
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
        choices = [(sh.id, sh.nickname) for sh in Stakeholder.query.filter_by(project_id=project.id)]
        choices.insert(0, ('x', 'No Stakeholder'))
        # choices.insert(1, (0, 'Add a new Component'))
        setattr(GoodsForm, 'stakeholders_list',
                SelectField('Select a Stakeholder to whom the asset is important', default='x', choices=choices))
        form = GoodsForm()
        if request.method == 'POST' and request.form.get('add'):
            if form.goods.data is not '':
                gd = Good.query.filter_by(description=form.goods.data, project_id=project.id).first()
                if gd is None:
                    good = Good(description=form.goods.data, project_id=project.id)
                    db.session.add(good)
                    db.session.commit()
                    flash('Good Added to the Database', 'succ')
                    if form.stakeholders_list.data is not 'x':
                        stakeholder = Stakeholder.query.filter_by(project_id=project.id, id=form.stakeholders_list.data).first()
                        gud = Good.query.filter_by(project_id=project.id, description=form.goods.data).first()
                        gud.add_stakeholder(stakeholder)
                        db.session.commit()
                    return redirect(url_for('goods', project=project.name))
                else:
                    flash('Good already exists', 'error')
            else:
                flash('Asset field can\'t be empty', 'error')
                return redirect(url_for('goods', project=project.name))
        elif request.method == 'POST' and request.form.get('update'):
            chbx_list = request.form.getlist('chbpx')
            # print('check box list {}'.format(chbx_list))
            goods = Good.query.filter_by(project_id=project.id).all()
            current_stakeholders_list = []
            for gd in goods:
                for sh in gd.stakeholders:
                    if sh in gd.stakeholders:
                        curr_sh = '{}-{}'.format(gd.id, sh.id)
                        current_stakeholders_list.append(curr_sh)
            # print('current stakeholders list {}'.format(current_stakeholders_list))
            for item in chbx_list:
                if item in current_stakeholders_list:
                    current_stakeholders_list.remove(item)
                good_id, stakeholder_id = item.split('-')
                gud = Good.query.filter_by(id=good_id).first()
                sth = Stakeholder.query.filter_by(id=stakeholder_id).first()
                gud.add_stakeholder(sth)
                db.session.commit()
            for remaining in current_stakeholders_list:
                rem_good_id, rem_stakeholder_id = remaining.split('-')
                rem_gud = Good.query.filter_by(id=rem_good_id).first()
                rem_sth = Stakeholder.query.filter_by(id=rem_stakeholder_id).first()
                rem_gud.remove_stakeholder(rem_sth)
                db.session.commit()
            # print('final stakeholder list {}'.format(current_stakeholders_list))
            flash('Assets and Stakeholders Matrix Updated', 'succ')
            return redirect(url_for('goods', project=project.name))
        goods = Good.query.filter_by(project_id=project.id).all()
        return render_template('goods.html',
                               title=project.name,
                               form=form,
                               goods=goods,
                               project=project)
    else:
        flash('You don\'t have permission to access this project', 'error')
        return redirect(url_for('index'))


@app.route('/removeg/<project>/<desc>', methods=['GET', 'POST'])
@login_required
def removeg(project, desc):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        asset = Good.query.filter_by(description=desc, project_id=project.id).first()
        for sh in asset.stakeholders:
            asset.remove_stakeholder(sh)
            db.session.commit()
        Good.query.filter_by(description=desc, project_id=project.id).delete()
        db.session.commit()
        flash('Good "{}" removed'.format(desc), 'error')
        return redirect(url_for('goods', project=project.name))
    else:
        flash('You don\'t have permission to access this project', 'error')
        return redirect(url_for('index'))


@app.route('/functional_req/<project>', methods=['GET', 'POST'])
@login_required
def functional_req(project):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        choices = [(sub.id, sub.name) for sub in SubService.query.filter_by(project_id=project.id)]
        choices.insert(0, ('x', 'No Component'))
        choices.insert(1, (0,'Add a new Component'))
        setattr(FunctionalRequirementsForm, 'subservice_multiple_select',
                SelectField('Add a Component for the Functional Requirement', default='x', choices=choices))
        form = FunctionalRequirementsForm()

        if request.method == 'POST' and request.form.get('freqbtn'):
            if form.freq.data is not '':
                if form.subservice_multiple_select.data is not 'x' and form.subservice_multiple_select.data is not '0':
                    sub = SubService.query.filter_by(id=form.subservice_multiple_select.data).first()
                    fr = FunctionalRequirement.query.filter_by(description=form.freq.data, project_id=project.id).first()
                    if fr is None:
                        freq = FunctionalRequirement(description=form.freq.data, project_id=project.id)
                        db.session.add(freq)
                        db.session.commit()
                        flash('Functional Requirement Added to the Database', 'succ')

                        fr2 = FunctionalRequirement.query.filter_by(description=form.freq.data, project_id=project.id).first()
                        fr2.add_serv(sub)
                        db.session.commit()
                    else:
                        flash('Functional Requirement already exists', 'error')
                else:
                    fr = FunctionalRequirement.query.filter_by(description=form.freq.data,
                                                               project_id=project.id).first()
                    if fr is None:
                        freq = FunctionalRequirement(description=form.freq.data, project_id=project.id)
                        db.session.add(freq)
                        db.session.commit()
                        flash('Functional Requirement Added to the Database', 'succ')
                    else:
                        flash('Functional Requirement already exists', 'error')
            else:
                flash('Functional Requirement field can\'t be empty', 'error')
            if form.subserv.data is not '' and form.subservice_multiple_select.data == '0':
                sub = SubService.query.filter_by(name=form.subserv.data, project_id=project.id).first()
                if sub is None:
                    sb = SubService(name=form.subserv.data, project_id=project.id)
                    db.session.add(sb)
                    db.session.commit()
                    flash('Component Added to the Database', 'succ')

                    added_sub = SubService.query.filter_by(name=form.subserv.data, project_id=project.id).first()
                    fr = FunctionalRequirement.query.filter_by(description=form.freq.data, project_id=project.id).first()
                    fr.add_serv(added_sub)
                    db.session.commit()
                else:
                    flash('Component Already Exists', 'error')

            return redirect(url_for('functional_req', project=project.name))
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
        flash('You don\'t have permission to access this project.', 'error')
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
        flash('You don\'t have permission to access this project.', 'error')
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
        flash('Component "{}" removed'.format(name), 'error')
        return redirect(url_for('functional_req', project=project.name))
    else:
        flash('You don\'t have permission to access this project.', 'error')
        return redirect(url_for('index'))


# @app.route('/removeass/<project>/<id>', methods=['GET', 'POST'])
# @login_required
# def removeass(project, id):
#     project = Projects.query.filter_by(name=project).first()
#     if g.user in project.editors:
#         Assumptions.query.filter_by(project_id=project.id, id=id).delete()
#         db.session.commit()
#     return redirect(url_for('assumptions', project=project.name))


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
                if hgoal.cb_value and not hgoal.extra_hg:
                    db_values.append(hgoal.cb_value)

            for val in db_values:
                if val not in current_req:
                    HardGoal.query.filter_by(cb_value=val, project_id=project.id).delete()
                    db.session.commit()
                    flash('Item(s) removed from the database', 'error')

            return redirect(url_for('hard_goals', project=project.name))

        elif request.method == 'POST' and request.form.get('sub2') == 'pressed2':
            callback_list = request.form.getlist('hglist')
            if callback_list:
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
                    hg = HardGoal.query.filter_by(project_id=project.id, description=remaining_hg).first()
                    if hg:
                        if not hg.extra_hg:
                            for bbm in hg.bbmechanisms:
                                hg.remove_bb(bbm)
                            if hg.original_hg:
                                HardGoal.query.filter_by(id=hg.original_hg).delete()
                        HardGoal.query.filter_by(project_id=project.id, description=remaining_hg).delete()
                    db.session.commit()
            else:
                for remaining_hg in hardgs:
                    hg = HardGoal.query.filter_by(project_id=project.id, description=remaining_hg).first()
                    if hg:
                        if not hg.extra_hg:
                            for bbm in hg.bbmechanisms:
                                hg.remove_bb(bbm)
                            if hg.original_hg:
                                HardGoal.query.filter_by(id=hg.original_hg).delete()
                            HardGoal.query.filter_by(project_id=project.id, description=remaining_hg).delete()
                    db.session.commit()
            project.final_assumptions = False
            db.session.commit()
            flash('Hard Goals Database Updated', 'succ')
            return redirect(url_for('hard_goals', project=project.name))

        return render_template('hardgoals.html',
                               title=project.name,
                               project=project,
                               hardgs=hardgs)
    else:
        flash('You don\'t have permission to access this project.', 'error')
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
    table_list = [[], [], []]
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
                project.final_assumptions = False
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
        current_bbms = {}
        for hg in project.hard_goals:
            bbms_list = []
            for bbm in hg.bbmechanisms:
                bbms_list.append(bbm)
            current_bbms[hg.id] = bbms_list
        if request.method == 'POST':
            for index, value in request.form.items():
                hg = HardGoal.query.filter_by(id=index).first()
                bbm = BbMechanisms.query.filter_by(id=value).first()
                for key, val in current_bbms.items():
                    if key == hg.id and bbm in val:
                        val.remove(bbm)
                    elif key == hg.id and bbm not in val:
                        hg.add_bb(bbm)
                        db.session.commit()
            for key, values in current_bbms.items():
                if values:
                    for valu in values:
                        hg = HardGoal.query.filter_by(id=key).first()
                        hg.remove_bb(valu)
            project.final_assumptions = False
            db.session.commit()
            flash('Black Box Mechanisms updated', 'succ')
            return redirect(url_for('bbmech', project=project.name))
        return render_template('bbmech.html',
                               title=project.name,
                               project=project,
                               current_bbms=current_bbms,
                               bbms=bbms)
    else:
        flash('You don\'t have permission to access this project', 'error')
        return redirect(url_for('index'))


@app.route('/bbmech/<project>/assumptions', methods=['GET', 'POST'])
@login_required
def assumptions(project):
    access = check_permission(project)
    project = Projects.query.filter_by(name=project).first()
    hgoal_bbm__dict = {}
    if access:
        current_hardgoals_gen = (hg for hg in project.hard_goals if hg.description)
        current_hardgoals = []
        for hg in current_hardgoals_gen:
            current_hardgoals.append(hg)
            hgoal_bbm__dict[hg] = []
            for bbm in hg.bbmechanisms:
                hgoal_bbm__dict[hg].append(bbm)
        empty_hgoals = []
        for key, values in hgoal_bbm__dict.items():
            if not values:
                empty_hgoals.append(key)
        if request.method == 'POST' and request.form.get('sub'):

                project.final_assumptions = True
                db.session.commit()
                return redirect(url_for('assumptions', project=project.name))

        elif request.method == 'POST' and request.form.get('ehg'):
            cb_values = request.form.get('ehg').split('-')
            hg = HardGoal.query.filter_by(id=cb_values[1]).first()
            bbm = BbMechanisms.query.filter_by(id=cb_values[0]).first()
            new_hg_start = hg.description.find('during the ')
            new_hg_service = hg.description.find('ensures the ')
            new_hg = hg.description[:new_hg_service] + 'ensures the ' + bbm.extra_hg + ' ' + hg.description[new_hg_start:]
            if 'authenticity' in  bbm.extra_hg.lower():
                n_hg = HardGoal(authenticity='yes', description=new_hg, project_id=hg.project_id, priority=hg.priority, extra_hg_used=True, extra_hg=True, original_hg=hg.id)
                db.session.add(n_hg)
                db.session.commit()
                hg.extra_hg_used = True
                hg.original_hg = n_hg.id
            elif 'confidentiality' in bbm.extra_hg.lower():
                n_hg = HardGoal(confidentiality='yes', description=new_hg, project_id=hg.project_id, priority=hg.priority, extra_hg_used=True, extra_hg=True, original_hg=hg.id)
                db.session.add(n_hg)
                db.session.commit()
                hg.extra_hg_used = True
                hg.original_hg = n_hg.id
            elif 'integrity' in bbm.extra_hg.lower():
                n_hg = HardGoal(integrity='yes', description=new_hg, project_id=hg.project_id, priority=hg.priority, extra_hg_used=True, extra_hg=True, original_hg=hg.id)
                db.session.add(n_hg)
                db.session.commit()
                hg.extra_hg_used = True
                hg.original_hg = n_hg.id
            project.final_assumptions = False
            db.session.commit()
            return redirect(url_for('assumptions', project=project.name))

        return render_template('assumptions.html',
                               title=project.name,
                               project=project,
                               current_hardgoals=current_hardgoals,
                               empty_hgoals=empty_hgoals)
    else:
        flash('You don\'t have permission to access this project', 'error')
        return redirect(url_for('index'))


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


class MyModelViewBbMech(sqla.ModelView):

    # form_ajax_refs = {
    #     'assumptions': QueryAjaxModelLoader('assumptions', db.session, Assumptions, fields=['name'])
    # }

    edit_modal = True

    # can_view_details = True

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
admin.add_view(MyModelViewBbMech(BbMechanisms, db.session))
admin.add_view(MyModelView(Assumptions, db.session))


@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for,
    )