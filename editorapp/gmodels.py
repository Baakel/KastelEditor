from editorapp import driver


class Project:
    def __init__(self, name):
        self.name = name

    def create_project(self, creator):
        with driver.session() as session:
            session.run("MATCH (u:User) "
                        "WHERE u.id = $uId "
                        "CREATE (p:Project {name: $name}) "
                        "CREATE (u)-[:CREATOR]->(p)", name=self.name, uId=creator)

    def get_project(self):
        with driver.session() as session:
            res = session.run("MATCH (p:Project) WHERE p.name = $name RETURN p", name=self.name).data()
            if res == []:
                return None
            return res

    def editors(self):
        with driver.session() as session:
            res = session.run("MATCH (u:User)-[r]->(p:Project) "
                              "WHERE type(r) = 'CREATOR' OR type(r) = 'EDITOR' AND p.name = $name "
                              "RETURN u.id as id", name=self.name)
            return set([editor['id'] for editor in res])

    def stakeholders(self):
        with driver.session() as session:
            res = session.run("MATCH (p:Project)-[:OWNS]->(s:Stakeholder) WHERE p.name = $name RETURN ID(s) as id, "
                              "s.name as nickname",
                              name=self.name).data()
            return res

    def assets(self):
        with driver.session() as session:
            res = session.run("MATCH (p:Project)-[:OWNS]->(a:Asset) "
                              "WHERE p.name = $name "
                              "OPTIONAL MATCH (a)-[:IMPORTANT_TO]->(s:Stakeholder)"
                              "RETURN ID(a) as id, "
                              "a.description as description,"
                              "collect(s.name) AS stakeholders", name=self.name).data()
            return res

    def softgoals(self):
        with driver.session() as session:
            res = session.run("MATCH (p:Project)-[:OWNS]->(s:SoftGoal) "
                              "WHERE p.name = $name "
                              "OPTIONAL MATCH (s)<-[:MAKES]-(a:Asset)"
                              "RETURN ID(s) as id, s.description as description, s.type as type, "
                              "collect(a.description) as assets",
                              name=self.name).data()
            return res

    def functional_requirements(self):
        with driver.session() as session:
            res = session.run("MATCH (p:Project)-[:OWNS]->(f:FunctionalRequirement) "
                              "WHERE p.name = $pName "
                              "OPTIONAL MATCH (f)-[:USES]->(s:SubService)"
                              "RETURN ID(f) as id, f.description as description, collect(s.name) as services",
                              pName=self.name).data()
            return res

    def sub_services(self):
        with driver.session() as session:
            res = session.run("MATCH (p:Project)-[:OWNS]->(s:SubService) "
                              "WHERE p.name = $pName "
                              "RETURN ID(s) as id, s.name as name", pName=self.name).data()
            return res


class Stakeholder:
    def __init__(self, name, project):
        self.name = name
        self.proj = project

    def create_stakeholder(self):
        with driver.session() as session:
            session.run("MATCH (p:Project) "
                        "WHERE p.name = $pName "
                        "CREATE (s:Stakeholder {name: $sName})<-[:OWNS]-(p)",
                        pName=self.proj, sName=self.name)

    def check_stakeholder(self):
        with driver.session() as session:
            res = session.run("MATCH (s:Stakeholder)<-[:OWNS]-(p:Project) "
                              "WHERE s.name = $sName AND p.name = $pName "
                              "RETURN s",
                              pName=self.proj, sName=self.name).data()
            return res

    def edit(self, new_name):
        with driver.session() as session:
            session.run("MATCH (s:Stakeholder)<-[:OWNS]-(p:Project) "
                        "WHERE s.name = $sName AND p.name = $pName "
                        "SET s.name = $nName ",
                        sName=self.name, nName=new_name, pName=self.proj)

    def delete(self):
        with driver.session() as session:
            session.run("MATCH (s:Stakeholder)<-[:OWNS]-(p:Project) "
                        "WHERE s.name = $sName AND p.name = $pName "
                        "DETACH DELETE s ",
                        sName=self.name, pName=self.proj)

    @staticmethod
    def get_all(project_name):
        with driver.session() as session:
            res = session.run("MATCH (s:Stakeholder)<-[:OWNS]-(p:Project) "
                              "WHERE p.name = $pName "
                              "RETURN s.name as name",
                              pName=project_name).data()
            return res

    @classmethod
    def get_stakeholder(cls, node_id: int):
        with driver.session() as session:
            res = session.run("MATCH (s:Stakeholder)<-[:OWNS]-(p:Project) "
                              "WHERE ID(s) = $nodeId "
                              "RETURN s,p", nodeId=node_id).data()
            if res == []:
                return None
            return cls(name=res[0]['s']['name'], project=res[0]['p']['name'])


