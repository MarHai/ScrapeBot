import string
import enum
import random
from sqlalchemy import Column, DateTime, String, Integer, Enum, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from scrapebot.emulate import RecipeStepTypeEnum, Emulator
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

base = declarative_base()


class User(UserMixin, base):
    __tablename__ = 'user'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    email = Column(String(150), unique=True)
    name = Column(String(80))
    password = Column(String(128))
    instances_owned = relationship('Instance', back_populates='owner', order_by='Instance.name')
    instance_privileges = relationship(
        'UserInstancePrivilege',
        back_populates='user',
        order_by='UserInstancePrivilege.created'
    )
    recipes_owned = relationship('Recipe', back_populates='owner', order_by='Recipe.name')
    recipe_privileges = relationship(
        'UserRecipePrivilege',
        back_populates='user',
        order_by='UserRecipePrivilege.created'
    )
    active = Column(Boolean, default=True)

    def __repr__(self):
        return "<User(email='%s', name='%s', active='%d')>" % (self.email, self.name, self.active)

    def create_password(self):
        temp = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(12))
        self.password = generate_password_hash(temp)
        return temp

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return str(self.uid)

    def jsonify(self):
        return {
            'uid': self.uid,
            'created': self.created,
            'email': self.email,
            'name': self.name,
            'active': self.active
        }


class UserInstancePrivilege(base):
    __tablename__ = 'user2instance'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    user_uid = Column(Integer, ForeignKey('user.uid'))
    user = relationship(User, back_populates='instance_privileges')
    instance_uid = Column(Integer, ForeignKey('instance.uid'))
    instance = relationship('Instance', back_populates='privileged_users')
    allowed_to_edit = Column(Boolean, default=False)

    def __repr__(self):
        return "<Privilege(user='%s', instance='%s', edit_permission='%d')>" % \
               (self.user.email, self.instance.name, self.allowed_to_edit)

    def jsonify(self):
        return {
            'uid': self.uid,
            'created': self.created,
            'user': self.user.jsonify(),
            'instance': self.instance.jsonify(),
            'allowed_to_edit': self.allowed_to_edit
        }


class UserRecipePrivilege(base):
    __tablename__ = 'user2recipe'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    user_uid = Column(Integer, ForeignKey('user.uid'))
    user = relationship(User, back_populates='recipe_privileges')
    recipe_uid = Column(Integer, ForeignKey('recipe.uid'))
    recipe = relationship('Recipe', back_populates='privileged_users')
    allowed_to_edit = Column(Boolean, default=False)

    def __repr__(self):
        return "<Privilege(user='%s', recipe='%s', edit_permission='%d')>" % \
               (self.user.email, self.recipe.name, self.allowed_to_edit)

    def jsonify(self):
        return {
            'uid': self.uid,
            'created': self.created,
            'user': self.user.jsonify(),
            'recipe': self.recipe.jsonify(),
            'allowed_to_edit': self.allowed_to_edit
        }


