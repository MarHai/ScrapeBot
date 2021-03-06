from time import time
import pytest
from scrapebot.test.test_database import *
from scrapebot.test.test_configuration import *
from scrapebot.emulate import RecipeStepTypeEnum, Emulator
from scrapebot.database import base, Recipe, RecipeStep, Instance, User, RecipeOrder, Run, RunStatusEnum
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


@pytest.fixture
def new_emulator():
    return make_emulator()


def make_emulator():
    emulator = Emulator()
    return emulator


@pytest.fixture(scope='session')
def connect_db():
    engine = create_engine('sqlite:///:memory:', encoding='utf-8')
    base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)


def test_step_run_with_random_item(new_recipe_step_item):
    new_recipe_step_item.step.use_random_item_instead_of_value = True
    run = make_run(new_recipe_step_item.step.recipe, make_instance(new_recipe_step_item.step.recipe.owner))
    try:
        new_recipe_step_item.step.run(None, run)
    except:
        assert run.data.__len__() > 0


def test_step_run_with_fixed_item(new_recipe_step_item):
    new_recipe_step_item.step.use_random_item_instead_of_value = False
    run = make_run(new_recipe_step_item.step.recipe, make_instance(new_recipe_step_item.step.recipe.owner))
    try:
        new_recipe_step_item.step.run(None, run)
    except:
        assert run.data.__len__() == 0


class TestEmulator(object):
    def test_run_init_firefox(self, new_configuration, new_emulator, new_run, new_recipe_step):
        handler = new_emulator.run(new_configuration, new_run, new_recipe_step)
        assert handler is RunStatusEnum.success
        new_emulator.close_session(new_run)

    def test_run_data(self, new_configuration, new_emulator, new_run, new_user):
        recipe = make_recipe(new_user)
        step = make_recipe_step(recipe)
        step.type = RecipeStepTypeEnum.data
        step.value = 42
        handler = new_emulator.run(new_configuration, new_run, step, make_recipe_step(recipe))
        assert handler is RunStatusEnum.success
        assert new_run.data.__len__() == 1
        assert new_run.data[0].value == step.value

    def test_run_pause(self, new_configuration, new_emulator, new_run, new_user):
        recipe = make_recipe(new_user)
        step = make_recipe_step(recipe)
        step.type = RecipeStepTypeEnum.pause
        step.value = 5
        t0 = time()
        handler = new_emulator.run(new_configuration, new_run, step, make_recipe_step(recipe))
        assert handler is RunStatusEnum.success
        assert time() - t0 >= (step.value*.75)

    def test_run_google(self, connect_db, new_configuration):
        user = User(email='mario@haim.it', password='Ak&f(8-fL:')
        instance = Instance(name='demo_instance')
        user.instances_owned.append(instance)
        recipe = Recipe(name='google', active=True)
        steps = [
            RecipeStep(sort=1, type=RecipeStepTypeEnum.navigate, value='https://www.google.com'),
            RecipeStep(sort=2, type=RecipeStepTypeEnum.find_by_name, value='q'),
            RecipeStep(sort=3, type=RecipeStepTypeEnum.write_slowly, value='computational methods'),
            RecipeStep(sort=4, type=RecipeStepTypeEnum.submit),
            RecipeStep(sort=5, type=RecipeStepTypeEnum.pause, value='2'),
            RecipeStep(sort=6, type=RecipeStepTypeEnum.scroll_to, value='-1'),
            RecipeStep(sort=7, type=RecipeStepTypeEnum.find_by_css,
                       value='#rso div[data-ved] div.r a:not([class]):not([id])'),
            RecipeStep(sort=8, type=RecipeStepTypeEnum.get_attributes, value='href')
        ]
        for step in steps:
            recipe.steps.append(step)
        user.recipes_owned.append(recipe)
        connect_db.add(user)
        connect_db.add(RecipeOrder(recipe=recipe, instance=instance))
        connect_db.commit()

        assert connect_db.query(Instance).count() == 1
        assert connect_db.query(Recipe).count() == 1
        assert connect_db.query(User).count() == 1
        assert connect_db.query(RecipeStep).count() == steps.__len__()

        run = Run(instance=instance, recipe=recipe)
        for i in range(0, steps.__len__()):
            assert steps[i].run(new_configuration, run, (None if i == 0 else steps[i-1])) is RunStatusEnum.success
            if steps[i].temp_result is None and i > 0 and steps[i-1].temp_result is not None:
                steps[i].temp_result = steps[i-1].temp_result
        run.end_session()
        connect_db.add(run)
        connect_db.commit()

        run = connect_db.query(Run).one_or_none()
        assert run is not None
        assert run.data.__len__() > 0
        last_data_value = run.data.pop().value
        assert last_data_value.__contains__('http')
