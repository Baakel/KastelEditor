# from random import sample
from flask import render_template, url_for, flash, redirect, request, session, g, abort, jsonify, Response
from editorapp import app, db, github
from flask_login import login_required
from wtforms import SelectField
# from wtforms.validators import DataRequired
from .forms import StakeHoldersForm, ProjectForm, GoodsForm, FunctionalRequirementsForm, EditorForm, AccessForm, \
    HardGoalsForm, BbmForm, FlaskForm, ActorsForm, AttackersForm, ExtraHgForm
from .models import Stakeholder, Users, Projects, Good, FunctionalRequirement,\
    HardGoal, Role, BbMechanisms,  Assumptions, SubService, freq_serv, hard_mechanism, SoftGoal, Attacker, Actors,\
    Aktoren, ActorDetails, ExtraAsset, ExtraFreqReq, ExtraSoftGoal
from flask_security import Security, SQLAlchemyUserDatastore, current_user
# from flask_security.utils import hash_password, verify_password, get_hmac
import flask_admin
# from flask_admin.contrib.sqla.form import InlineModelConverter
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers
from .schema import schema
from flask_graphql import GraphQLView
import requests
import json, re
from datetime import datetime
# import sys


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
            # if bbmech.name == 'Asymmetric or Hybrid Encryption':
            #     bbmech.extra_asset = 'Authenticity of the Encrypted Material'
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

    actors = Actors.query.first()
    if not actors:
        actors = [
            'External',
            'User',
            'Admin'
        ]
        for actor in actors:
            a = Actors(name=actor)
            db.session.add(a)
        db.session.commit()



@app.errorhandler(401)
def unauthorized_error(error):
    flash('Please log in first.')
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(400)
def bad_request(error):
    return render_template('400.html'), 400


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.before_request
def before_request():
    g.user = None
    g.project = None
    if '_user_id' in session:
        g.user = Users.query.get(session['_user_id'])
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


@app.route('/test/<id>', methods=['GET', 'POST'])
@login_required
def test(id):
    arguments = request.args.get('var', None)
    hg = HardGoal.query.filter_by(id=id).first()
    print(hg.sg_id)
    if arguments:
        print(f'found {arguments} and the urls is: {url_for("test", var="prueba", second="prueba2", _method="GET")}')
    else:
        print('no args')
        print(request.args)
    return redirect(url_for('index'))


@app.route('/help')
def help():
    return render_template('help.html',
                           title='Help')


@app.route('/<project>/export')
@app.route('/<project>/export/<backup>')
@login_required
def export(project, backup=False):
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

        soft_goals = [sg for sg in proj.soft_goals]
        soft_goals_dict = {}
        for sg in soft_goals:
            if sg.integrity:
                cbval = re.match(r"([a-zA-Z]+)([0-9]+)", sg.cb_value, re.I)
                asset = Good.query.filter_by(id=cbval.groups()[1]).first()
                soft_goals_dict[sg.integrity] = {'priority': sg.priority,
                                                 'cb_value': '{}¡{}'.format(cbval.groups()[0], asset.description)}
        for sg in soft_goals:
            if sg.authenticity:
                cbval = re.match(r"([a-zA-Z]+)([0-9]+)", sg.cb_value, re.I)
                asset = Good.query.filter_by(id=cbval.groups()[1]).first()
                soft_goals_dict[sg.authenticity] = {'priority': sg.priority,
                                                 'cb_value': '{}¡{}'.format(cbval.groups()[0], asset.description)}
        for sg in soft_goals:
            if sg.confidentiality:
                cbval = re.match(r"([a-zA-Z]+)([0-9]+)", sg.cb_value, re.I)
                asset = Good.query.filter_by(id=cbval.groups()[1]).first()
                soft_goals_dict[sg.confidentiality] = {'priority': sg.priority,
                                                 'cb_value': '{}¡{}'.format(cbval.groups()[0], asset.description)}
        project_dict['Soft Goals'] = soft_goals_dict

        attackers_list = [atk.name for atk in proj.attackers]
        attackers = [atk for atk in proj.attackers]
        attackers_sg_dict = {}
        for atk in attackers:
            sg = [sg for sg in atk.soft_goals]
            attackers_sg_dict[atk.name] = {'authenticity': [], 'integrity': [], 'confidentiality': []}
            for s in sg:
                if 'authenticity' in s.cb_value:
                    attackers_sg_dict[atk.name]['authenticity'].append(s.authenticity)
                elif 'integrity' in s.cb_value:
                    attackers_sg_dict[atk.name]['integrity'].append(s.integrity)
                elif 'confidentiality' in s.cb_value:
                    attackers_sg_dict[atk.name]['confidentiality'].append(s.confidentiality)
        project_dict['Attackers'] = attackers_list
        project_dict['Attackers and Soft Goal Relationships'] = attackers_sg_dict

        actors = [act for act in proj.actors]
        actors_dictionary = {}
        for actor in actors:
            attackers = [atk.name for atk in actor.attackers]
            details = [{'component': dets.service_id, 'role': dets.role_id} for dets in actor.details]
            actors_dictionary[actor.name] = {}
            actors_dictionary[actor.name]['attackers'] = attackers
            actors_dictionary[actor.name]['details'] = details

            for i, deeds in enumerate(actors_dictionary[actor.name]['details']):
                component = SubService.query.filter_by(id=deeds['component']).first()
                actors_dictionary[actor.name]['details'][i]['component'] = component.name

                role = Actors.query.filter_by(id=deeds['role']).first()
                actors_dictionary[actor.name]['details'][i]['role'] = role.name
        project_dict['Actors'] = actors_dictionary

        hard_goals = [hg for hg in proj.hard_goals if hg.description]
        hard_goals_dict = {}
        hard_bb_mechanism_relationship = {'base': {},
                                          'status': {}}
        for hg in hard_goals:
            if hg.authenticity:
                if hg.original_hg:
                    original = HardGoal.query.filter_by(id=hg.original_hg).first()
                    if original is not None:
                        hard_goals_dict[hg.description] = {
                            'authenticity': hg.authenticity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                            'extra_hg': hg.extra_hg, 'original_hg': original.description, 'component_id': SubService.query.filter_by(id=hg.component_id).first().name,
                            'freq_id': FunctionalRequirement.query.filter_by(id=hg.freq_id).first().description,
                            'sg_id': SoftGoal.query.filter_by(id=hg.sg_id).first().authenticity,
                            'unique_id': hg.unique_id}
                    else:
                        hard_goals_dict[hg.description] = {
                            'authenticity': hg.authenticity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                            'extra_hg': hg.extra_hg, 'original_hg': None, 'component_id': SubService.query.filter_by(id=hg.component_id).first().name,
                            'freq_id': FunctionalRequirement.query.filter_by(id=hg.freq_id).first().description,
                            'sg_id': SoftGoal.query.filter_by(id=hg.sg_id).first().authenticity,
                            'unique_id': hg.unique_id}
                else:
                    hard_goals_dict[hg.description] = {
                        'authenticity': hg.authenticity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                        'extra_hg': hg.extra_hg, 'original_hg': None, 'component_id': SubService.query.filter_by(id=hg.component_id).first().name,
                        'freq_id': FunctionalRequirement.query.filter_by(id=hg.freq_id).first().description,
                        'sg_id': SoftGoal.query.filter_by(id=hg.sg_id).first().authenticity,
                        'unique_id': hg.unique_id}
            if hg.confidentiality:
                if hg.original_hg:
                    original = HardGoal.query.filter_by(id=hg.original_hg).first()
                    if original is not None:
                        hard_goals_dict[hg.description] = {
                            'confidentiality': hg.confidentiality, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                            'extra_hg': hg.extra_hg, 'original_hg': original.description, 'component_id': SubService.query.filter_by(id=hg.component_id).first().name,
                            'freq_id': FunctionalRequirement.query.filter_by(id=hg.freq_id).first().description,
                            'sg_id': SoftGoal.query.filter_by(id=hg.sg_id).first().confidentiality,
                            'unique_id': hg.unique_id}
                    else:
                        hard_goals_dict[hg.description] = {
                            'authenticity': hg.authenticity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                            'extra_hg': hg.extra_hg, 'original_hg': None, 'component_id': SubService.query.filter_by(id=hg.component_id).first().name,
                            'freq_id': FunctionalRequirement.query.filter_by(id=hg.freq_id).first().description,
                            'sg_id': SoftGoal.query.filter_by(id=hg.sg_id).first().confidentiality,
                            'unique_id': hg.unique_id}
                else:
                    hard_goals_dict[hg.description] = {
                        'confidentiality': hg.confidentiality, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                        'extra_hg': hg.extra_hg, 'original_hg': None, 'component_id': SubService.query.filter_by(id=hg.component_id).first().name,
                        'freq_id': FunctionalRequirement.query.filter_by(id=hg.freq_id).first().description,
                        'sg_id': SoftGoal.query.filter_by(id=hg.sg_id).first().confidentiality,
                        'unique_id': hg.unique_id}
            if hg.integrity:
                if hg.original_hg:
                    original = HardGoal.query.filter_by(id=hg.original_hg).first()
                    if original is not None:
                        hard_goals_dict[hg.description] = {
                            'integrity': hg.integrity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                            'extra_hg': hg.extra_hg, 'original_hg': original.description, 'component_id': SubService.query.filter_by(id=hg.component_id).first().name,
                            'freq_id': FunctionalRequirement.query.filter_by(id=hg.freq_id).first().description,
                            'sg_id': SoftGoal.query.filter_by(id=hg.sg_id).first().integrity,
                            'unique_id': hg.unique_id}
                    else:
                        hard_goals_dict[hg.description] = {
                            'authenticity': hg.authenticity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                            'extra_hg': hg.extra_hg, 'original_hg': None, 'component_id': SubService.query.filter_by(id=hg.component_id).first().name,
                            'freq_id': FunctionalRequirement.query.filter_by(id=hg.freq_id).first().description,
                            'sg_id': SoftGoal.query.filter_by(id=hg.sg_id).first().integrity,
                            'unique_id': hg.unique_id}
                else:
                    hard_goals_dict[hg.description] = {
                        'integrity': hg.integrity, 'priority': hg.priority, 'extra_hg_used': hg.extra_hg_used,
                        'extra_hg': hg.extra_hg, 'original_hg': None, 'component_id': SubService.query.filter_by(id=hg.component_id).first().name,
                        'freq_id': FunctionalRequirement.query.filter_by(id=hg.freq_id).first().description,
                        'sg_id': SoftGoal.query.filter_by(id=hg.sg_id).first().integrity,
                        'unique_id': hg.unique_id}
            for bbm in hg.bbmechanisms:
                # hard_bb_mechanism_relationship[hg.description] = bbm.name
                hard_bb_mechanism_relationship['base'].update({hg.description: bbm.name})
                hard_bb_mechanism_relationship['status'].update({hg.description: hg.correctly_implemented})
        project_dict['Hard Mechanism Relationship']  = hard_bb_mechanism_relationship
        project_dict['Hard Goals'] = hard_goals_dict

        black_box_mechanisms_dict = {}
        for bb in BbMechanisms.query.all():
            ea_list = []
            for e_a in bb.extra_assets:
                ea_list.append(e_a.name)
            esg_list = []
            for e_sg in bb.extra_softgoals:
                esg_list.append(e_sg.name)
            efr_list = []
            for e_fr in bb.extra_func_req:
                efr_list.append(e_fr.name)
            black_box_mechanisms_dict[bb.name] = {}
            black_box_mechanisms_dict[bb.name]['base'] = {'authenticity': bb.authenticity, 'integrity': bb.integrity,
                                                          'confidentiality': bb.confidentiality,
                                                          'extra_asset': ea_list,
                                                          'extra_softgoals': esg_list,
                                                          'extra_functional_requirement': efr_list}
            black_box_mechanisms_dict[bb.name]['role'] = [act.name for act in bb.against_actor]
        project_dict['Black Box Mechanisms'] = black_box_mechanisms_dict
        actor_roles = Actors.query.all()
        actor_roles_list = []
        for role in actor_roles:
            actor_roles_list.append(role.name)
        project_dict['Actor Roles'] = actor_roles_list
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
        resp = jsonify(project_dict)
        if backup:
            resp.headers['Content-disposition'] = 'attachment; filename={}-backup.json'.format(proj.name.replace(' ', '_'))
        else:
            resp.headers['Content-disposition'] = 'attachment; filename={}.json'.format(proj.name)
        return resp
    else:
        flash('You don\'t have permission to do that', 'error')
        return redirect(url_for('index'))