class Instance(base):
    __tablename__ = 'instance'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    name = Column(String(256))
    description = Column(Text)
    owner_uid = Column(Integer, ForeignKey('user.uid'))
    owner = relationship(User, back_populates='instances_owned')
    privileged_users = relationship(
        UserInstancePrivilege,
        back_populates='instance',
        order_by='UserInstancePrivilege.created'
    )
    runs = relationship('Run', back_populates='instance', order_by='desc(Run.created)', lazy='select')
    recipes = relationship(
        'RecipeOrder',
        back_populates='instance',
        order_by='RecipeOrder.created'
    )

    def __repr__(self):
        return "<Instance(name='%s', owner='%s')>" % (self.name, self.owner.name)

    def get_active_recipes(self):
        """
        Fetch a list of active recipes which are actively ascribed to this instance.
        :return:
        """
        recipes = list()
        for recipe_order in self.recipes:
            if recipe_order.recipe.active:
                recipes.append(recipe_order.recipe)
        return recipes

    def is_visible_to_user(self, user):
        if self.owner_uid is user.uid:
            return True
        for user_privilege in self.privileged_users:
            if user_privilege.user_uid is user.uid:
                return True
        return False

    def is_editable_by_user(self, user):
        if self.owner_uid is user.uid:
            return True
        for user_privilege in self.privileged_users:
            if user_privilege.user_uid is user.uid and user_privilege.allowed_to_edit:
                return True
        return False

    def runs_recipe(self, recipe, only_consider_active=True):
        for recipe_order in self.recipes:
            if recipe == recipe_order.recipe and (not only_consider_active or recipe_order.recipe.active):
                return True
        return False

    def get_latest_run(self, recipe=None, only_include_successful_runs=False):
        for run in self.runs:
            if recipe is None or run.recipe is recipe:
                if not only_include_successful_runs or run.status == RunStatusEnum.success:
                    return run
        return None

    def get_latest_runs(self, n=10, recipe=None, only_include_successful_runs=False):
        n_runs = []
        for run in self.runs:
            if recipe is None or run.recipe is recipe:
                if not only_include_successful_runs or run.status == RunStatusEnum.success:
                    n_runs.append(run)
                    if len(n_runs) == n:
                        break
        return n_runs

    def jsonify(self, include_latest_run=False, recipe=None):
        if include_latest_run:
            latest_run = self.get_latest_run(recipe)
            return {
                'uid': self.uid,
                'created': self.created,
                'name': self.name,
                'description': self.description,
                'owner': self.owner.jsonify(),
                'latest_run': False if latest_run is None else latest_run.jsonify()
            }
        else:
            return {
                'uid': self.uid,
                'created': self.created,
                'name': self.name,
                'description': self.description,
                'owner': self.owner.jsonify()
            }


class RecipeOrder(base):
    __tablename__ = 'recipe2instance'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    recipe_uid = Column(Integer, ForeignKey('recipe.uid'))
    recipe = relationship('Recipe', back_populates='instances')
    instance_uid = Column(Integer, ForeignKey('instance.uid'))
    instance = relationship('Instance', back_populates='recipes')
    cookies_from_last_run = Column(Text, default='{}')

    def __repr__(self):
        return "<RecipeOrder(recipe='%s', instance='%s')>" % (self.recipe.name, self.instance.name)

    def jsonify(self):
        return {
            'uid': self.uid,
            'created': self.created,
            'recipe': self.recipe.jsonify(),
            'instance': self.instance.jsonify(),
            'cookies_from_last_run': self.cookies_from_last_run
        }


