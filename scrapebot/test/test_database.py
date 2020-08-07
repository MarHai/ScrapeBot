import pytest
from datetime import datetime
from scrapebot.database import *
from scrapebot.emulate import RecipeStepTypeEnum


@pytest.fixture
def new_user():
    return make_user()


def make_user():
    user = User()
    user.created = datetime.now()
    user.uid = random.randint(1, 65535)
    user.active = True
    return user


@pytest.fixture
def new_user_instance_privilege(new_user, new_instance):
    return make_user_instance_privilege(new_user, new_instance)


def make_user_instance_privilege(user, instance):
    privilege = UserInstancePrivilege()
    privilege.created = datetime.now()
    privilege.uid = random.randint(1, 65535)
    privilege.user = user
    privilege.user_uid = user.uid
    privilege.instance = instance
    privilege.instance_uid = instance.uid
    privilege.allowed_to_edit = False
    return privilege


@pytest.fixture
def new_user_recipe_privilege(new_user, new_recipe):
    return make_user_recipe_privilege(new_user, new_recipe)


def make_user_recipe_privilege(user, recipe):
    privilege = UserRecipePrivilege()
    privilege.created = datetime.now()
    privilege.uid = random.randint(1, 65535)
    privilege.user = user
    privilege.user_uid = user.uid
    privilege.recipe = recipe
    privilege.recipe_uid = recipe.uid
    privilege.allowed_to_edit = False
    return privilege


@pytest.fixture
def new_instance(new_user):
    return make_instance(new_user)


def make_instance(user):
    instance = Instance()
    instance.created = datetime.now()
    instance.uid = random.randint(1, 65535)
    instance.owner = user
    instance.owner_uid = user.uid
    return instance


@pytest.fixture
def new_recipe_order(new_instance, new_recipe):
    return make_recipe_order(new_instance, new_recipe)


def make_recipe_order(instance, recipe):
    order = RecipeOrder()
    order.created = datetime.now()
    order.uid = random.randint(1, 65535)
    order.instance = instance
    order.instance_uid = instance.uid
    order.recipe = recipe
    order.recipe_uid = recipe.uid
    return order


@pytest.fixture
def new_recipe(new_user):
    return make_recipe(new_user)


def make_recipe(user):
    recipe = Recipe()
    recipe.created = datetime.now()
    recipe.uid = random.randint(1, 65535)
    recipe.owner = user
    recipe.owner_uid = user.uid
    recipe.interval = 15
    recipe.active = True
    recipe.cookies = False
    return recipe


@pytest.fixture
def new_recipe_step(new_recipe):
    return make_recipe_step(new_recipe)


def make_recipe_step(recipe):
    step = RecipeStep()
    step.created = datetime.now()
    step.uid = random.randint(1, 65535)
    step.sort = random.randint(1, 30)
    step.recipe = recipe
    step.recipe_uid = recipe.uid
    step.use_random_item_instead_of_value = False
    step.use_data_item_instead_of_value = 0
    step.type = RecipeStepTypeEnum.log
    step.value = 'test log from step'
    step.active = True
    return step


@pytest.fixture
def new_recipe_step_item(new_recipe_step):
    return make_recipe_step_item(new_recipe_step)


def make_recipe_step_item(recipe_step):
    item = RecipeStepItem()
    item.created = datetime.now()
    item.uid = random.randint(1, 65535)
    item.step = recipe_step
    item.step_uid = recipe_step.uid
    item.value = 'test item value'
    return item


@pytest.fixture
def new_run(new_recipe, new_instance):
    return make_run(new_recipe, new_instance)


def make_run(recipe, instance):
    run = Run()
    run.created = datetime.now()
    run.uid = random.randint(1, 65535)
    run.runtime = random.randint(5, 50)
    run.recipe = recipe
    run.recipe_uid = recipe.uid
    run.instance = instance
    run.instance_uid = instance.uid
    run.status = RunStatusEnum.success
    return run


@pytest.fixture
def new_log(new_run):
    return make_log(new_run)


def make_log(run):
    log = Log()
    log.created = datetime.now()
    log.uid = random.randint(1, 65535)
    log.type = LogTypeEnum.info
    log.run = run
    log.run_uid = run.uid
    log.message = 'test log entry'
    return log


@pytest.fixture
def new_data(new_run, new_recipe_step):
    return make_data(new_run, new_recipe_step)


def make_data(run, recipe_step):
    data = Data()
    data.created = datetime.now()
    data.uid = random.randint(1, 65535)
    data.run = run
    data.run_uid = run.uid
    data.step = recipe_step
    data.step_uid = recipe_step.uid
    data.value = 'test value'
    return data


class TestUser(object):
    def test_jsonify(self, new_user):
        assert type(new_user.get_id()) is str
        assert isinstance(new_user.jsonify(), dict)

    def test_password_creation(self, new_user):
        password = new_user.create_password()
        assert len(password) >= 10
        assert new_user.check_password(password)


