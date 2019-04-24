from flask import jsonify, request
from web import db
from scrapebot.database import Run, Instance, Recipe, UserRecipePrivilege, RecipeOrder
from flask_login import current_user, login_required
from web.json import bp
from sqlalchemy import func, or_


@bp.route('/json/instances', methods=['GET', 'POST'])
@login_required
def instances():
    recipe_uids = []
    json = request.get_json()
    if json is not None and 'uids' in json:
        recipe_uids = json['uids']
    data = []
    for instance in current_user.instances_owned:
        if len(recipe_uids) > 0:
            for order in instance.recipes:
                if order.recipe_uid in recipe_uids:
                    data.append(instance.jsonify(include_latest_run=True, recipe=order.recipe))
        else:
            data.append(instance.jsonify(include_latest_run=True))
    for privilege in current_user.instance_privileges:
        if len(recipe_uids) > 0:
            for order in privilege.instance.recipes:
                if order.recipe_uid in recipe_uids:
                    data.append(privilege.instance.jsonify(include_latest_run=True, recipe=order.recipe))
        else:
            data.append(privilege.instance.jsonify(include_latest_run=True))
    return jsonify({'status': 200, 'count': len(data), 'data': data})


@bp.route('/json/recipes', methods=['GET', 'POST'])
@login_required
def recipes():
    data = []
    for (recipe, latest_run_uid) in db.session.query(
            Recipe,
            func.max(Run.uid)
        ).outerjoin(
            UserRecipePrivilege,
            UserRecipePrivilege.recipe_uid == Recipe.uid
        ).outerjoin(
            Run,
            Run.recipe_uid == Recipe.uid
        ).outerjoin(
            RecipeOrder,
            RecipeOrder.recipe_uid == Recipe.uid
        ).filter(
            or_(
                Recipe.owner_uid == current_user.uid,
                UserRecipePrivilege.user_uid == current_user.uid
            ),
            # careful: the following is a filter statement based on an IF
            RecipeOrder.instance_uid.in_(request.get_json()['uids']) if
            request.get_json() is not None and 'uids' in request.get_json() else
            1 == 1
        ).group_by(Recipe):
        recipe_json = recipe.jsonify()
        if latest_run_uid is not None:
            run = db.session.query(Run).filter(Run.uid == latest_run_uid).one_or_none()
            if run is not None:
                recipe_json['latest_run'] = run.jsonify()
        data.append(recipe_json)
    return jsonify({'status': 200, 'count': len(data), 'data': data})


@bp.route('/json/run/<run_uid>')
@login_required
def run(run_uid):
    temp_run = db.session.query(Run).filter(Run.uid == int(run_uid)).first()
    if temp_run.recipe.is_visible_to_user(current_user) and temp_run.instance.is_visible_to_user(current_user):
        return jsonify({'status': 200, 'run': temp_run.jsonify(True, True)})
    return jsonify({'status': 403, 'message': 'No permission to view this run.'})


@bp.route('/json/runs/<recipe_uid>-<instance_uid>', defaults={'page': 1})
@bp.route('/json/runs/<recipe_uid>-<instance_uid>/<page>')
@login_required
def runs(recipe_uid, instance_uid, page):
    data = []
    temp_runs = db.session.query(Run)
    if int(recipe_uid) > 0:
        temp_runs = temp_runs.filter(Run.recipe_uid == int(recipe_uid))
    if int(instance_uid) > 0:
        temp_runs = temp_runs.filter(Run.instance_uid == int(instance_uid))
    temp_runs = temp_runs.order_by(Run.created.desc()).paginate(int(page), 10, error_out=False)
    for temp_run in temp_runs.items:
        if temp_run.recipe.is_visible_to_user(current_user) and temp_run.instance.is_visible_to_user(current_user):
            data.append(temp_run.jsonify())
    return jsonify({
        'status': 200,
        'count': len(data),
        'data': data,
        'page': page,
        'has_next': temp_runs.has_next,
        'has_prev': temp_runs.has_prev,
        'next_page': temp_runs.next_num,
        'prev_page': temp_runs.prev_num
    })


@bp.route('/json/instance/<instance_uid>/chart')
@login_required
def instance_chart(instance_uid):
    temp_instance = db.session.query(Instance).filter(Instance.uid == instance_uid).first()
    if temp_instance is not None and temp_instance.is_visible_to_user(current_user):
        data = db.session.query(Recipe.name, func.date(Run.created), func.count(Run.uid))\
            .select_from(Run)\
            .filter(Run.instance_uid == instance_uid)\
            .join(Run.recipe)\
            .group_by(Recipe, func.date(Run.created))\
            .order_by(func.date(Run.created))
        datasets = dict()
        labels = []
        for row in data:
            if str(row[1]) not in labels:
                labels.append(str(row[1]))
            if row[0] not in datasets:
                datasets[row[0]] = []
            datasets[row[0]].append(row[2])
        return jsonify({
            'status': 200,
            'instance': temp_instance.name,
            'labels': labels,
            'datasets': [{'label': name, 'data': values} for name, values in datasets.items()]
        })
    return jsonify({'status': 403, 'message': 'No permission to view this instance.'})