class Recipe(base):
    __tablename__ = 'recipe'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    name = Column(String(256))
    description = Column(Text)
    active = Column(Boolean, default=False)
    cookies = Column(Boolean, default=False)
    interval = Column(Integer, default=15)
    owner_uid = Column(Integer, ForeignKey('user.uid'))
    owner = relationship(User, back_populates='recipes_owned')
    privileged_users = relationship(
        UserRecipePrivilege,
        back_populates='recipe',
        order_by='UserRecipePrivilege.created'
    )
    steps = relationship('RecipeStep', back_populates='recipe', order_by='RecipeStep.sort')
    runs = relationship('Run', back_populates='recipe', order_by='desc(Run.created)', lazy='select')
    instances = relationship(
        RecipeOrder,
        back_populates='recipe',
        order_by='RecipeOrder.created'
    )

    def __repr__(self):
        return "<Recipe(name='%s', owner='%s', interval='%d min', active='%d')>" % \
               (self.name, self.owner.name, self.interval, self.active)

    def get_active_steps(self):
        """
        Fetch the ordered list of active steps from this recipe.
        :return:
        """
        steps = list()
        for step in self.steps:
            if step.active:
                steps.append(step)
        return steps

    def get_average_runtime(self):
        if len(self.runs) > 0:
            summed_runtime = 0
            for run in self.runs:
                summed_runtime = summed_runtime + run.runtime
            return round(summed_runtime/len(self.runs))
        return 0

    def is_visible_to_user(self, user):
        if self.owner_uid is user.uid:
            return True
        for user_privilege in self.privileged_users:
            if user_privilege.user_uid is user.uid:
                return True
        return False

    def is_editable_by_user(self, user):
        if self.owner_uid is user.uid:
            return True
        for user_privilege in self.privileged_users:
            if user_privilege.user_uid is user.uid and user_privilege.allowed_to_edit:
                return True
        return False

    def runs_on_instance(self, instance):
        for recipe_order in self.instances:
            if instance == recipe_order.instance:
                return True
        return False

    def get_latest_run(self, instance=None, only_include_successful_runs=False):
        for run in self.runs:
            if instance is None or run.instance is instance:
                if not only_include_successful_runs or run.status == RunStatusEnum.success:
                    return run
        return None

    def get_latest_runs(self, n=10, instance=None, only_include_successful_runs=False):
        n_runs = []
        for run in self.runs:
            if instance is None or run.instance is instance:
                if not only_include_successful_runs or run.status == RunStatusEnum.success:
                    n_runs.append(run)
                    if len(n_runs) == n:
                        break
        return n_runs

    def jsonify(self, include_latest_run=False, instance=None):
        if include_latest_run:
            latest_run = self.get_latest_run(instance)
            return {
                'uid': self.uid,
                'created': self.created,
                'name': self.name,
                'description': self.description,
                'active': self.active,
                'interval': self.interval,
                'cookies': self.cookies,
                'owner': self.owner.jsonify(),
                'latest_run': False if latest_run is None else latest_run.jsonify()
            }
        else:
            return {
                'uid': self.uid,
                'created': self.created,
                'name': self.name,
                'description': self.description,
                'active': self.active,
                'interval': self.interval,
                'cookies': self.cookies,
                'owner': self.owner.jsonify()
            }


class RecipeStep(base):
    __tablename__ = 'recipestep'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    sort = Column(Integer)
    type = Column(Enum(RecipeStepTypeEnum), default=RecipeStepTypeEnum.log)
    value = Column(Text)
    use_random_item_instead_of_value = Column(Boolean, default=False)
    use_data_item_instead_of_value = Column(Integer, default=0)
    items = relationship('RecipeStepItem', back_populates='step', order_by='RecipeStepItem.created')
    active = Column(Boolean, default=False)
    recipe_uid = Column(Integer, ForeignKey('recipe.uid'))
    recipe = relationship(Recipe, back_populates='steps')
    data = relationship('Data', back_populates='step', lazy='select')
    temp_result = None

    def __repr__(self):
        return "<Step(recipe='%s', sort='%d', type='%s', active='%d')>" % \
               (self.recipe.name, self.sort, self.type, self.active)

    def find_random_item(self):
        """
        Randomly select one of the RecipeStepItems
        :return:
        """
        return random.choice(self.items)

    def run(self, config, run, prior_step=None):
        """
        Do the magic that this step promises to do
        :param config:
        :param run:
        :param prior_step:
        :return:
        """
        if self.use_data_item_instead_of_value > 0:
            data_item_step_sort = int(self.use_data_item_instead_of_value)
            for data in run.data:
                if data.step.sort is data_item_step_sort:
                    self.value = str(data.value)
                    run.log.append(Log(message='"' + data.value + '" as value loaded from data'))
                    break
        elif self.use_random_item_instead_of_value:
            item = self.find_random_item()
            self.value = str(item.value)
            self.data.append(Data(run=run, value=self.value))
            run.log.append(Log(message='"' + item.value + '" randomly selected'))
        return run.process(config, self, prior_step)

    def jsonify(self):
        return {
            'uid': self.uid,
            'created': self.created,
            'sort': self.sort,
            'type': self.type.name,
            'value': self.value,
            'use_random_item_instead_of_value': self.use_random_item_instead_of_value,
            'use_data_item_instead_of_value': self.use_data_item_instead_of_value,
            'active': self.active,
            'recipe': self.recipe.jsonify()
        }