@app.route('/import', methods=['POST', 'GET'])
@app.route('/import/<dele>', methods=['POST', 'GET', 'DELETE'])
@login_required
def import_project(dele=False):
        # file = request.files['inputFile']
        # read_file = file.read()
        # decoded_file = read_file.decode('utf-8')
        # json_data = json.loads(decoded_file)
        # original_project = Projects.query.filter_by(name=json_data['Project']).first()
        # if original_project:
        #     print(original_project)
    try:
        if dele:
            project = Projects.query.filter_by(name=dele).first()
            stakeholders = Stakeholder.query.filter_by(project_id=project.id).all()
            for stkhld in stakeholders:
                db.session.delete(stkhld)
                db.session.commit()
            softgoals = SoftGoal.query.filter_by(project_id=project.id).all()
            for sftgl in softgoals:
                db.session.delete(sftgl)
                db.session.commit()
            functional_reqs = FunctionalRequirement.query.filter_by(project_id=project.id).all()
            for fr in functional_reqs:
                db.session.delete(fr)
                db.session.commit()
            services = SubService.query.filter_by(project_id=project.id).all()
            for serv in services:
                db.session.delete(serv)
                db.session.commit()
            goods = Good.query.filter_by(project_id=project.id).all()
            for gd in goods:
                db.session.delete(gd)
                db.session.commit()
            attackers = Attacker.query.filter_by(project_id=project.id).all()
            for atk in attackers:
                for sg in atk.soft_goals:
                    atk.remove_sg(sg)
                db.session.delete(atk)
                db.session.commit()
            actors = Aktoren.query.filter_by(project_id=project.id).all()
            for act in actors:
                for atk in act.attackers:
                    act.remove_atk(atk)
                for det in act.details:
                    ActorDetails.query.filter_by(id=det.id).delete()
                db.session.delete(act)
                db.session.commit()
            hard_goals = HardGoal.query.filter_by(project_id=project.id).all()
            for hg in hard_goals:
                for bbm in hg.bbmechanisms:
                    for e_a in bbm.extra_assets:
                        ExtraAsset.query.filter_by(id=e_a.id).delete()
                    for e_fr in bbm.extra_func_req:
                        ExtraFreqReq.query.filter_by(id=e_fr.id).delete()
                    for e_sg in bbm.extra_softgoals:
                        ExtraSoftGoal.query.filter_by(id=e_sg.id).delete()
                    hg.remove_bb(bbm)
                db.session.delete(hg)
                db.session.commit()
            for editor in project.editors:
                u = editor.revoke_access(project)
                db.session.add(u)
                db.session.commit()
            db.session.delete(project)
            db.session.commit()

        json_data = session['json_data']
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
        g.user.contribute(curr_project)
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
                cbval = json_data['Soft Goals'][soft_goals]['cb_value'].split('¡')
                asset = Good.query.filter_by(description=cbval[1], project_id=curr_project.id).first()
                sg = SoftGoal(priority=json_data['Soft Goals'][soft_goals]['priority'],
                              cb_value='{}{}'.format(cbval[0], asset.id),
                              authenticity=soft_goals, project_id=curr_project.id)
                db.session.add(sg)
                db.session.commit()
            elif 'confidentiality' in json_data['Soft Goals'][soft_goals]['cb_value']:
                cbval = json_data['Soft Goals'][soft_goals]['cb_value'].split('¡')
                asset = Good.query.filter_by(description=cbval[1], project_id=curr_project.id).first()
                sg = SoftGoal(priority=json_data['Soft Goals'][soft_goals]['priority'],
                              cb_value='{}{}'.format(cbval[0], asset.id),
                              confidentiality=soft_goals, project_id=curr_project.id)
                db.session.add(sg)
                db.session.commit()
            elif 'integrity' in json_data['Soft Goals'][soft_goals]['cb_value']:
                cbval = json_data['Soft Goals'][soft_goals]['cb_value'].split('¡')
                asset = Good.query.filter_by(description=cbval[1], project_id=curr_project.id).first()
                sg = SoftGoal(priority=json_data['Soft Goals'][soft_goals]['priority'],
                              cb_value='{}{}'.format(cbval[0], asset.id),
                              integrity=soft_goals, project_id=curr_project.id)
                db.session.add(sg)
                db.session.commit()
        for attacker in json_data['Attackers']:
            atk = Attacker(name=attacker, project_id=curr_project.id)
            db.session.add(atk)
            db.session.commit()
        for attacker, values in json_data['Attackers and Soft Goal Relationships'].items():
            atk = Attacker.query.filter_by(name=attacker, project_id=curr_project.id).first()
            if values['authenticity']:
                for auth in values['authenticity']:
                    sg = SoftGoal.query.filter_by(authenticity=auth, project_id=curr_project.id).first()
                    atk.add_sg(sg)
                    db.session.commit()
            if values['integrity']:
                for integ in values['integrity']:
                    sg = SoftGoal.query.filter_by(integrity=integ, project_id=curr_project.id).first()
                    atk.add_sg(sg)
                    db.session.commit()
            if values['confidentiality']:
                for conf in values['confidentiality']:
                    sg = SoftGoal.query.filter_by(confidentiality=conf, project_id=curr_project.id).first()
                    atk.add_sg(sg)
                    db.session.commit()
        for actor, values in json_data['Actors'].items():
            act = Aktoren(name=actor, project_id=curr_project.id)
            db.session.add(act)
            for attacker in values['attackers']:
                atk = Attacker.query.filter_by(name=attacker, project_id=curr_project.id).first()
                act.add_atk(atk)
            for detail in values['details']:
                component_id = SubService.query.filter_by(name=detail['component'], project_id=curr_project.id).first().id
                role_id = Actors.query.filter_by(name=detail['role']).first().id
                act_det = ActorDetails(service_id=component_id, role_id=role_id, actor_id=act.id)
                db.session.add(act_det)
            db.session.commit()
        original_hg_dict = {}
        for hard_goal in json_data['Hard Goals']:
            if json_data['Hard Goals'][hard_goal]['original_hg'] is not None:
                original_hg_dict[hard_goal] = json_data['Hard Goals'][hard_goal].pop('original_hg', None)
            # json_data['Hard Goals'][hard_goal]['original_hg']
            component_id = SubService.query.filter_by(name=json_data['Hard Goals'][hard_goal]['component_id'], project_id=curr_project.id).first()
            freq_id = FunctionalRequirement.query.filter_by(description=json_data['Hard Goals'][hard_goal]['freq_id'], project_id=curr_project.id).first()
            if "Authenticity" in json_data['Hard Goals'][hard_goal]['sg_id']:
                sg_id = SoftGoal.query.filter_by(authenticity=json_data['Hard Goals'][hard_goal]['sg_id'], project_id=curr_project.id).first()
            elif "Confidentiality" in json_data['Hard Goals'][hard_goal]['sg_id']:
                sg_id = SoftGoal.query.filter_by(confidentiality=json_data['Hard Goals'][hard_goal]['sg_id'], project_id=curr_project.id).first()
            else:
                sg_id = SoftGoal.query.filter_by(integrity=json_data['Hard Goals'][hard_goal]['sg_id'], project_id=curr_project.id).first()
            if sg_id is None:
                print(f'hard goal is {hard_goal} and json is {json_data["Hard Goals"][hard_goal]["sg_id"]}')
            json_data['Hard Goals'][hard_goal]['component_id'] = component_id.id
            json_data['Hard Goals'][hard_goal]['freq_id'] = freq_id.id
            json_data['Hard Goals'][hard_goal]['sg_id'] = sg_id.id
            if 'unique_id' not in json_data['Hard Goals'][hard_goal].keys():
                json_data['Hard Goals'][hard_goal]['unique_id'] = hg_id_gen(curr_project, freq_id, component_id, sg_id)
            # json_data['Hard Goals'][hard_goal]['unique_id'] = hg_id_gen(curr_project, freq_id, component_id, sg_id)
            hg = HardGoal(description=hard_goal, project_id=curr_project.id, **json_data['Hard Goals'][hard_goal])
            db.session.add(hg)
            db.session.commit()
        for hg, og in original_hg_dict.items():
            hard_goal = HardGoal.query.filter_by(description=hg, project_id=curr_project.id).first()
            original_hg = HardGoal.query.filter_by(description=og, project_id=curr_project.id).first()
            hard_goal.original_hg = original_hg.id
            db.session.commit()
        for role in json_data['Actor Roles']:
            r = Actors.query.filter_by(name=role).first()
            if r is None:
                new_role = Actors(name=role)
                db.session.add(new_role)
                db.session.commit()
        for bbm in json_data['Black Box Mechanisms']:
            extra_assets_list = json_data['Black Box Mechanisms'][bbm]['base']['extra_asset']
            json_data['Black Box Mechanisms'][bbm]['base'].pop('extra_asset', None)
            extra_fr_list = json_data['Black Box Mechanisms'][bbm]['base']['extra_functional_requirement']
            json_data['Black Box Mechanisms'][bbm]['base'].pop('extra_functional_requirement', None)
            extra_sg_list = json_data['Black Box Mechanisms'][bbm]['base']['extra_softgoals']
            json_data['Black Box Mechanisms'][bbm]['base'].pop('extra_softgoals', None)
            bb = BbMechanisms.query.filter_by(name=bbm, **json_data['Black Box Mechanisms'][bbm]['base']).first()
            if bb is None:
                existing_bb = BbMechanisms.query.filter_by(name=bbm).first()
                if existing_bb is None:
                    bb = BbMechanisms(name=bbm, **json_data['Black Box Mechanisms'][bbm]['base'])
                    db.session.add(bb)
                    if json_data['Black Box Mechanisms'][bbm]['role']:
                        for role in json_data['Black Box Mechanisms'][bbm]['role']:
                            r = Actors.query.filter_by(name=role).first()
                            bb.add_role(r)
                    db.session.commit()
                    for e_a in extra_assets_list:
                        ea = ExtraAsset(name=e_a, bbm_id=bb.id)
                        db.session.add(ea)
                    for e_fr in extra_fr_list:
                        efr = ExtraFreqReq(name=e_fr, bbm_id=bb.id)
                        db.session.add(efr)
                    for e_sg in extra_sg_list:
                        esg = ExtraSoftGoal(name=e_sg, bbm_id=bb.id)
                        db.session.add(esg)
                    db.session.commit()
                else:
                    existing_bb.authenticity = json_data['Black Box Mechanisms'][bbm]['base']['authenticity']
                    existing_bb.confidentiality = json_data['Black Box Mechanisms'][bbm]['base']['confidentiality']
                    existing_bb.integrity = json_data['Black Box Mechanisms'][bbm]['base']['integrity']
                    # existing_bb.extra_asset = json_data['Black Box Mechanisms'][bbm]['base']['extra_asset']
                    # existing_bb.extra_softgoal = json_data['Black Box Mechanisms'][bbm]['base']['extra_softgoal']
                    # existing_bb.extra_functional_requirement = json_data['Black Box Mechanisms'][bbm]['base']['extra_functional_requirement']
                    current_role = [role for role in existing_bb.against_actor]
                    if current_role:
                            for role in current_role:
                                existing_bb.remove_role(role)
                    if json_data['Black Box Mechanisms'][bbm]['role']:
                        for role in json_data['Black Box Mechanisms'][bbm]['role']:
                            r = Actors.query.filter_by(name=role).first()
                            existing_bb.add_role(r)
                    current_extra_assets = [str(ca) for ca in existing_bb.extra_assets]
                    for extra_asset in extra_assets_list:
                        if extra_asset in current_extra_assets:
                            continue
                        else:
                            new_extra_asset = ExtraAsset(name=extra_asset, bbm_id=existing_bb.id)
                            db.session.add(new_extra_asset)
                    current_extra_fr = [str(cfr) for cfr in existing_bb.extra_func_req]
                    for extra_fr in extra_fr_list:
                        if extra_fr in current_extra_fr:
                            continue
                        else:
                            new_extra_fr = ExtraFreqReq(name=extra_fr, bbm_id=existing_bb.id)
                            db.session.add(new_extra_fr)
                    current_extra_sg = [str(sg) for sg in existing_bb.extra_softgoals]
                    for extra_sg in extra_sg_list:
                        if extra_sg in current_extra_sg:
                            continue
                        else:
                            new_extra_sg = ExtraSoftGoal(name=extra_sg, bbm_id=existing_bb.id)
                            db.session.add(new_extra_sg)
                    db.session.commit()
            else:
                current_role = [role for role in bb.against_actor]
                if current_role:
                    for role in current_role:
                        bb.remove_role(role)
                if json_data['Black Box Mechanisms'][bbm]['role']:
                    for role in json_data['Black Box Mechanisms'][bbm]['role']:
                        r = Actors.query.filter_by(name=role).first()
                        bb.add_role(r)
                current_extra_assets = [str(ca) for ca in bb.extra_assets]
                for extra_asset in extra_assets_list:
                    if extra_asset in current_extra_assets:
                        continue
                    else:
                        new_extra_asset = ExtraAsset(name=extra_asset, bbm_id=bb.id)
                        db.session.add(new_extra_asset)
                current_extra_fr = [str(cfr) for cfr in bb.extra_func_req]
                for extra_fr in extra_fr_list:
                    if extra_fr in current_extra_fr:
                        continue
                    else:
                        new_extra_fr = ExtraFreqReq(name=extra_fr, bbm_id=bb.id)
                        db.session.add(new_extra_fr)
                current_extra_sg = [str(sg) for sg in bb.extra_softgoals]
                for extra_sg in extra_sg_list:
                    if extra_sg in current_extra_sg:
                        continue
                    else:
                        new_extra_sg = ExtraSoftGoal(name=extra_sg, bbm_id=bb.id)
                        db.session.add(new_extra_sg)
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
                if ass not in bb.assumptions:
                    bb.add_ass(ass)
        for hard_goal in json_data['Hard Mechanism Relationship']['base']:
            hg = HardGoal.query.filter_by(description=hard_goal, project_id=curr_project.id).first()
            bbm = BbMechanisms.query.filter_by(name=json_data['Hard Mechanism Relationship']['base'][hard_goal]).first()
            if bbm:
                hg.add_bb(bbm)
            db.session.commit()
        for hard_goal in json_data['Hard Mechanism Relationship']['status']:
            hg = HardGoal.query.filter_by(description=hard_goal, project_id=curr_project.id).first()
            status = json_data['Hard Mechanism Relationship']['status'][hard_goal]
            if status == 0:
                status_string = 'Correctly Implemented and Correctly Integrated'
            elif status == 1:
                status_string = 'Correctly Implemented but Incorrectly Integrated'
            elif status == 2:
                status_string = 'Incorrectly Implemented but Correctly Integrated'
            elif status == 3:
                status_string = "Incorrectly Implemented and Incorrectly Integrated"
            else:
                status_string = 'Invalid'
            hg.correctly_implemented = status
            db.session.commit()
        session.pop('json_data', None)
        return redirect(url_for('projects', name=project_name))
    except Exception as e:
        print(f'Error: {e}')
        flash('An error occurred while importing project. Information might not be complete', 'error')
        return redirect(url_for('index'))


