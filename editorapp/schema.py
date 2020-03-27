import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType
from .models import HardGoal as HardGoalModel
from .models import Role as RoleModel
from .models import Users as UserModel
from .models import Stakeholder as StakeholderModel
from .models import Good as GoodModel


class Good(SQLAlchemyObjectType):
    class Meta:
        model = GoodModel
        interfaces = (relay.Node, )


class Stakeholder(SQLAlchemyObjectType):
    class Meta:
        model = StakeholderModel
        interfaces = (relay.Node, )


class HardGoal(SQLAlchemyObjectType):
    class Meta:
        model = HardGoalModel
        interfaces = (relay.Node, )


class Role(SQLAlchemyObjectType):
    class Meta:
        model = RoleModel
        interfaces = (relay.Node, )


class Users(SQLAlchemyObjectType):
    class Meta:
        model = UserModel
        interfaces = (relay.Node, )


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    all_hgs = SQLAlchemyConnectionField(HardGoal)
    all_roles = SQLAlchemyConnectionField(Role)
    all_users = SQLAlchemyConnectionField(Users)


class Query2(graphene.ObjectType):
    todas_hgs = graphene.List(HardGoal, id=graphene.Int())
    good = graphene.Field(Good, id=graphene.ID(required=True))

    def resolve_good(self, info, id):
        return GoodModel.query.filter_by(id=id).first()

    def resolve_todas_hgs(self, info, **kwargs):
        print(kwargs['id'])
        hg = HardGoalModel.query.filter_by(id=kwargs['id']).all()
        return hg


schema = graphene.Schema(query=Query2)