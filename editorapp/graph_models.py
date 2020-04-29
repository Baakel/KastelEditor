from py2neo.ogm import GraphObject, Property, Label, RelatedFrom, RelatedTo

class Stakeholder(GraphObject):
    name = Property()

    project = RelatedFrom("Project", "IMPORTANT_TO")


class Project(GraphObject):
    name = Property()
    final_assumptions = Property()

    important_to = RelatedTo("Stakeholder")