@app.route('/uidcheck', methods=['POST','GET'])
@login_required
def check_uid():
    try:
        json_data = session['json_data']

        conflicting_ids = []
        for hg, hg_dict in json_data['Hard Goals'].items():
            if 'unique_id' not in hg_dict.keys():
                continue
            existing_hg = HardGoal.query.filter_by(unique_id=hg_dict['unique_id']).first()
            if existing_hg:
                conflicting_ids.append(existing_hg)

        if conflicting_ids:
            conf_projects = []
            for id in conflicting_ids:
                conf_proj = Projects.query.filter_by(id=id.project_id).first()
                conf_projects.append(conf_proj)

            conf_projects_set = set(conf_projects)

            if len(conf_projects_set) == 1:
                conf_project_name = conf_projects[0].name
                return render_template('conflict.html',
                                       title=f'Conflict in {json_data["Project"]}',
                                       project_name=json_data['Project'],
                                       conflict_proj=conf_project_name)
            else:
                print('More than 1 project conflict')
                flash('An error occurred, please contact the admin with error code 23420', 'error')
                return redirect(url_for('index'))
        else:
            return redirect(url_for('import_project'))
    except Exception as e:
        print(e)
        flash('error occurred while importing', 'error')
        return redirect(url_for('index'))


@app.route('/preprocess', methods=['POST'])
@login_required
def preprocess():
    try:
        file = request.files['inputFile']
        read_file = file.read()
        decoded_file = read_file.decode('utf-8')
        json_data = json.loads(decoded_file)

        # original_project = Projects.query.filter_by(name=json_data['Project']).first()

        existing_bb_list = []
        warnings = []
        for bbm in json_data['Black Box Mechanisms']:
            temp_json_data = json_data['Black Box Mechanisms'][bbm]['base'].copy()
            temp_json_data.pop('extra_asset', None)
            temp_json_data.pop('extra_functional_requirement', None)
            temp_json_data.pop('extra_softgoals', None)
            bb = BbMechanisms.query.filter_by(name=bbm, **temp_json_data).first()
            if bb is None:
                existing_bb = BbMechanisms.query.filter_by(name=bbm).first()
                if existing_bb:
                    existing_bb_list.append(existing_bb)
            else:
                roles = [role for role in bb.against_actor]
                json_roles = [role for role in json_data['Black Box Mechanisms'][bbm]['role']]
                if roles:
                    for role in roles:
                        if role.name not in json_roles:
                            existing_bb_list.append(bb)
                else:
                    if json_roles:
                        existing_bb_list.append(bb)


        for bbmecha in existing_bb_list:
            hgs = [hg for hg in bbmecha.hardgoals]
            projects = [proj.project_id for proj in hgs]
            warning = [Projects.query.filter_by(id=p).first().name for p in set(projects)]
            if warning:
                warnings.extend(warning)

        session['json_data'] = json_data
        return render_template('preprocess.html',
                               warnings=set(warnings),
                               project_name=json_data['Project'],
                               title='Importing Projecct')
    except Exception as e:
        print(e)
        flash('Please select a valid file to import', 'error')
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


@app.route('/diagram/<project>', methods=['GET', 'POST'])
@login_required
def diagram(project):
    proj = Projects.query.filter_by(name=project).first()
    if proj is None:
        flash(f'Project {project} does\'t exist.', 'error')
        return redirect(url_for('index'))
    if g.user in proj.editors or proj.public:
        return render_template('diagram.html',
                               project=proj,
                               title=proj.name)
    else:
        flash("You don't have permission to see that.", 'error')
        return redirect(url_for('index'))

@app.route('/api')
def api():
    project_name = request.args.get('project')
    functional_requirement_param = request.args.get('fr')
    actors_param = request.args.get('actors')
    sg_param = request.args.get("sgs")
    assets_param = request.args.get("assets")
    stk_param = request.args.get("stk")
    atk_param = request.args.get("atk")
    hgs_param = request.args.get("hgs")
    bbms_param = request.args.get("bbms")
    project = Projects.query.filter_by(name=project_name).first()
    data = {
        'name': project.name,
        'children': [],
        'desc': 'Project'
    }

    def get_status(list):
        if 3 in list:
            status = {'code': 3,
                      'message': 'BBM NOT correctly implemented'}
        elif 2 in list:
            status = {'code': 2,
                      'message': "BBM NOT correctly implemented"}
        elif 1 in list:
            status = {'code': 1,
                      'message': "BBM correctly implemented"}
        elif 0 in list:
            status = {'code': 0,
                      'message': "BBM correctly implemented"}
        else:
            status = {'code': 4,
                      'message': "BBM not analyzed"}
        return status

    def add_actors(parent):

        for actor in project.actors:
            roles = [role for role in actor.details if role.service_id == parent['id']]
            for role in roles:
                level = Actors.query.filter_by(id=role.role_id).first()
                data = {
                    'name': actor.name,
                    'children': [],
                    'comp': parent['id'],
                    'sg_id': False,
                    'desc': f'Actor access level: {level.name}'
                }
                parent['children'].append(data)
        return parent

    def add_components(parent):
        for comp in project.sub_services:
            hgs_status = set([hg.correctly_implemented for hg in HardGoal.query.filter_by(component_id=comp.id).all()])
            status = get_status(hgs_status)
            data = {
                'name': comp.name,
                'children': [],
                'id': comp.id,
                'desc': 'Component',
                'status': status['code']
            }
            parent['children'].append(data)
        return parent

    def add_softgoals(parent):
        sgs_allowed = [(hg.sg_id, hg.component_id) for hg in project.hard_goals]
        for softgoal in project.soft_goals:
            hgs_status = set([hg.correctly_implemented for hg in HardGoal.query.filter_by(sg_id=softgoal.id,
                                                                                          component_id=parent[
                                                                                              'id']).all()])
            status = get_status(hgs_status)
            if softgoal.authenticity:
                data = {
                    'name': softgoal.authenticity,
                    'children': [],
                    'goal': 'auth',
                    'sg_id': softgoal.id,
                    'hg_id': False,
                    'comp': parent['id'],
                    'desc': 'Soft Goal',
                    'status': status['code']
                }
            elif softgoal.confidentiality:
                data = {
                    'name': softgoal.confidentiality,
                    'children': [],
                    'goal': 'conf',
                    'hg_id': False,
                    'sg_id': softgoal.id,
                    'comp': parent['id'],
                    'desc': 'Soft Goal',
                    'status': status['code']
                }
            else:
                data = {
                    'name': softgoal.integrity,
                    'children': [],
                    'goal': 'integ',
                    'hg_id': False,
                    'sg_id': softgoal.id,
                    'comp': parent['id'],
                    'desc': 'Soft Goal',
                    'status': status['code']
                }
            if (softgoal.id, parent['id']) in sgs_allowed:
                parent['children'].append(data)
        return parent

    def add_stakeholders(parent):
        if parent['sg_id']:
            sg = SoftGoal.query.filter_by(id=parent['sg_id']).first()

            match = re.match(r"([a-z]+)([0-9]+)", sg.cb_value, re.I)
            asset = Good.query.filter_by(id=match[2]).first()
            for stakeholder in asset.stakeholders:
                data = {
                    'name': stakeholder.nickname,
                    'children': [],
                    'sg_id': None,
                    'hg_id': False,
                    'desc': 'Stakeholder'
                }
                parent['children'].append(data)

    def add_assets(parent):
        if not parent['sg_id']:
            return parent

        sg = SoftGoal.query.filter_by(id=parent['sg_id']).first()
        match = re.match(r"([a-z]+)([0-9]+)", sg.cb_value, re.I)
        asset = Good.query.filter_by(id=match[2]).first()
        data = {
            'name': asset.description,
            'children': [],
            'sg_id': None,
            'hg_id': False,
            'desc': 'Asset'
        }
        parent['children'].append(data)

    def add_attackers(parent):
        if not parent['sg_id']:
            return parent
        for attacker in project.attackers:
            ids = [sg.id for sg in attacker.soft_goals]
            if parent['sg_id'] in ids:
                data = {
                    'name': attacker.name,
                    'children': [],
                    'sg_id': False,
                    'hg_id': False,
                    'desc': 'Attacker'
                }
                parent['children'].append(data)

    def add_functional_requirements(parent):
        if not parent['sg_id']:
            return parent

        hgs = HardGoal.query.filter_by(sg_id=parent['sg_id'], component_id=parent['comp']).all()
        for fr in project.functional_req:
            for hg in hgs:
                if fr.id == hg.freq_id:
                    data = {
                        'name': fr.description,
                        'children': [],
                        'sg_id': None,
                        'hg_id': hg.id,
                        'desc': 'Functional Requirement',
                        'status': hg.correctly_implemented
                    }
                    parent['children'].append(data)
        return parent

    def add_hardgoals(parent):
        # for hardgoal in project.hard_goals:
        #     if hardgoal.sg_id == parent['sg_id'] and hardgoal.component_id == parent['comp']:
        #         data = {
        #             'name': hardgoal.description,
        #             'children': [
        #                 {'name': hardgoal.bbmechanisms[0].name,
        #                  'children': []}
        #             ]
        #         }
        #         parent['children'].append(data)
        if parent['hg_id']:
            hardgoal = HardGoal.query.filter_by(id=parent['hg_id']).first()
            data = {
                'name': hardgoal.description,
                'children': [
                    {
                        'name': hardgoal.bbmechanisms[0].name,
                        'children': [],
                        'desc': 'BBM',
                        'status': hardgoal.correctly_implemented
                    }
                ],
                'desc': 'Hard Goal',
                'status': hardgoal.correctly_implemented
            }
            parent['children'].append(data)
        elif parent['sg_id']:
            hardgoals = HardGoal.query.filter_by(sg_id=parent['sg_id']).all()
            for hg in hardgoals:
                if parent['comp'] == hg.component_id:
                    data = {
                        'name': hg.description,
                        'children': [
                            {
                                'name': hg.bbmechanisms[0].name,
                                'children': [],
                                'desc': 'BBM',
                                'status': hg.correctly_implemented
                            }
                        ],
                        'desc': 'Hard Goal',
                        'status': hg.correctly_implemented
                    }
                    parent['children'].append(data)
        return parent

    project_dict = add_components(data)
    for comp in project_dict['children']:
        if sg_param:
            comp_dict = add_softgoals(comp)
            for sg in comp_dict['children']:
                if functional_requirement_param:
                    sg_dict = add_functional_requirements(sg)
                    for fr in sg_dict['children']:
                        if fr['hg_id']:
                            if hgs_param:
                                sgs_dict = add_hardgoals(fr)
                                if not bbms_param:
                                    for hgs_dict in sgs_dict['children']:
                                        hgs_dict['children'] = []
                else:
                    if hgs_param:
                        sgs_dict = add_hardgoals(sg)
                        if not bbms_param:
                            for hgs_dict in sgs_dict['children']:
                                hgs_dict['children'] = []
                if assets_param:
                    add_assets(sg)
                if stk_param:
                    add_stakeholders(sg)
                if atk_param:
                    add_attackers(sg)
                # sg_dict = add_hardgoals(sg)
        if actors_param:
            add_actors(comp)

    # print(data)
    return jsonify(data)