class User:
    def __init__(self, token, nickname=None, contact=None, id=None, role=None):
        self.nickname = nickname
        self.contact = contact
        self.id = id
        self.role = role
        self.token = token
        self.roles = [role]

    def wprojects(self):
        with driver.session() as session:
            res = session.run("MATCH (u:User)-[r]->(p:Project) "
                        "WHERE type(r) = 'CREATOR' OR  type(r) = 'EDITOR' AND u.name = $name "
                        "RETURN p.name as name", name=self.nickname)
            return [project for project in res]

    def has_role(self, e_role):
        if not e_role in self.roles:
            return False
        return True

    def create(self):
        with driver.session() as session:
            session.run("CREATE (u:User {nickname: $nickname, contact: $contact, id: $id, role: $role, token: $token})",
                        nickname=self.nickname, contact=self.contact, id=self.id, role=self.role, token=self.token)

    def get_token(self):
        return self.token

    @staticmethod
    def get_all(limit=5):
        with driver.session() as session:
            res = session.run("MATCH (u:User) RETURN u LIMIT $limit", limit=limit).data()
            return res

    @staticmethod
    def query(nickname=None):
        if not nickname:
            return None
        with driver.session() as session:
            res = session.run("MATCH (u:User) "
                              "WHERE u.nickname = $nickname "
                              "RETURN u",
                              nickname=nickname).data()
            return res

    @classmethod
    def get_user(cls, id):
        with driver.session() as session:
            res = session.run("MATCH (u:User) "
                              "WHERE u.id = $uId "
                              "RETURN u", uId=id).data()
            if res == []:
                return None
            return cls(nickname=res[0]['u']['nickname'], id=res[0]['u']['id'], role=res[0]['u']['role'],
                       token=res[0]['u']['token'], contact=res[0]['u']['contact'])


class Asset:
    def __init__(self, description, project):
        self.description = description
        self.project = project

    def create_asset(self):
        with driver.session() as session:
            session.run("MATCH (p:Project) "
                        "WHERE p.name = $pName "
                        "CREATE (a:Asset {description: $desc})<-[:OWNS]-(p)",
                        pName=self.project, desc=self.description)

    def check_asset(self):
        with driver.session() as session:
            res = session.run("MATCH (a:Asset)<-[:OWNS]-(p:Project) "
                              "WHERE a.description = $desc AND p.name = $pName "
                              "RETURN a",
                              desc=self.description, pName=self.project).data()
            if res == []:
                return None
            return res

    def edit(self, new_name):
        with driver.session() as session:
            session.run("MATCH (a:Asset)<-[:OWNS]-(p:Project) "
                        "WHERE a.description = $aName AND p.name = $pName "
                        "SET a.description = $nName", aName=self.description, nName=new_name, pName=self.project)

    def link_stakeholder(self, stakeholder):
        with driver.session() as session:
            session.run("MATCH (a:Asset)<-[:OWNS]-(p:Project), (s:Stakeholder)<-[:OWNS]-(p:Project) "
                        "WHERE a.description = $aDesc AND s.name = $sName AND p.name = $pName "
                        "MERGE (a)-[:IMPORTANT_TO]->(s)", aDesc=self.description, sName=stakeholder, pName=self.project)

    def unlink_stakeholder(self, stakeholder):
        with driver.session() as session:
            session.run("MATCH (a:Asset)-[r:IMPORTANT_TO]->(s:Stakeholder)<-[:OWNS]-(p:Project) "
                        "WHERE a.description = $desc AND s.name = $sName AND p.name = $pName "
                        "DELETE r", desc=self.description, sName=stakeholder, pName=self.project)

    def delete(self):
        with driver.session() as session:
            session.run("MATCH (a:Asset)<-[:OWNS]-(p:Project)"
                        "WHERE a.description = $aDesc AND p.name = $pName "
                        "OPTIONAL MATCH (a)-[:MAKES]->(s:SoftGoal) "
                        "DETACH DELETE s,a", aDesc=self.description, pName=self.project)

    @classmethod
    def get_asset(cls, node_id: int):
        with driver.session() as session:
            res = session.run("MATCH (a:Asset)<-[:OWNS]-(p:Project) "
                              "WHERE ID(a) = $nodeId "
                              "RETURN a,p", nodeId=node_id).data()
            if res == []:
                return None
            return cls(description=res[0]['a']['description'], project=res[0]['p']['name'])


