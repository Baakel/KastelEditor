import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyConnectionField, SQLAlchemyObjectType
from .models import HardGoal as HardGoalModel
from .models import Role as RoleModel
from .models import Users as UserModel
from .models import Stakeholder as StakeholderModel
from .models import Good as GoodModel
from .models import FunctionalRequirement as FunctionalRequirementModel
from .models import SubService as SubServiceModel
from .models import SoftGoal as SoftGoalModel
from .models import Projects as ProjectsModel
from .models import Assumptions as AssumptionsModel
from .models import Actors as ActorsModel
from .models import BbMechanisms as BbMechanismsModel
from .models import ExtraAsset as ExtraAssetModel
from .models import ExtraSoftGoal as ExtraSoftGoalModel
from .models import ExtraFreqReq as ExtraFreqReqModel
from .models import Attacker as AttackerModel
from .models import Aktoren as AktorenModel
from .models import ActorDetails as ActorDetailsModel


class ActorDetails(SQLAlchemyObjectType):
    class Meta:
        model = ActorDetailsModel
        interfaces = (relay.Node, )


class Aktoren(SQLAlchemyObjectType):
    class Meta:
        model = AktorenModel
        interfaces = (relay.Node, )


class Attacker(SQLAlchemyObjectType):
    class Meta:
        model = AttackerModel
        interfaces = (relay.Node, )


class ExtraFreqReq(SQLAlchemyObjectType):
    class Meta:
        model = ExtraFreqReqModel
        interfaces = (relay.Node, )


class ExtraSoftGoal(SQLAlchemyObjectType):
    class Meta:
        model = ExtraSoftGoalModel
        interfaces = (relay.Node, )


class ExtraAsset(SQLAlchemyObjectType):
    class Meta:
        model = ExtraAssetModel
        interfaces = (relay.Node, )


class BbMechanisms(SQLAlchemyObjectType):
    class Meta:
        model = BbMechanismsModel
        interfaces = (relay.Node, )


class Actors(SQLAlchemyObjectType):
    class Meta:
        model = ActorsModel
        interfaces = (relay.Node, )


class Assumptions(SQLAlchemyObjectType):
    class Meta:
        model = AssumptionsModel
        interfaces = (relay.Node, )


class Projects(SQLAlchemyObjectType):
    class Meta:
        model = ProjectsModel
        interfaces = (relay.Node, )


class SoftGoal(SQLAlchemyObjectType):
    class Meta:
        model = SoftGoalModel
        interfaces = (relay.Node, )


class SubService(SQLAlchemyObjectType):
    class Meta:
        model = SubServiceModel
        interfaces = (relay.Node, )


class FunctionalRequirement(SQLAlchemyObjectType):
    class Meta:
        model = FunctionalRequirementModel
        interfaces = (relay.Node, )


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
        hg = HardGoalModel.query.filter_by(id=kwargs['id']).all()
        return hg


schema = graphene.Schema(query=Query2)