@app.route('/testdata')
def testdata():
    proj = request.args.get('project')
    stakeholders = request.args.get('stakeholders', False)
    attackers = request.args.get('attackers', False)
    actors = request.args.get('actors', False)
    bbms = request.args.get('bbms', False)
    sgs = request.args.get('sgs', False)
    hgs = request.args.get('hgs', False)
    assets = request.args.get('assets', False)
    functional_reqs = request.args.get('freq', False)
    req = [stakeholders, attackers, actors, bbms, sgs, hgs]
    # for i, r in enumerate(req):
    #     print(f'r is {r} and iter is {i}')
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
            'drawLineThrough': True,
            'siblingSeparation': 100,
            'subTeeSeparation': 60,
            'levelSeparation': 15,
            'nodeAlign': 'BOTTOM'
        },
        'nodeStructure': {
            'text': {'name': project.name, 'desc': 'Project'},
            'children': [

            ]
        }

    }

    def component_dict(parent, project):
        for comp in project.sub_services:
            status = 1
            found_2 = False
            found_4 = False
            found_1 = False
            aok = False
            for hg in comp.hard_goals:
                if hg.correctly_implemented is None or hg.correctly_implemented == 0:
                    aok = True
                elif hg.correctly_implemented == 1:
                    found_1 = True
                elif hg.correctly_implemented == 2:
                    found_2 = True
                elif hg.correctly_implemented == 3:
                    status = 3
                    break
                else:
                    found_4 = True
            else:
                if found_1:
                    status = 1
                elif found_2:
                    status = 2
                elif found_4:
                    status = 4
                else:
                    status = 0
            comp_dict = {'text': {'name': comp.name, 'desc': 'Component'},
                         'children': [],
                         'HTMLclass': 'blue',
                         'connectors': {'style': {'stroke-width': 1}},
                         'collapsable': True}
            # if status == 2:
            #     comp_dict['text']['desc'] = 'Component (Imp Error)'
            #     comp_dict['HTMLclass'] = 'imp-error'
            # elif status == 0:
            #     comp_dict['text']['desc'] = 'Component (Not Implemented)'
            #     comp_dict['HTMLclass'] = 'not-imp'
            get_status_format(comp_dict, status, "Component")
            parent['children'].append(comp_dict)
        return parent

    def assets_dict(parent, project):
        sg = SoftGoal.query.filter_by(id=parent['id']).first()
        for ass in project.goods:
            match = re.match(r"([a-z]+)([0-9]+)", sg.cb_value, re.I)
            items = None
            if match:
                items = match.groups()
                items = int(items[1])
            if ass.id == items:
                ass_dict = {'text': {'name': ass.description, 'desc': 'Asset'},
                            'children': [],
                            'HTMLclass': 'leaf',
                            'collapsable': False,
                            'connectors': {'style': {'stroke-width': 1}}}
                # status = 1
                # for hg in sg.hard_goals:
                #     if hg.correctly_implemented is None or hg.correctly_implemented == 0:
                #         status = 0
                #     elif hg.correctly_implemented == 2:
                #         status = 2
                # if status == 2 and 'imp-error' in parent['HTMLclass']:
                #     get_status_format(ass_dict, status, "Asset")
                # elif status == 0 and 'not-imp' in parent['HTMLclass']:
                #     get_status_format(ass_dict, status, "Asset")
                get_status_format(ass_dict, parent['sg_status'], "Asset")
                parent['children'].append(ass_dict)

    def sgs_dictionary(parent, project):
        for sg in project.soft_goals:
            if sg.authenticity:
                description = sg.authenticity
            elif sg.confidentiality:
                description = sg.confidentiality
            elif sg.integrity:
                description = sg.integrity
            else:
                description = 'SG corrupted'

            hgs_list = [hg.component_id for hg in sg.hard_goals]
            components = [SubService.query.filter_by(id=comp).first().name for comp in hgs_list]

            if parent['text']['name'] in components:
                found_2 = False
                found_1 = False
                found_4 = False
                aok = False
                for hg in sg.hard_goals:
                    if hg.correctly_implemented is None or hg.correctly_implemented == 0 and SubService.query.filter_by(id=hg.component_id).first().name == parent['text']['name']:
                        aok = True
                    elif hg.correctly_implemented == 1 and SubService.query.filter_by(
                            id=hg.component_id).first().name == parent['text']['name']:
                        found_1 = True
                    elif hg.correctly_implemented == 2 and SubService.query.filter_by(id=hg.component_id).first().name == parent['text']['name']:
                        found_2 = True
                    elif hg.correctly_implemented == 3 and SubService.query.filter_by(
                        id=hg.component_id).first().name == parent['text']['name']:
                        status = 3
                        break
                    elif (hg.correctly_implemented != 2 and hg.correctly_implemented != 0 and hg.correctly_implemented != 1 and hg.correctly_implemented != 3) and SubService.query.filter_by(
                        id=hg.component_id).first().name == parent['text']['name']:
                        found_4 = True
                else:
                    if found_1:
                        status = 1
                    elif found_2:
                        status = 2
                    elif found_4:
                        status = 4
                    else:
                        status = 0
                sg_dict = {'text': {'name': description, 'desc': 'Soft Goal'},
                           'children': [],
                           'HTMLclass': 'yellow',
                           'collapsable': True,
                           'connectors': {'style': {'stroke-width': 1}},
                           'parent': parent['text']['name'],
                           'id': sg.id,
                           'sg_status': status}

                get_status_format(sg_dict, status, "Soft Goal")
                parent['children'].append(sg_dict)
        return parent

    def freq_dict(parent, project):
        for hg in project.hard_goals:
            comp = SubService.query.filter_by(id=hg.component_id).first()
            if hg.sg_id == parent['id'] and parent['parent'] == comp.name:
                freq = FunctionalRequirement.query.filter_by(id=hg.freq_id).first()
                status = 1
                if hg.correctly_implemented is None or hg.correctly_implemented == 0:
                    status = 0
                elif hg.correctly_implemented == 2:
                    status = 2
                elif hg.correctly_implemented == 3:
                    status = 3
                elif hg.correctly_implemented == 1:
                    status = 1
                else:
                    status = 4
                freq_dict = {'text': {'name': freq.description, 'desc': 'Functional Requirement'},
                             'children': [],
                             'HTMLclass': 'aqua',
                             'collapsable': True,
                             'connectors': {'style': {'stroke-width': 1}},
                             'parent': parent['id'],
                             'grandpa': parent['parent']}
                get_status_format(freq_dict, status, "Functional Requirement")
                # if status == 0:
                #     # freq_dict['text']['desc'] = 'Functional Requirement (Not Implemented)'
                #     # freq_dict['HTMLclass'] = 'not-imp'
                #     # freq_dict['connectors']['style']['stroke-width'] = 3
                # elif status == 2:
                #     # freq_dict['text']['desc'] = 'Functional Requirement (Imp Error)'
                #     # freq_dict['HTMLclass'] = 'imp-error'
                #     freq_dict['connectors']['style']['stroke'] = '#ff1a1a'
                #     # freq_dict['connectors']['style']['stroke-width'] = 3
                parent['children'].append(freq_dict)
        return parent

    def hgs_dictionary2(parent, project):
        for hg in project.hard_goals:
            sg = SoftGoal.query.filter_by(id=hg.sg_id).first()
            comp = SubService.query.filter_by(id=hg.component_id).first()
            if sg.confidentiality:
                desc = sg.confidentiality
            elif sg.authenticity:
                desc = sg.authenticity
            elif sg.integrity:
                desc = sg.integrity
            else:
                desc = None
            if 'Functional Requirement' in parent['text']['desc']:
                fr = FunctionalRequirement.query.filter_by(id=hg.freq_id).first()
                desc = fr.description
            if (desc == parent['text']['name'] and parent['parent'] == comp.name) or (desc == parent['text']['name'] and parent['parent'] == sg.id and parent['grandpa'] == comp.name):
                hg_dict = {'text': {'name': hg.description, 'desc': 'Hard Goal'},
                           'children': [],
                           'HTMLclass': 'green',
                           'collapsable': True,
                           'connectors': {'style': {'stroke-width': 1}}}
                # if hg.correctly_implemented is None or hg.correctly_implemented == 0:
                #     hg_dict['text']['desc'] = 'Hard Goal (Not Implemented)'
                #     hg_dict['HTMLclass'] = 'not-imp'
                #     hg_dict['connectors']['style']['stroke-width'] = 3
                # elif hg.correctly_implemented == 2:
                #     hg_dict['text']['desc'] = 'Hard Goal (Implementation Error)'
                #     hg_dict['HTMLclass'] = 'imp-error'
                #     hg_dict['connectors']['style']['stroke-width'] = 3
                #     hg_dict['connectors']['style']['stroke'] = '#ff1a1a'
                get_status_format(hg_dict, hg.correctly_implemented, "Hard Goal")
                parent['children'].append(hg_dict)
        return parent

    def stks_dict(parent, project):
        for asset in project.goods:
            for stakeholder in asset.stakeholders:
                stk_dict = {'text': {'name': stakeholder.nickname, 'desc': 'Important to: '},
                            'children': [],
                            'HTMLclass': 'magenta',
                            'collapsable': False}
                parent['children'].append(stk_dict)

    def atks_dict(parent, project):
        for attacker in project.attackers:
            atk_dict = {'text': {'name': attacker.name, 'desc': 'At Risk From: '},
                        'children': [],
                        'HTMLclass': 'red',
                        'collapsable': False}
            parent['children'].append(atk_dict)

    def bbms_dict(parent, project):
        for hg in project.hard_goals:
            if hg.description == parent['text']['name']:
                for bbm in hg.bbmechanisms:
                    bbm_dict = {'text': {'name': bbm.name, 'desc': 'Black Box Mechanism'},
                                'children': [],
                                'HTMLclass': 'dark',
                                'connectors': {'style': {'stroke-width': 1}}}
                    # if hg.correctly_implemented is None or hg.correctly_implemented == 0:
                    #     bbm_dict['text']['desc'] = 'Black Box Mechanism (Not Implemented)'
                    #     bbm_dict['HTMLclass'] = 'not-imp'
                    # elif hg.correctly_implemented == 2:
                    #     bbm_dict['text']['desc'] = 'Black Box Mechanism (Imp Error)'
                    #     bbm_dict['HTMLclass'] = 'imp-error'
                    get_status_format(bbm_dict, hg.correctly_implemented, "Black Box Mechanism")
                    if hg.correctly_implemented == 0:
                        bbm_dict['HTMLclass'] = "green"
                        bbm_dict['text']['desc'] = "Black Box Mechanism (Correctly Implemented)"
                    elif hg.correctly_implemented == 1:
                        bbm_dict['HTMLclass'] = "green"
                        bbm_dict['text']['desc'] = "Black Box Mechanism (Correctly Implemented)"
                    elif hg.correctly_implemented == 2:
                        bbm_dict['HTMLclass'] = "imp-error"
                        bbm_dict['text']['desc'] = "Black Box Mechanism (BBM NOT correctly Implemented)"
                    elif hg.correctly_implemented == 3:
                        bbm_dict['HTMLclass'] = "imp-error"
                        bbm_dict['text']['desc'] = "Black Box Mechanism (BBM NOT correctly Implemented)"
                    else:
                        bbm_dict['text']['desc'] = "Black Box Mechanism (Not Analyzed)"
                    parent['children'].append(bbm_dict)
        return parent

    def actors_dict(parent, project):
        for actor in project.actors:
            roles_id = [detail.role_id for detail in actor.details if SubService.query.filter_by(id=detail.service_id).first().name == parent['text']['name']]
            roles = [Actors.query.filter_by(id=role).first().name for role in roles_id]

            if roles:
                actor_dict = {'text': {'name': actor.name, 'desc': f'Attacker Access Level: {roles}'},
                              'children': [],
                              'HTMLclass': 'orange',
                              'collapsable': False,
                              'connectors': {'type': 'straight'},
                              'id': None}
                parent['children'].append(actor_dict)

    def get_status_format(dict, status, desc):
        if status == 0:
            dict['HTMLclass'] = 'status-0'
            dict['connectors']['style']['stroke-width'] = 1
            dict['text']['desc'] = f"{desc} (BBM Correctly Integrated)"
            # dict['connectors']['style']['stroke'] = '#000'
        elif status == 1:
            dict['text']['desc'] = f"{desc} (BBM NOT Correctly Integrated)"
            dict['HTMLclass'] = 'imp-error status-1'
            dict['connectors']['style']['stroke-width'] = 3
            # dict['connectors']['style']['stroke'] = "#000"
        elif status == 2:
            dict['text']['desc'] = f"{desc} (BBM Correctly Integrated)"
            dict['HTMLclass'] = 'orange status-2'
            dict['connectors']['style']['stroke-width'] = 3
            # dict['connectors']['style']['stroke'] = "#ff1a1a"
        elif status == 3:
            dict['text']['desc'] = f"{desc} (BBM NOT Correctly Integrated)"
            dict['HTMLclass'] = "imp-error status-3"
            dict['connectors']['style']['stroke-width'] = 3
        elif status == 4:
            dict['text']['desc'] = f"{desc} (BBM integration not analyzed)"
            dict['HTMLclass'] = "not-analyzed"
            dict['connectors']['style']['stroke-width'] = 1
        else:
            dict['text']['desc'] = f"{desc} (STATUS ERROR)"
            dict['HTMLclass'] = 'not-imp'
        return dict

    root_dict = component_dict(dictionary['nodeStructure'], project)
    for comp in root_dict['children']:
        if actors:
            actors_dict(comp, project)
        if sgs:
            comp_dict = sgs_dictionary(comp, project)
            for sg in comp_dict['children']:
                if stakeholders and 'Soft Goal' in sg['text']['desc']:
                    stks_dict(sg, project)
                if attackers and 'Soft Goal' in sg['text']['desc']:
                    atks_dict(sg, project)
                if assets and 'Soft Goal' in sg['text']['desc']:
                    assets_dict(sg, project)
                if functional_reqs:
                    sg_dict = freq_dict(sg, project)
                    for fr in sg_dict['children']:
                        if hgs:
                            fr_dict = hgs_dictionary2(fr, project)
                            if bbms:
                                for hg in fr_dict['children']:
                                    bbms_dict(hg, project)
                else:
                    if hgs:
                        sg_dict = hgs_dictionary2(sg, project)
                        if bbms:
                            for hg in sg_dict['children']:
                                bbms_dict(hg, project)

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
    edited_sh = [k for k in request.form if k.startswith('edited')]
    if g.user in project.editors:
        if edited_sh:
            original_nickname = edited_sh[0].split('-')
            sh_list = [sh.nickname for sh in Stakeholder.query.filter_by(project_id=project.id).all()]
            if request.form.get(edited_sh[0]) not in sh_list:
                sh = Stakeholder.query.filter_by(nickname=original_nickname[1], project_id=project.id).first()
                sh.nickname = request.form.get(edited_sh[0])
                db.session.commit()
                flash('Stakeholder \'{}\' changed to \'{}\''.format(original_nickname[1], request.form.get(edited_sh[0])), 'succ')
            else:
                flash('Stakeholder \'{}\' already exists'.format(original_nickname[1]), 'error')
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
        # else:
        #     flash('You can\'t edit a Stakeholder and add a new one at the same time')
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
        return redirect(url_for('stakeholders', project=projname.name))
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
        softgoals = SoftGoal.query.filter_by(project_id=project.id).all()
        for sftgl in softgoals:
            db.session.delete(sftgl)
            db.session.commit()
        functional_reqs = FunctionalRequirement.query.filter_by(project_id=project.id).all()
        for fr in functional_reqs:
            db.session.delete(fr)
            db.session.commit()
        services = SubService.query.filter_by(project_id=project.id).all()
        for serv in services:
            db.session.delete(serv)
            db.session.commit()
        goods = Good.query.filter_by(project_id=project.id).all()
        for gd in goods:
            db.session.delete(gd)
            db.session.commit()
        attackers = Attacker.query.filter_by(project_id=project.id).all()
        for atk in attackers:
            for sg in atk.soft_goals:
                atk.remove_sg(sg)
            db.session.delete(atk)
            db.session.commit()
        actors = Aktoren.query.filter_by(project_id=project.id).all()
        for act in actors:
            for atk in act.attackers:
                act.remove_atk(atk)
            for det in act.details:
                ActorDetails.query.filter_by(id=det.id).delete()
            db.session.delete(act)
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