class SoftGoal:
    def __init__(self, description, project, type):
        self.description = description
        self.project = project
        self.type = type

    def create_sg(self, asset):
        with driver.session() as session:
            session.run("MATCH (p:Project), (a:Asset)<-[:OWNS]-(p) "
                        "WHERE p.name = $pName AND a.description = $aDesc "
                        "MERGE (s:SoftGoal {description: $desc, type: $type})<-[:MAKES]-(a) "
                        "MERGE (p)-[:OWNS]->(s)", pName=self.project, desc=self.description, aDesc=asset,
                        type=self.type)

    def delete(self):
        with driver.session() as session:
            session.run("MATCH (p:Project)-[:OWNS]->(s:SoftGoal) "
                        "WHERE p.name = $pName AND s.description = $desc AND s.type = $type "
                        "DETACH DELETE s", pName=self.project, desc=self.description, type=self.type)


class FunctionalRequirement:
    def __init__(self, description, project):
        self.description = description
        self.project = project

    def create(self):
        with driver.session() as session:
            session.run("MATCH (p:Project) "
                        "WHERE p.name = $pName "
                        "CREATE (f:FunctionalRequirement {description: $fName})<-[:OWNS]-(p)",
                        fName=self.description, pName=self.project)

    def delete(self):
        with driver.session() as session:
            session.run("MATCH (p:Project)-[:OWNS]->(f:FunctionalRequirement) "
                        "WHERE p.name = $pName AND f.description = $desc "
                        "DETACH DELETE f", pName=self.project, desc=self.description)

    def check(self):
        with driver.session() as session:
            res = session.run("MATCH (f:FunctionalRequirement)<-[:OWNS]-(p:Project) "
                              "WHERE f.description = $desc AND p.name = $pName "
                              "RETURN f.description as description", desc=self.description, pName=self.project).data()
            if res == []:
                return None
            return res

    def edit(self, new_desc):
        with driver.session() as session:
            session.run("MATCH (f:FunctionalRequirement)<-[:OWNS]-(p:Project) "
                        "WHERE p.name = $pName AND f.description = $desc "
                        "SET f.description = $newDesc",
                        pName=self.project, desc=self.description, newDesc=new_desc)

    def link(self, sub_service):
        with driver.session() as session:
            session.run("MATCH (f:FunctionalRequirement)<-[:OWNS]-(p:Project)-[:OWNS]->(s:SubService) "
                        "WHERE f.description = $desc AND p.name = $pName AND s.name = $sName "
                        "MERGE (f)-[:USES]->(s)",
                        desc=self.description, pName=self.project, sName=sub_service)

    def unlink(self, sub_service):
        with driver.session() as session:
            session.run("MATCH (f:FunctionalRequirement)<-[:OWNS]-(p:Project)-[:OWNS]->(s:SubService), "
                        "(f)-[r:USES]->(s) "
                        "WHERE f.description = $desc AND p.name = $pName AND s.name = $sName "
                        "DELETE r",
                        desc=self.description, pName=self.project, sName=sub_service)

    @staticmethod
    def get_all(project_name):
        with driver.session() as session:
            res = session.run("MATCH (f:FunctionalRequirement)<-[:OWNS]-(p:Project) "
                              "WHERE p.name = $pName "
                              "OPTIONAL MATCH (f)-[:USES]->(s:SubService) "
                              "RETURN ID(f) as id, f.description as description, collect(s.name) as services",
                              pName=project_name).data()
            return res


class SubService:
    def __init__(self, name, project):
        self.name = name
        self.project = project

    def create(self):
        with driver.session() as session:
            session.run("MATCH (p:Project) "
                        "WHERE p.name = $pName "
                        "CREATE (s:SubService {name: $sName})<-[:OWNS]-(p)",
                        pName=self.project, sName=self.name)

    def check(self):
        with driver.session() as session:
            res = session.run("MATCH (s:SubService)<-[:OWNS]-(p:Project) "
                              "WHERE s.name = $sName AND p.name = $pName "
                              "RETURN s.name as description", sName=self.name, pName=self.project).data()
            if res == []:
                return None
            return res

    def delete(self):
        with driver.session() as session:
            session.run("MATCH (s:SubService)<-[:OWNS]-(p:Project) "
                        "WHERE s.name = $sName AND p.name = $pName "
                        "DETACH DELETE s", sName=self.name, pName=self.project)

    def edit(self, new_name):
        with driver.session() as session:
            session.run("MATCH (s:SubService)<-[:OWNS]-(p:Project) "
                        "WHERE p.name = $pName AND s.name = $name "
                        "SET s.name = $newName",
                        pName=self.project, name=self.name, newName=new_name)

    @staticmethod
    def get_all(project_name):
        with driver.session() as session:
            res = session.run("MATCH (s:SubService)<-[:OWNS]-(p:Project) "
                              "WHERE p.name = $pName "
                              "RETURN ID(s) as id, s.name as name",
                              pName=project_name).data()
            return res