class RecipeStepItem(base):
    __tablename__ = 'recipestepitem'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    value = Column(String(256))
    step_uid = Column(Integer, ForeignKey('recipestep.uid'))
    step = relationship(RecipeStep, back_populates='items')

    def __repr__(self):
        return "<Item(value='%s', step='%s', recipe='%s')>" % (self.value, self.step.type, self.step.recipe.name)

    def jsonify(self):
        return {
            'uid': self.uid,
            'created': self.created,
            'value': self.value,
            'step': self.step.jsonify()
        }


class RunStatusEnum(enum.Enum):
    success = 0
    error = 1
    config_error = 3
    command_not_found = 127
    in_progress = -1


class Run(base):
    __tablename__ = 'run'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    runtime = Column(Integer, default=0)
    instance_uid = Column(Integer, ForeignKey('instance.uid'))
    instance = relationship('Instance', back_populates='runs')
    recipe_uid = Column(Integer, ForeignKey('recipe.uid'))
    recipe = relationship('Recipe', back_populates='runs')
    status = Column(Enum(RunStatusEnum), default=RunStatusEnum.success)
    log = relationship('Log', back_populates='run', order_by='Log.created, Log.uid', lazy='select')
    data = relationship('Data', back_populates='run', order_by='Data.created, Data.uid', lazy='select')
    __emulator = Emulator()

    def __repr__(self):
        return "<Run(date='%s', recipe='%s', instance='%s', status='%s')>" % \
               (self.created, self.recipe.name, self.instance.name, self.status)

    def get_recipe_order(self):
        for temp_order in self.recipe.instances:
            if temp_order.instance is self.instance:
                return temp_order
        return None

    def process(self, config, step, prior_step=None):
        """
        Processes the actual step handling and forwards it to the emulator
        :param config:
        :param step:
        :param prior_step:
        :return:
        """
        return self.__emulator.run(config, self, step, prior_step)

    def end_session(self):
        return self.__emulator.close_session(self)

    def jsonify(self, include_log=False, include_data=False):
        temp = {
            'uid': self.uid,
            'created': self.created,
            'runtime': self.runtime,
            'instance': self.instance.jsonify(),
            'recipe': self.recipe.jsonify(),
            'status': self.status.name
        }
        if include_log:
            temp['log'] = []
            for temp_log in self.log:
                temp['log'].append(temp_log.jsonify())
        if include_data:
            temp['data'] = []
            for temp_data in self.data:
                temp['data'].append(temp_data.jsonify())
        return temp


class LogTypeEnum(enum.Enum):
    info = 1
    warning = 2
    error = 3


class Log(base):
    __tablename__ = 'log'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    type = Column(Enum(LogTypeEnum), default=LogTypeEnum.info)
    message = Column(Text)
    run_uid = Column(Integer, ForeignKey('run.uid'))
    run = relationship(Run, back_populates='log')

    def __repr__(self):
        return "<Log(date='%s', recipe='%s', type='%s', message='%s')>" % \
               (self.created, self.run.recipe.name, self.type, self.message)

    def jsonify(self):
        return {
            'uid': self.uid,
            'created': self.created,
            'type': self.type.name,
            'message': self.message,
            'run': self.run.jsonify()
        }


class Data(base):
    __tablename__ = 'data'
    uid = Column(Integer, primary_key=True)
    created = Column(DateTime, default=func.now())
    value = Column(Text)
    run_uid = Column(Integer, ForeignKey('run.uid'))
    run = relationship(Run, back_populates='data')
    step_uid = Column(Integer, ForeignKey('recipestep.uid'))
    step = relationship(RecipeStep, back_populates='data')

    def __repr__(self):
        return "<Data(date='%s', recipe='%s', step='%s', value='%s')>" % \
               (self.created, self.run.recipe.name, self.step.sort, self.value)

    def jsonify(self):
        return {
            'uid': self.uid,
            'created': self.created,
            'value': self.value,
            'run': self.run.jsonify(),
            'step': self.step.jsonify()
        }