# @lm.user_loader
# def load_user(id):
#     return Users.query.get(int(id))


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

    session['_user_id'] = user.id
    return redirect(next_url)


@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token


@app.route('/logout')
def logout():
    session.pop('_user_id', None)
    return redirect(url_for('index'))


@app.route('/assets/<project>', methods=['GET', 'POST'])
@login_required
def goods(project):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        edited_asset = [a for a in request.form if a.startswith('edited')]
        if edited_asset:
            original_asset_name = edited_asset[0].split('-')[1]
            new_asset_name = request.form.get(edited_asset[0])
            original_asset = Good.query.filter_by(description=original_asset_name, project_id=project.id).first()
            original_asset.description = new_asset_name

            project_soft_goals = [sg for sg in project.soft_goals]
            auth_sg = [i for i in project_soft_goals if (i.authenticity and original_asset_name in i.authenticity)]
            for auth in auth_sg:
                string_to_replace = auth.authenticity
                new_string = string_to_replace.replace('{}'.format(original_asset_name), '{}'.format(new_asset_name))
                auth.authenticity = new_string
            conf_sg = [i for i in project_soft_goals if (i.confidentiality and original_asset_name in i.confidentiality)]
            for conf in conf_sg:
                string_to_replace = conf.confidentiality
                new_string = string_to_replace.replace('{}'.format(original_asset_name), '{}'.format(new_asset_name))
                conf.confidentiality = new_string
            int_sg = [i for i in project_soft_goals if (i.integrity and original_asset_name in i.integrity)]
            for integ in int_sg:
                string_to_replace = integ.integrity
                new_string = string_to_replace.replace('{}'.format(original_asset_name), '{}'.format(new_asset_name))
                integ.integrity = new_string

            project_hard_goals = [hg for hg in project.hard_goals]
            auth_hg = [i for i in project_hard_goals if (i.authenticity is not None and original_asset_name in i.authenticity)]
            for auth in  auth_hg:
                string_to_replace = auth.authenticity
                new_string = string_to_replace.replace('{}'.format(original_asset_name), '{}'.format(new_asset_name))
                auth.authenticity = new_string
            conf_hg = [i for i in project_hard_goals if (i.confidentiality is not None and original_asset_name in i.confidentiality)]
            for conf in conf_hg:
                string_to_replace = conf.confidentiality
                new_string = string_to_replace.replace('{}'.format(original_asset_name), '{}'.format(new_asset_name))
                conf.confidentiality = new_string
            integrity_hg = [i for i in project_hard_goals if (i.integrity is not None and original_asset_name in i.integrity)]
            for integ in integrity_hg:
                string_to_replace = integ.integrity
                new_string = string_to_replace.replace('{}'.format(original_asset_name), '{}'.format(new_asset_name))
                integ.integrity = new_string
            hg_description = [i for i in project_hard_goals if (i.description is not None and original_asset_name in i.description)]
            for descr in hg_description:
                string_to_replace = descr.description
                new_string = string_to_replace.replace('{}'.format(original_asset_name), '{}'.format(new_asset_name))
                descr.description = new_string

            db.session.commit()

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
                    flash('Asset Added to the Database', 'succ')
                    if form.stakeholders_list.data is not 'x':
                        stakeholder = Stakeholder.query.filter_by(project_id=project.id, id=form.stakeholders_list.data).first()
                        gud = Good.query.filter_by(project_id=project.id, description=form.goods.data).first()
                        gud.add_stakeholder(stakeholder)
                        db.session.commit()
                    return redirect(url_for('goods', project=project.name))
                else:
                    flash('Asset already exists', 'error')
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
        flash('Asset "{}" removed'.format(desc), 'error')
        return redirect(url_for('goods', project=project.name))
    else:
        flash('You don\'t have permission to access this project', 'error')
        return redirect(url_for('index'))


@app.route('/soft_goals/<project>', methods=['GET', 'POST'])
@login_required
def soft_goals(project):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        if request.method == 'POST':
            for good in project.goods:
                for softgoal in request.form.getlist('authenticity{}'.format(good.id)):
                    auth_desc = '{} of {}'.format(softgoal, good.description)
                    cb_value = 'authenticity{}'.format(good.id)
                    SG = SoftGoal.query.filter_by(authenticity=auth_desc, project_id=project.id).first()
                    if SG is None:
                        auth = SoftGoal(authenticity=auth_desc, project_id=project.id, cb_value=cb_value)
                        db.session.add(auth)
                        db.session.commit()
                        flash('Protection Goals Updated', 'succ')

                for softgoal in request.form.getlist('confidentiality{}'.format(good.id)):
                    conf_desc = '{} of {}'.format(softgoal, good.description)
                    cb_value = 'confidentiality{}'.format(good.id)
                    SG = SoftGoal.query.filter_by(confidentiality=conf_desc, project_id=project.id).first()
                    if SG is None:
                        conf = SoftGoal(confidentiality=conf_desc, project_id=project.id, cb_value=cb_value)
                        db.session.add(conf)
                        db.session.commit()
                        flash('Protection Goals Updated', 'succ')

                for softgoal in request.form.getlist('integrity{}'.format(good.id)):
                    int_desc = '{} of {}'.format(softgoal, good.description)
                    cb_value = 'integrity{}'.format(good.id)
                    SG = SoftGoal.query.filter_by(integrity=int_desc, project_id=project.id).first()
                    if SG is None:
                        integ = SoftGoal(integrity=int_desc, project_id=project.id, cb_value=cb_value)
                        db.session.add(integ)
                        db.session.commit()
                        flash('Protection Goals Updated', 'succ')

            current_req = []
            for i in request.form:
                current_req.append(i)
            softgoals = SoftGoal.query.filter_by(project_id=project.id).all()
            db_values = []
            for sgoal in softgoals:
                db_values.append(sgoal)
            for val in db_values:
                if str(val) not in current_req:
                    sg = SoftGoal.query.filter_by(cb_value=str(val), project_id=project.id).first()
                    attackers = [s for s in sg.attackers]
                    for attacker in attackers:
                        attacker.remove_sg(sg)
                    hgs = [hg for hg in sg.hard_goals]
                    for hard_goal in hgs:
                        print(f'DELETING {hard_goal}')
                        remove_hard_goal(hard_goal)
                    SoftGoal.query.filter_by(cb_value=str(val), project_id=project.id).delete()
                    db.session.commit()
                    flash('Item(s) removed from the database', 'error')

            return redirect(url_for('soft_goals', project=project.name))
        soft_g = [sg for sg in project.soft_goals]
        print(soft_g)
        return render_template('soft_goals.html',
                               title=project.name,
                               project=project,
                               soft_g=soft_g)
    else:
        flash('You don\'t have permission to access this project.', 'error')
        return redirect(url_for('index'))


@app.route('/attackers/<project>', methods=['GET', 'POST'])
@login_required
def attackers(project):
    project = Projects.query.filter_by(name=project).first()

    choices_auth = [(sg.id, sg.authenticity) for sg in SoftGoal.query.filter_by(project_id=project.id) if
                    sg.authenticity]
    choices_conf = [(sg.id, sg.confidentiality) for sg in SoftGoal.query.filter_by(project_id=project.id) if
                    sg.confidentiality]
    choices_int = [(sg.id, sg.integrity) for sg in SoftGoal.query.filter_by(project_id=project.id) if
                    sg.integrity]
    choices = [*choices_auth, *choices_conf, *choices_int]
    choices.insert(0, ('x', 'No Soft Goal'))
    setattr(AttackersForm, 'softgoals_list',
            SelectField('Select a Soft Goal the attacker aims to break', default='x', choices=choices))

    form = AttackersForm()
    if g.user in project.editors:

        if request.method == 'POST':
            if form.attacker.data is not '' and form.attacker.data is not ' ':
                attacker = Attacker.query.filter_by(name=form.attacker.data, project_id=project.id).first()
                if form.softgoals_list.data is not 'x':
                    sg = SoftGoal.query.filter_by(id=form.softgoals_list.data).first()
                else:
                    sg = None
                if attacker is None:
                    atk = Attacker(name=form.attacker.data, project_id=project.id)
                    db.session.add(atk)
                    db.session.commit()
                    if sg:
                        if not atk.alrdy_used(sg):
                            atk.add_sg(sg)
                            db.session.commit()
                    flash('Attacker "{}" added to the database'.format(form.attacker.data), 'succ')
                    return redirect(url_for('attackers', project=project.name))
                else:
                    flash('Attacker "{}" already exists'.format(form.attacker.data), 'error')
                    return redirect(url_for('attackers', project=project.name))
            else:
                flash("The attacker field can't be empty", 'error')
                return redirect(url_for('attackers', project=project.name))

        attackers = [atk for atk in project.attackers]
        return render_template('attackers.html',
                               project=project,
                               title='{} attackers'.format(project.name),
                               form=form,
                               attackers=attackers)
    else:
        flash('You don\'t have permission to access this project.', 'error')
        return redirect(url_for('index'))


