import sys
import time
from datetime import datetime
from random import shuffle
from setup import get_config, get_engine, get_db
from scrapebot.database import *


print('[' + str(datetime.now()) + '] ScrapeBot initiated (this is server time)')
config = get_config(False)
db = get_db(get_engine(config))

this_instance_name = config.get('Instance', 'name')
this_instance = None
try:
    if this_instance_name == '' or db.query(Instance).filter(Instance.name == this_instance_name).count() == 0:
        print('Error: Instance not found')
        exit(1)
    else:
        print('Authenticated as instance "' + this_instance_name + '"')
        this_instance = db.query(Instance).filter(Instance.name == this_instance_name).one()
except:
    print('Error: Initial database query failed')
    error = sys.exc_info()[0]
    if error is not None:
        print('- ' + str(error))
    exit(1)

recipes = this_instance.get_active_recipes()
if len(recipes) > 0:
    shuffle(recipes)
    print(str(len(recipes)) + ' active recipe(s) found to be handled by this instance')
    for recipe in recipes:
        steps = recipe.get_active_steps()
        if len(steps) > 0:
            latest_run = recipe.get_latest_run(this_instance)
            # to compare with an adequate timezone, we use the same database function as CREATE does
            now = db.query(func.now()).first()[0]
            if latest_run is not None and \
               (int(time.mktime(now.timetuple()) - time.mktime(latest_run.created.timetuple()))/60) < recipe.interval:

                print('# skipping ' + recipe.name + ' since latest run was less than ' + str(recipe.interval) +
                      ' minute(s) ago')
            else:
                if latest_run is None:
                    print('# ' + recipe.name + ' (' + str(len(steps)) +
                          ' active step(s) found, never run on this instance)')
                else:
                    print('# ' + recipe.name + ' (' + str(len(steps)) +
                          ' active step(s) found, last run on this instance at ' + str(latest_run.created) + ')')
                status = RunStatusEnum.in_progress
                run = Run(instance=this_instance, recipe=recipe, status=status)
                db.add(run)
                prior_step = None
                for step in steps:
                    try:
                        status = step.run(config, run, prior_step)
                    except:
                        error = sys.exc_info()[0]
                        if error is not None:
                            error = str(error).strip('<>')
                            print('- Fatal ERROR: ' + error)
                            run.log.append(Log(message=error, type=LogTypeEnum.error))
                        status = RunStatusEnum.error
                    if status is not RunStatusEnum.success:
                        run.status = status
                        break
                    if step.temp_result is None and prior_step is not None and prior_step.temp_result is not None:
                        step.temp_result = prior_step.temp_result
                    prior_step = step
                run.end_session()
                if run.status == RunStatusEnum.in_progress:
                    run.status = RunStatusEnum.success
                db.commit()
        else:
            print('# skipping ' + recipe.name + ' since no active steps were found')
    print('All done')
else:
    print('No (active) recipes found (actively) ascribed to this instance')