class TestUserInstancePrivilege(object):
    def test_jsonify(self, new_user_instance_privilege):
        assert isinstance(new_user_instance_privilege.jsonify(), dict)


class UserRecipePrivilege(object):
    def test_jsonify(self, new_user_recipe_privilege):
        assert isinstance(new_user_recipe_privilege.jsonify(), dict)


class TestInstance(object):
    def test_jsonify(self, new_instance):
        assert isinstance(new_instance.jsonify(), dict)

    def test_active_recipes(self, new_recipe_order):
        new_recipe_order.recipe.active = True
        instance = new_recipe_order.instance
        assert instance.get_active_recipes().__contains__(new_recipe_order.recipe)

    def test_inactive_recipes(self, new_recipe_order):
        new_recipe_order.recipe.active = False
        instance = new_recipe_order.instance
        assert instance.get_active_recipes().__contains__(new_recipe_order.recipe) is not True

    def test_user_visibility(self, new_instance):
        assert new_instance.is_visible_to_user(new_instance.owner)
        assert new_instance.is_visible_to_user(make_user()) is not True

    def test_user_editability(self, new_instance):
        assert new_instance.is_editable_by_user(new_instance.owner)
        assert new_instance.is_editable_by_user(make_user()) is False

    def test_runs_recipe(self, new_recipe_order):
        instance = new_recipe_order.instance
        assert instance.runs_recipe(new_recipe_order.recipe)
        assert instance.runs_recipe(make_recipe(instance.owner)) is False

    def test_get_latest_run(self, new_run):
        instance = new_run.instance
        assert instance.get_latest_run() is not None
        assert instance.get_latest_run(make_recipe(instance.owner)) is None

    def test_get_latest_runs(self, new_run):
        instance = new_run.instance
        assert instance.get_latest_runs().__len__() == 1


class TestRecipeOrder(object):
    def test_jsonify(self, new_recipe_order):
        assert isinstance(new_recipe_order.jsonify(), dict)


class TestRecipe(object):
    def test_jsonify(self, new_recipe):
        assert isinstance(new_recipe.jsonify(), dict)

    def test_get_active_steps(self, new_recipe_step):
        new_recipe_step.active = True
        recipe = new_recipe_step.recipe
        assert recipe.get_active_steps().__len__() == 1

    def test_get_inactive_steps(self, new_recipe_step):
        new_recipe_step.active = False
        recipe = new_recipe_step.recipe
        assert recipe.get_active_steps().__len__() == 0

    def test_get_average_runtime(self, new_run):
        recipe = new_run.recipe
        assert recipe.get_average_runtime() >= 0

    def test_user_visibility(self, new_recipe):
        assert new_recipe.is_visible_to_user(new_recipe.owner)
        assert new_recipe.is_visible_to_user(make_user()) is not True

    def test_user_editability(self, new_recipe):
        assert new_recipe.is_editable_by_user(new_recipe.owner)
        assert new_recipe.is_editable_by_user(make_user()) is False

    def test_runs_on_instance(self, new_recipe_order):
        recipe = new_recipe_order.recipe
        assert recipe.runs_on_instance(new_recipe_order.instance)
        assert recipe.runs_on_instance(make_instance(recipe.owner)) is False

    def test_get_latest_run(self, new_run):
        recipe = new_run.recipe
        assert recipe.get_latest_run() is not None
        assert recipe.get_latest_run(make_instance(recipe.owner)) is None

    def test_get_latest_runs(self, new_run):
        recipe = new_run.recipe
        assert recipe.get_latest_runs().__len__() == 1


class TestRecipeStep(object):
    @pytest.mark.parametrize('new_type', [RecipeStepTypeEnum.scroll_to, RecipeStepTypeEnum.write_slowly])
    def test_jsonify(self, new_recipe_step, new_type):
        assert isinstance(new_recipe_step.jsonify(), dict)

    def test_find_random_item(self, new_recipe_step):
        with pytest.raises(IndexError):
            assert new_recipe_step.find_random_item()
        make_recipe_step_item(new_recipe_step)
        new_recipe_step.use_random_item_instead_of_value = True
        assert new_recipe_step.find_random_item()


class TestRecipeStepItem(object):
    def test_jsonify(self, new_recipe_step_item):
        assert isinstance(new_recipe_step_item.jsonify(), dict)


class TestRun(object):
    @pytest.mark.parametrize('new_status', [RunStatusEnum.success, RunStatusEnum.error])
    def test_jsonify(self, new_run, new_status):
        assert isinstance(new_run.jsonify(), dict)

    def test_get_recipe_order(self, new_recipe_order):
        run = make_run(new_recipe_order.recipe, new_recipe_order.instance)
        assert run.get_recipe_order() is new_recipe_order


class TestLog(object):
    @pytest.mark.parametrize('new_type', [LogTypeEnum.info, LogTypeEnum.error])
    def test_jsonify(self, new_log, new_type):
        assert isinstance(new_log.jsonify(), dict)


class TestData(object):
    def test_jsonify(self, new_data):
        assert isinstance(new_data.jsonify(), dict)