@app.route('/attackers/<project>/<id>', methods=['GET', 'POST'])
@login_required
def atk(project, id):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        attacker = Attacker.query.filter_by(id=id).first()

        softgoals = [sg for sg in attacker.soft_goals]

        if request.method == 'POST':
            for item in request.form.getlist('chbpx'):
                sg_id, attacker_id = item.split('-')
                atkr = Attacker.query.filter_by(id=attacker_id).first()
                sg = SoftGoal.query.filter_by(id=sg_id).first()
                if not atkr.alrdy_used(sg):
                    atkr.add_sg(sg)
                    db.session.commit()
                else:
                    softgoals.remove(sg)
            else:
                for item in softgoals:
                    attacker.remove_sg(item)
                    db.session.commit()
            flash('Soft Goals updated', 'succ')
            return redirect(url_for('atk', project=project.name, id=attacker.id))

        return render_template('atks.html',
                               title='{} - {}'.format(project.name, attacker.name),
                               attacker=attacker,
                               project=project,
                               softgoals=softgoals)
    else:
        flash('You don\'t have permission to access this project', 'error')
        return redirect(url_for('index'))


@app.route('/stk/<project>')
@login_required
def stk(project):
    res = Stakeholder.query.filter_by(project_id=project).all()
    list_of_stk = [stkh.as_dict() for stkh in res]
    return jsonify(list_of_stk)


@app.route('/removeatt/<project>/<desc>', methods=['GET', 'POST'])
@login_required
def removeatt(project, desc):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        att = Attacker.query.filter_by(name=desc, project_id=project.id).first()
        name = att.name
        # for atk in .goods:
        #     sth.remove_stakeholder(sh)
        # db.session.commit()
        for sg in att.soft_goals:
            att.remove_sg(sg)
        Attacker.query.filter_by(name=desc, project_id=project.id).delete()
        db.session.commit()
        flash('Attacker "{}" removed'.format(name), 'error')
        return redirect(url_for('attackers', project=project.name))
    else:
        flash('You don\'t have permission to access this project.', 'error')
        return redirect(url_for('index'))


@app.route('/actors/<project>', methods=['GET', 'POST'])
@login_required
def actors(project):
    project = Projects.query.filter_by(name=project).first()
    form = ActorsForm()
    if g.user in project.editors:
        if request.method == 'POST' and form.actor.data is not '':
            actor = Aktoren.query.filter_by(name=form.actor.data, project_id=project.id).first()
            if actor is None:
                a = Aktoren(name=form.actor.data, project_id=project.id)
                db.session.add(a)
                db.session.commit()
                flash('Actor "{}" added to the database'.format(a.name), 'succ')
                return redirect(url_for('act', project=project.name, id=a.id))
            else:
                flash('Actor "{}" already in database'.format(form.actor.data), 'error')
                return redirect(url_for('actors', project=project.name))

        actors = [a for a in project.actors]
        return render_template('actors.html',
                               title='Actors of {}'.format(project.name),
                               form=form,
                               project=project,
                               actors=actors)
    else:
        flash('You don\'t have permission to access this project.', 'error')
        return redirect(url_for('index'))


@app.route('/actors/<project>/<id>', methods=['GET', 'POST'])
@login_required
def act(project, id):
    project = Projects.query.filter_by(name=project).first()
    choices = [(choice.id ,choice.name) for choice in Actors.query.all()]
    choices.insert(0, ('x', 'Choose a Role'))
    fields = {}
    for serv in SubService.query.filter_by(project_id=project.id).all():
        setattr(ActorsForm, f'serv{serv.id}',
                SelectField('Actor\'s Role', default='x', choices=choices))
    actor = Aktoren.query.filter_by(id=id, project_id=project.id).first()
    form = ActorsForm()
    if g.user in project.editors:
        if request.method == 'POST':
            form_fields = [(name, val) for name,val in request.form.items() if name.startswith('serv')]
            checkboxes = [atk.split('-')[1] for atk in request.form if atk.startswith('atk')]
            atk_indb = [atk.id for atk in actor.attackers]
            for attacker in checkboxes:
                if int(attacker) not in [_.id for _ in actor.attackers]:
                    actor.add_atk(Attacker.query.filter_by(id=attacker).first())
                    db.session.commit()
                else:
                    atk_indb.remove(int(attacker))

            for attacker in atk_indb:
                actor.remove_atk(Attacker.query.filter_by(id=attacker).first())
                db.session.commit()

            for field in form_fields:
                prev_dets = ActorDetails.query.filter_by(actor_id=id, service_id=field[0][4:]).first()
                if prev_dets is None and field[1] != 'x':
                    details = ActorDetails(actor_id=id, service_id=field[0][4:], role_id=field[1])
                    db.session.add(details)
                    db.session.commit()
                elif prev_dets and field[1] != 'x':
                    prev_dets.role_id = field[1]
                    db.session.commit()

            flash('Changes Saved', 'succ')
            return redirect(url_for('actors', project=project.name))

        services_used = [serv.service_id for serv in actor.details]
        for i in services_used:
            for details in ActorDetails.query.filter_by(actor_id=id, service_id=i).all():
                fields[f'serv{i}'] = details.role_id
        atkrs = [atkr.id for atkr in actor.attackers]
        return render_template('acts.html',
                               title='{} - {}'.format(project.name, actor.name),
                               project=project,
                               actor=actor,
                               services_used=services_used,
                               atkrs=atkrs,
                               form=form,
                               fields=fields)
    else:
        flash('You don\'t have permission to access this project.', 'error')
        return redirect(url_for('index'))


@app.route('/removeact/<project>/<name>', methods=['GET', 'POST'])
@login_required
def removeact(project, name):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        actor = Aktoren.query.filter_by(name=name, project_id=project.id).first()
        for detail in actor.details:
            ActorDetails.query.filter_by(id=detail.id).delete()
        for attacker in actor.attackers:
            actor.remove_atk(attacker)
        db.session.commit()
        Aktoren.query.filter_by(name=name, project_id=project.id).delete()
        db.session.commit()
        flash('Actor "{}" removed'.format(name), 'error')
        return redirect(url_for('actors', project=project.name))
    else:
        flash('You don\'t have permission to access this project.', 'error')
        return redirect(url_for('index'))


@app.route('/functional_req/<project>', methods=['GET', 'POST'])
@login_required
def functional_req(project):
    project = Projects.query.filter_by(name=project).first()
    if g.user in project.editors:
        edited_fr = [a for a in request.form if a.startswith('editedfr')]
        edited_sub = [a for a in request.form if a.startswith('editedsub')]
        if edited_fr:
            original_fr_name = edited_fr[0].split('-')[1]
            new_fr_name = request.form.get(edited_fr[0])
            original_fr = FunctionalRequirement.query.filter_by(description=original_fr_name, project_id=project.id).first()
            original_fr.description = new_fr_name

            project_hard_goals = [hg for hg in project.hard_goals]
            hg_description = [i for i in project_hard_goals if
                              (i.description is not None and original_fr_name in i.description)]
            for hg_desc in hg_description:
                string_to_replace = hg_desc.description
                new_string = string_to_replace.replace('{}'.format(original_fr_name), '{}'.format(new_fr_name))
                hg_desc.description = new_string

            db.session.commit()

        if edited_sub:
            original_sub_name = edited_sub[0].split('-')[1]
            new_sub_name = request.form.get(edited_sub[0])
            original_sub = SubService.query.filter_by(name=original_sub_name, project_id=project.id).first()
            original_sub.name = new_sub_name

            project_hard_goals = [hg for hg in project.hard_goals]
            hg_description = [i for i in project_hard_goals if
                              (i.description is not None and original_sub_name in i.description)]
            for hg_desc in hg_description:
                string_to_replace = hg_desc.description
                new_string = string_to_replace.replace('{}'.format(original_sub_name), '{}'.format(new_sub_name))
                hg_desc.description = new_string

            db.session.commit()


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
                    if fr is not None:
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
        hgs_list = HardGoal.query.filter_by(freq_id=fr.id, project_id=project.id).all()
        print(hgs_list)
        for hg in hgs_list:
            remove_hard_goal(hg)
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
        for details in ss.actor_details:
            db.session.delete(details)
            db.session.commit()
        hgs_list = HardGoal.query.filter_by(component_id=ss.id, project_id=project.id).all()
        for hg in hgs_list:
            remove_hard_goal(hg)
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
        hardgs = [hg.description for hg in hardgoalz]
        # for hg in hardgoalz:
        #     if hg.description is not None:
        #         hardgs.append(hg.description)
        # if request.method == 'POST' and request.form.get('subb') == 'pressed':
        #
        #     for good in project.goods:
        #         for goal in request.form.getlist('authenticity%s' % good.id):
        #             auth_desc = goal + " of " + good.description
        #             cb_value = 'authenticity%s' % good.id
        #             HG = HardGoal.query.filter_by(authenticity=auth_desc, project_id=project.id).first()
        #             if HG is None:
        #                 auth = HardGoal(authenticity=auth_desc, project_id=project.id, cb_value=cb_value)
        #                 db.session.add(auth)
        #                 db.session.commit()
        #                 flash('Protection Goals updated', 'succ')
        #
        #         for goal in request.form.getlist('confidentiality%s' % good.id):
        #             conf_desc = goal + " of " + good.description
        #             cb_value = 'confidentiality%s' % good.id
        #             HG = HardGoal.query.filter_by(confidentiality=conf_desc, project_id=project.id).first()
        #             if HG is None:
        #                 conf = HardGoal(confidentiality=conf_desc, project_id=project.id, cb_value=cb_value)
        #                 db.session.add(conf)
        #                 db.session.commit()
        #                 flash('Protection Goals updated', 'succ')
        #
        #         for goal in request.form.getlist('integrity%s' % good.id):
        #             integ_desc = goal + " of " + good.description
        #             cb_value = 'integrity%s' % good.id
        #             HG = HardGoal.query.filter_by(integrity=integ_desc, project_id=project.id).first()
        #             if HG is None:
        #                 integ = HardGoal(integrity=integ_desc, project_id=project.id, cb_value=cb_value)
        #                 db.session.add(integ)
        #                 db.session.commit()
        #                 flash('Protection Goals updated', 'succ')
        #
        #     for hgoal in project.hard_goals:
        #         test = request.form.getlist('Hgoal%s' % hgoal.id)
        #         if test and hgoal.description is None:
        #             hgoal.priority = True
        #             db.session.add(hgoal)
        #             db.session.commit()
        #         elif not test and hgoal.description is None:
        #             hgoal.priority = False
        #             db.session.add(hgoal)
        #             db.session.commit()
        #         gen = (hgl for hgl in project.hard_goals if hgl.description is not None)
        #         for hgl in gen:
        #             if test:
        #                 if hgoal.authenticity is not None and hgoal.authenticity in hgl.description:
        #                     hgl.priority = True
        #                     db.session.add(hgl)
        #                     db.session.commit()
        #                 elif hgoal.confidentiality is not None and hgoal.confidentiality in hgl.description:
        #                     hgl.priority = True
        #                     db.session.add(hgl)
        #                     db.session.commit()
        #                 elif hgoal.integrity is not None and hgoal.integrity in hgl.description:
        #                     hgl.priority = True
        #                     db.session.add(hgl)
        #                     db.session.commit()
        #             else:
        #                 if hgoal.authenticity is not None and hgoal.authenticity in hgl.description:
        #                     hgl.priority = False
        #                     db.session.add(hgl)
        #                     db.session.commit()
        #                 elif hgoal.confidentiality is not None and hgoal.confidentiality in hgl.description:
        #                     hgl.priority = False
        #                     db.session.add(hgl)
        #                     db.session.commit()
        #                 elif hgoal.integrity is not None and hgoal.integrity in hgl.description:
        #                     hgl.priority = False
        #                     db.session.add(hgl)
        #                     db.session.commit()
        #
        #     current_req = []
        #     for i in request.form:
        #         current_req.append(i)
        #     hardgoals = HardGoal.query.filter_by(project_id=project.id).all()
        #     db_values = []
        #     for hgoal in hardgoals:
        #         if hgoal.cb_value and not hgoal.extra_hg:
        #             db_values.append(hgoal.cb_value)
        #
        #     for val in db_values:
        #         if val not in current_req:
        #             HardGoal.query.filter_by(cb_value=val, project_id=project.id).delete()
        #             db.session.commit()
        #             flash('Item(s) removed from the database', 'error')
        #
        #     return redirect(url_for('hard_goals', project=project.name))

        if request.method == 'POST' and request.form.get('sub2') == 'pressed2':
            callback_list = request.form.getlist('hglist')
            if callback_list:
                for item in callback_list:
                    item_parts = item.split('¡')
                    fr = FunctionalRequirement.query.filter_by(description=item_parts[1], project_id=project.id).first()
                    comp = SubService.query.filter_by(name=item_parts[0], project_id=project.id).first()
                    if "Authenticity" in item_parts[2]:
                        sg = SoftGoal.query.filter_by(authenticity=item_parts[2], project_id=project.id).first()
                    elif "Confidentiality" in item_parts[2]:
                        sg = SoftGoal.query.filter_by(confidentiality=item_parts[2], project_id=project.id).first()
                    elif "Integrity" in item_parts[2]:
                        sg = SoftGoal.query.filter_by(integrity=item_parts[2], project_id=project.id).first()
                    else:
                        sg = None
                    final_string = '{} ensures the {} during the process of {}'.format(item_parts[0], item_parts[2], item_parts[1])
                    nhg = HardGoal.query.filter_by(description=final_string, project_id=project.id).first()
                    if nhg is None:
                        new_hg = HardGoal(project_id=project.id, description=final_string, component_id=item_parts[3], freq_id=item_parts[4], sg_id=item_parts[5], unique_id=hg_id_gen(project, fr, comp, sg))
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
                        else:
                            for bbm in hg.bbmechanisms:
                                hg.remove_bb(bbm)
                            original_hg = HardGoal.query.filter_by(id=hg.original_hg).first()
                            original_hg.extra_hg_used = None
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
                        else:
                            for bbm in hg.bbmechanisms:
                                hg.remove_bb(bbm)
                            original_hg = HardGoal.query.filter_by(id=hg.original_hg).first()
                            original_hg.extra_hg_used = None
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


def remove_hard_goal(hg):
    if hg.extra_hg:
        for bbm in hg.bbmechanisms:
            hg.remove_bb(bbm)
        original_hg = HardGoal.query.filter_by(id=hg.original_hg).first()
        if original_hg is not None:
            original_hg.extra_hg_used = None
    elif hg.extra_hg_used and hg.original_hg is None:
        hgs_gen = [hardgoal for hardgoal in HardGoal.query.filter_by(original_hg=hg.id).all()]
        for hardgoal in hgs_gen:
            db.session.delete(hardgoal)
            db.session.commit()
        for bbm in hg.bbmechanisms:
            hg.remove_bb(bbm)
    else:
        for bbm in hg.bbmechanisms:
            hg.remove_bb(bbm)
        if hg.original_hg:
            HardGoal.query.filter_by(id=hg.original_hg).delete()
    HardGoal.query.filter_by(id=hg.id).delete()
    db.session.commit()


# @app.route('/bbm/<project>', methods=['GET', 'POST'])
# @login_required
# def bbm(project):
#     project = Projects.query.filter_by(name=project).first()
#     blackbox_mechanisms = BbMechanisms.query.all()
#     choices_tuples = [(bbm.id, bbm.name) for bbm in blackbox_mechanisms]
#     table_list = [[], [], []]
#     count = 0
#     class MultipleSelects(FlaskForm):
#         pass
#
#     hgoals = HardGoal.query.filter_by(project_id=project.id).all()
#     for hg in hgoals:
#         if hg.description:
#             table_list[0].append(count)
#             count += 1
#             table_list[1].append(hg.description)
#             bbms = [bbm.id for bbm in hg.bbmechanisms]
#             if bbms:
#                 default_bbm = bbms[0]
#             else:
#                 default_bbm = 1
#             if hg.authenticity == 'yes':
#                 choices_tuples = [(bbma.id, bbma.name) for bbma in blackbox_mechanisms if bbma.authenticity]
#             if hg.confidentiality == 'yes':
#                 choices_tuples = [(bbmc.id, bbmc.name) for bbmc in blackbox_mechanisms if bbmc.confidentiality]
#             if hg.integrity == 'yes':
#                 choices_tuples = [(bbmi.id, bbmi.name) for bbmi in blackbox_mechanisms if bbmi.authenticity]
#             setattr(MultipleSelects, str(hg.id), SelectField('Desired Mechanism', choices=choices_tuples, default=default_bbm, validators=[DataRequired()]))
#             table_list[2].append('{}'.format(hg.id))
#
#     form2 = MultipleSelects()
#
#     if request.method == 'POST' and request.form.get('sub') == 'pressed':
#         for key,value in form2.data.items():
#             if key != 'csrf_token':
#                 hardG = HardGoal.query.filter_by(id=key).first()
#                 blbxm = BbMechanisms.query.filter_by(id=value).first()
#                 hardG.add_bb(blbxm)
#                 project.final_assumptions = False
#                 db.session.commit()
#         flash('Black Box mechanisms updated', 'succ')
#     elif request.method == 'POST' and request.form.get('sub') != 'pressed':
#         if request.form.get('rmbbm'):
#             data = request.form.get('rmbbm').split('-')
#             hg = HardGoal.query.filter_by(id=data[0]).first()
#             blbm = BbMechanisms.query.filter_by(id=data[1]).first()
#             hg.remove_bb(blbm)
#             db.session.commit()
#             flash('Black Box Mechanism "{}" successfully removed for Hard Goal "{}"'.format(blbm.name, hg.description), 'succ')
#             return redirect(url_for('bbm', project=project.name))
#
#     return render_template('bbm.html',
#                            title=project.name,
#                            project=project,
#                            form2=form2,
#                            blackbox_mechanisms=blackbox_mechanisms,
#                            choices_tuples=choices_tuples,
#                            table_list=table_list)


@app.route('/bbmech/<project>', methods=['POST', 'GET'])
@login_required
def bbmech(project):
    project = Projects.query.filter_by(name=project).first()
    if check_permission(project.name):
        bbms = BbMechanisms.query.all()
        current_bbms = {'bbms_list': {},
                        'components': {}}
        for hg in project.hard_goals:
            bbms_list = []
            for bbm in hg.bbmechanisms:
                bbms_list.append(bbm)
            current_bbms['bbms_list'].update({hg.id: bbms_list})
            component = SubService.query.filter_by(id=hg.component_id).first()
            roles_set = list(set([details.role_id for details in component.actor_details]))
            current_bbms['components'].update({component.id: roles_set})
        if request.method == 'POST':
            for index, value in request.form.items():
                hg = HardGoal.query.filter_by(id=index).first()
                bbm = BbMechanisms.query.filter_by(id=value).first()
                for key, val in current_bbms['bbms_list'].items():
                    if hg:
                        if key == hg.id and bbm in val:
                            # if hg.extra_hg_used and not hg.extra_hg:
                            #     match = False
                            #     # ehg = HardGoal.query.filter_by(id=hg.original_hg).first()
                            #     e_hgs = HardGoal.query.filter_by(original_hg=hg.id).all()
                            #     if bbm.extra_assets:
                            #         for e_a in bbm.extra_assets:
                            #             for ehg in e_hgs:
                            #                 if e_a in ehg.description:
                            #                     match = True
                            #                     break
                            #             else:
                            #                 continue
                            #             break
                            #         # if bbm.extra_asset in ehg.description:
                            #         #     match = True
                            #     if not match:
                            #         if ehg:
                            #             for bb in ehg.bbmechanisms:
                            #                 ehg.remove_bb(bb)
                            #             HardGoal.query.filter_by(id=hg.original_hg).delete()
                            #         hg.extra_hg_used = None
                            #         hg.original_hg = None
                            #         db.session.commit()
                            val.remove(bbm)
                        elif key == hg.id and bbm not in val:
                            hg.add_bb(bbm)
                            db.session.commit()
                            # if hg.extra_hg_used and not hg.extra_hg:
                            #     match = False
                            #     ehg = HardGoal.query.filter_by(id=hg.original_hg).first()
                            #     if bbm.extra_assets:
                            #         for e_a in bbm.extra_assets:
                            #             if e_a in ehg.description:
                            #                 match = True
                            #                 break
                            #         # if bbm.extra_asset in ehg.description:
                            #         #     match = True
                            #     if not match:
                            #         if ehg:
                            #             for bb in ehg.bbmechanisms:
                            #                 ehg.remove_bb(bb)
                            #             HardGoal.query.filter_by(id=hg.original_hg).delete()
                            #         hg.extra_hg_used = None
                            #         hg.original_hg = None
                            #         db.session.commit()
            for key, values in current_bbms['bbms_list'].items():
                if values:
                    for valu in values:
                        hg = HardGoal.query.filter_by(id=key).first()
                        hg.remove_bb(valu)
            project.final_assumptions = False
            db.session.commit()

            flash('Black Box Mechanisms updated', 'succ')
            return redirect(url_for('assumptions', project=project.name))
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
            new_hg_start = hg.description.find('during the process of ')
            new_hg_service = hg.description.find('ensures the ')
            new_hg = hg.description[:new_hg_service] + 'ensures the ' + bbm.extra_asset + ' ' + hg.description[new_hg_start:]
            if 'authenticity' in  bbm.extra_asset.lower():
                n_hg = HardGoal(authenticity='yes', description=new_hg, project_id=hg.project_id, priority=hg.priority, extra_hg_used=True, extra_hg=True, original_hg=hg.id, component_id=hg.component_id)
                db.session.add(n_hg)
                db.session.commit()
                hg.extra_hg_used = True
                hg.original_hg = n_hg.id
            elif 'confidentiality' in bbm.extra_asset.lower():
                n_hg = HardGoal(confidentiality='yes', description=new_hg, project_id=hg.project_id, priority=hg.priority, extra_hg_used=True, extra_hg=True, original_hg=hg.id, component_id=hg.component_id)
                db.session.add(n_hg)
                db.session.commit()
                hg.extra_hg_used = True
                hg.original_hg = n_hg.id
            elif 'integrity' in bbm.extra_asset.lower():
                n_hg = HardGoal(integrity='yes', description=new_hg, project_id=hg.project_id, priority=hg.priority, extra_hg_used=True, extra_hg=True, original_hg=hg.id, component_id=hg.component_id)
                db.session.add(n_hg)
                db.session.commit()
                hg.extra_hg_used = True
                hg.original_hg = n_hg.id
            project.final_assumptions = False
            db.session.commit()
            return redirect(url_for('assumptions', project=project.name))

        return render_template('assumptions.html',
                               title=project.name,
                               project=project.name,
                               current_hardgoals=current_hardgoals,
                               empty_hgoals=empty_hgoals)
    else:
        flash('You don\'t have permission to access this project', 'error')
        return redirect(url_for('index'))


@app.route('/bbmech/<project>/<hg>', methods=['GET', 'POST'])
@login_required
def ebbm(project, hg):
    access = check_permission(project)
    project = Projects.query.filter_by(name=project).first()
    if access:
        form = ExtraHgForm()
        hg = HardGoal.query.filter_by(id=hg).first()
        fr = FunctionalRequirement.query.filter_by(id=hg.freq_id).first()
        component = SubService.query.filter_by(id=hg.component_id).first()
        if hg.authenticity:
            hg_goal = 'Authenticity'
        elif hg.confidentiality:
            hg_goal = 'Confidentiality'
        else:
            hg_goal = 'Integrity'
        mecha = [bbm for bbm in hg.bbmechanisms][0]
        e_fr = [fr for fr in mecha.extra_func_req]
        e_sg = [sg for sg in mecha.extra_softgoals]
        # mecha_list = [len(mecha.extra_assets), len(mecha.extra_softgoals), len(mecha.extra_func_req)]
        # longer = max(range(len(mecha_list)), key=mecha_list.__getitem__)
        # print(longer)
        if request.method == 'POST':
            for field, value in request.form.items():
                if field == 'csrf_token':
                    continue
                else:
                    if not [asset for asset in mecha.extra_assets]:
                        return redirect(url_for('assumptions', project=project.name))
                    _, component_id, sg_id, fr_id = field.split('-')

                    extra_component = SubService.query.filter_by(name=value, project_id=project.id).first()
                    if extra_component is None:
                        extra_component = SubService(name=value, project_id=project.id)
                        db.session.add(extra_component)
                        db.session.commit()
                        flash(f'Added COMPONENT: {extra_component.name} to the Database', 'succ')

                    if not e_sg:
                        extra_asset = ExtraAsset.query.filter_by(id=sg_id).first()
                        asset_in_db = Good.query.filter_by(description=extra_asset.name, project_id=project.id).first()
                        if asset_in_db is None:
                            extra_asset = Good(description=extra_asset.name, project_id=project.id)
                            db.session.add(extra_asset)
                            db.session.commit()
                            flash(f'Added ASSET: {extra_asset.description} to the Database', 'succ')
                        else:
                            extra_asset = asset_in_db
                    else:
                        extra_asset_index = ExtraSoftGoal.query.filter_by(id=sg_id).first().name
                        if 'authenticity' in extra_asset_index.lower():
                            ass_goal = 'authenticity'
                        elif 'confidentiality' in extra_asset_index.lower():
                            ass_goal = 'confidentiality'
                        else:
                            ass_goal = 'integrity'
                        end_index = re.search(f'{ass_goal.lower()} of ', extra_asset_index.lower()).end()
                        extra_asset_name = extra_asset_index[end_index:]
                        extra_asset = Good.query.filter_by(description=extra_asset_name, project_id=project.id).first()
                        if extra_asset is None:
                            extra_asset = Good(description=extra_asset_name, project_id=project.id)
                            db.session.add(extra_asset)
                            db.session.commit()
                            flash(f'Added ASSET: {extra_asset.description} to the Database', 'succ')

                    if e_sg:
                        extra_sg = ExtraSoftGoal.query.filter_by(id=sg_id).first()
                        if extra_sg is not None:
                            if 'Authenticity' in extra_sg.name:
                                goal = {'authenticity': extra_sg.name}
                            elif 'Confidentiality' in extra_sg.name:
                                goal = {'confidentiality': extra_sg.name}
                            else:
                                goal = {'integrity': extra_sg.name}
                            existing_sg = SoftGoal.query.filter_by(project_id=project.id, **goal).first()
                            if existing_sg is None:
                                goal_desc = str(next(iter(goal)))
                                extra_sg = SoftGoal(cb_value=f'{goal_desc}{extra_asset.id}', project_id=project.id, **goal)
                                db.session.add(extra_sg)
                                db.session.commit()
                                flash(f'Added SOFT GOAL: {extra_sg.cb_value} to the Database', 'succ')
                            else:
                                extra_sg = existing_sg
                    else:
                        if hg_goal == 'Authenticity':
                            sg_goal = {'authenticity': f'{hg_goal} of {extra_asset.description}'}
                        elif hg_goal == 'Confidentiality':
                            sg_goal = {'confidentiality': f'{hg_goal} of {extra_asset.description}'}
                        else:
                            sg_goal = {'integrity': f'{hg_goal} of {extra_asset.description}'}
                        goal_desc = str(next(iter(sg_goal)))
                        extra_sg = SoftGoal(cb_value=f'{goal_desc}{extra_asset.id}', project_id=project.id, **sg_goal)
                        db.session.add(extra_sg)
                        db.session.commit()
                        flash(f'Added SOFT GOAL: {extra_sg.cb_value} to the Database', 'succ')

                    if e_fr:
                        extra_fr = ExtraFreqReq.query.filter_by(id=fr_id).first()
                        if extra_fr is not None:
                            existing_fr = FunctionalRequirement.query.filter_by(description=extra_fr.name, project_id=project.id).first()
                            if existing_fr is None:
                                extra_fr = FunctionalRequirement(description=extra_fr.name, project_id=project.id)
                                db.session.add(extra_fr)
                                db.session.commit()
                                flash(f'Added FUNCTIONAL REQUIREMENT: {extra_fr.description} to the Database', 'succ')
                            else:
                                extra_fr = existing_fr

                            extra_fr.add_serv(extra_component)
                            db.session.commit()
                    else:
                        extra_fr = FunctionalRequirement.query.filter_by(id=fr_id).first()
                        extra_fr.add_serv(extra_component)
                        db.session.commit()

                    if extra_sg.authenticity:
                        sg_desc = extra_sg.authenticity
                        nhg_goal = {'authenticity': 'yes'}
                    elif extra_sg.confidentiality:
                        sg_desc = extra_sg.confidentiality
                        nhg_goal = {'confidentiality': 'yes'}
                    else:
                        sg_desc = extra_sg.integrity
                        nhg_goal = {'integrity': 'yes'}
                    new_extra_hg_description = f'{extra_component.name} ensures the {sg_desc} during the process of {extra_fr.description}'
                    existing_hg = HardGoal.query.filter_by(description=new_extra_hg_description, project_id=project.id).first()
                    if existing_hg is None:
                        extra_hg = HardGoal(component_id=extra_component.id, freq_id=extra_fr.id, sg_id=extra_sg.id, description=new_extra_hg_description, extra_hg_used=1, extra_hg=1, original_hg=hg.id, project_id=project.id, unique_id=hg_id_gen(project, extra_fr, extra_component, extra_sg), **nhg_goal)
                        db.session.add(extra_hg)
                        db.session.commit()
                        flash(f'Added HARD GOAL: {extra_hg.description} to the Database', 'succ')



                    # extra_component = SubService.query.filter_by(id=component_id).first()
                    # if extra_component.name != value:
                    #     # extra_component.name = value
                    #     alrdy_in_db_component = SubService.query.filter_by(name=value, project_id=hg.project.id).first()
                    #     if not alrdy_in_db_component:
                    #         new_extra_component = SubService(name=value, project_id=hg.project_id)
                    #         db.session.add(new_extra_component)
                    # else:
                    #     new_extra_component = False
                    # extra_sg = ExtraSoftGoal.query.filter_by(id=sg_id).first()
                    # if extra_sg is None:
                    #     extra_sg = ExtraSoftGoal(name="", bbm_id=mecha.id)
                    # # print(extra_sg.id, extra_sg.authenticity, extra_sg.confidentiality, extra_sg.integrity)
                    # if not e_sg:
                    #     # print(f'sg_id is {sg_id}')
                    #     extra_asset = ExtraAsset.query.filter_by(id=sg_id).first()
                    #     old_asset = Good.query.filter_by(description=extra_asset.name, project_id=project.id).first()
                    #     if not old_asset:
                    #         new_extra_asset = Good(description=extra_asset.name, project_id=project.id)
                    #         db.session.add(new_extra_asset)
                    #         db.session.commit()
                    #     else:
                    #         new_extra_asset = False
                    #     extra_sg.name = f'{goal} of {extra_asset.name}'
                    #     esg_dict = {goal.lower(): extra_sg.name}
                    #     if not old_asset:
                    #         if new_extra_asset:
                    #             new_extra_asset = Good.query.filter_by(description=extra_asset.name, project_id=project.id).first()
                    #     new_extra_sg = SoftGoal(cb_value=f'{goal.lower()}{new_extra_asset.id if new_extra_asset else old_asset.id}', project_id=project.id, **esg_dict)
                    #     # else:
                    #     #     new_extra_sg = SoftGoal(cb_value=f'{goal.lower()}{old_asset.id}')
                    # else:
                    #     if 'integrity' in extra_sg.name.lower():
                    #         esg_dict = {'integrity': extra_sg.name}
                    #         new_asset_from_sg = f"{extra_sg.name.replace('Integrity of ', '')}"
                    #     elif 'confidentiality' in extra_sg.name.lower():
                    #         esg_dict = {'confidentiality': extra_sg.name}
                    #         new_asset_from_sg = f"{extra_sg.name.replace('Confidentiality of ', '')}"
                    #     elif 'authenticity' in extra_sg.name.lower():
                    #         esg_dict = {'authenticity': extra_sg.name}
                    #         new_asset_from_sg = f"{extra_sg.name.replace('Authenticity of ', '')}"
                    #     else:
                    #         esg_dict = {goal.lower(): extra_sg.name}
                    #         new_asset_from_sg = f"{extra_sg.name}"
                    #     old_asset_f_sg = Good.query.filter_by(description=new_asset_from_sg, project_id=project.id).first()
                    #     if not old_asset_f_sg:
                    #         new_a_f_sg = Good(description=new_asset_from_sg, project_id=project.id)
                    #         db.session.add(new_a_f_sg)
                    #         db.session.commit()
                    #     new_extra_sg = SoftGoal(cb_value=f'{goal.lower()}{old_asset_f_sg.id if old_asset_f_sg else new_a_f_sg.id}', project_id=project.id, **esg_dict)
                    # alrdy_in_db_sg = SoftGoal.query.filter_by(**esg_dict).first()
                    # if alrdy_in_db_sg:
                    #     new_extra_sg = alrdy_in_db_sg #
                    # else:
                    #     db.session.add(new_extra_sg)
                    # extra_fr = ExtraFreqReq.query.filter_by(id=fr_id).first()
                    # if extra_fr is None:
                    #     extra_fr = ExtraFreqReq(name="", bbm_id=mecha.id)
                    # if not e_fr:
                    #     extra_fr.name = fr.description
                    #     if new_extra_component:
                    #         fr.add_serv(new_extra_component)
                    #     else:
                    #         fr.add_serv(component)
                    # else:
                    #     old_fr = FunctionalRequirement.query.filter_by(description=extra_fr.name, project_id=project.id).first()
                    #     if not old_fr:
                    #         new_extra_fr = FunctionalRequirement(description=extra_fr.name, project_id=project.id)
                    #         db.session.add(new_extra_fr)
                    #     else:
                    #         new_extra_fr = old_fr
                    #     if new_extra_component:
                    #         new_extra_fr.add_serv(new_extra_component)
                    #     else:
                    #         new_extra_fr.add_serv(component)
                    #     db.session.commit()
                    #     # new_extra_fr.add_serv(new_extra_component)
                    # # print(component_id, asset_id, sg_id, fr_id)
                    #
                    # new_hg = f'{new_extra_component.name if new_extra_component else extra_component.name} ensures the {extra_sg.name} during the process of {extra_fr.name}'
                    # print(new_hg)
                    # if 'integrity' in extra_sg.name.lower():
                    #     nehg_dict = {'integrity': 'yes'}
                    # elif 'confidentiality' in extra_sg.name.lower():
                    #     nehg_dict = {'confidentiality': 'yes'}
                    # elif 'authenticity' in extra_sg.name.lower():
                    #     nehg_dict = {'authenticity': 'yes'}
                    # else:
                    #     nehg_dict = {}
                    # # print(nehg_dict)
                    # new_extra_hg = HardGoal(description=new_hg, component_id=new_extra_component.id if new_extra_component else extra_component.id, freq_id=new_extra_fr.id if e_fr else fr.id,
                    # sg_id=new_extra_sg.id, extra_hg_used=True, extra_hg=True, original_hg=hg.id, project_id=hg.project_id, unique_id=hg_id_gen(project, fr, new_extra_component if new_extra_component else extra_component, new_extra_sg), **nehg_dict)
                    # db.session.add(new_extra_hg)
                    # hg.extra_hg_used = True
                    # # print(new_extra_hg.unique_id)
                    # # # db.session.commit()
                    # # print(new_extra_hg.id, new_extra_hg.authenticity, new_extra_hg.confidentiality, new_extra_hg.integrity)
                    # #
                    # # print(f'''
                    # #       extra sg {extra_sg}''')
                    # db.session.commit()
            hg.extra_hg_used = 1
            db.session.commit()
            flash('The Changes were added to the Database.', 'succ')
            return redirect(url_for('assumptions', project=project.name))
            # return redirect(url_for('ebbm', project=project.name, hg=hg.id))
        return render_template("ebbm.html",
                               title=hg.description,
                               project=project.name,
                               hg=hg,
                               mecha=mecha,
                               form=form,
                               fr=fr,
                               component=component,
                               goal=hg_goal,
                               e_fr=e_fr,
                               e_sg=e_sg)
                               # longer=longer)
    else:
        flash('You don\'t have permission to access this page', 'error')
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
            if current_user.is_authenticated:
                flash('You don\'t have permission to access this page.', 'error')
                return redirect(url_for('index'))
            else:
                return redirect(url_for('security.login', next=request.url))


class MyModelViewBbMech(sqla.ModelView):

    # form_ajax_refs = {
    #     'assumptions': {
    #         'fields': ['name', 'id'],
    #         'page_size': 10
    #     }
    # }

    edit_modal = True
    # column_list = ['name', 'assumptionz']
    # column_display_all_relations = True
    column_list = ['name','authenticity','confidentiality','integrity', 'extra_assets', 'extra_softgoals', 'extra_func_req','assumptions', 'against_actor']
    # column_editable_list = ['extra_assets']
    inline_models = (ExtraAsset, ExtraSoftGoal, ExtraFreqReq)

    # can_view_details = True

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                flash('You don\'t have permission to access this page.', 'error')
                return redirect(url_for('index'))
            else:
                return redirect(url_for('security.login', next=request.url))


class MyModelViewHg(sqla.ModelView):

    # form_ajax_refs = {
    #     'assumptions': {
    #         'fields': ['name', 'id'],
    #         'page_size': 10
    #     }
    # }

    # edit_modal = True
    # column_list = ['name', 'assumptionz']
    # column_display_all_relations = True

    can_delete = False
    can_edit = False
    can_create = False
    column_filters = ['project.name', 'correctly_implemented']
    column_searchable_list = ['project.name', 'id', 'unique_id', 'description']
    column_list = ['project.name', 'id', 'description', 'correctly_implemented', 'unique_id']
    column_editable_list = ['correctly_implemented']

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
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
admin.add_view(MyModelView(Actors, db.session, 'Actor Roles'))
admin.add_view(MyModelViewBbMech(BbMechanisms, db.session))
admin.add_view(MyModelView(Assumptions, db.session))
admin.add_view(MyModelViewHg(HardGoal, db.session, 'HG Implementation'))


@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for,
    )


def hg_id_gen(proj, fr, comp, sg):
    return f"HGP{proj.id}F{fr.id}C{comp.id}SG{sg.id}T{datetime.now().strftime('%d%m%y%H%M%S%f')}"

# app.add_url_rule(
#         "/graphql", view_func=GraphQLView.as_view("graphql", schema=schema, graphiql=True)
# )