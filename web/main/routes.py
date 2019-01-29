from datetime import date
from flask import render_template, flash, redirect, url_for, request
from scrapebot.database import *
from web import db, mail
from flask_login import current_user, login_required
from flask_mail import Message
from web.main import bp
from web.main.forms import *


@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('main/dashboard.html')


@bp.route('/imprint')
def imprint():
    return render_template('main/imprint.html')


@bp.route('/instance/<instance_uid>', methods=['GET', 'POST'])
@login_required
def instance(instance_uid):
    temp_instance = db.session.query(Instance).filter(Instance.uid == instance_uid).first()
    if temp_instance is not None and temp_instance.is_visible_to_user(current_user):
        user_recipes = current_user.recipes_owned
        for privilege in current_user.recipe_privileges:
            if privilege.allowed_to_edit:
                user_recipes.append(privilege.recipe)
        form_privilege = PrivilegeForm()
        if form_privilege.validate_on_submit() and form_privilege.email.data:
            if temp_instance.owner_uid is current_user.uid:
                temp_user = db.session.query(User).filter(User.email == form_privilege.email.data).first()
                if temp_user is None or temp_user is temp_instance.owner:
                    flash('User not found')
                else:
                    temp_privilege = db.session.query(UserInstancePrivilege)\
                        .filter(UserInstancePrivilege.user == temp_user, UserInstancePrivilege.instance == temp_instance)\
                        .first()
                    if temp_privilege is None:
                        temp_privilege = UserInstancePrivilege(user=temp_user,
                                                               allowed_to_edit=form_privilege.allowed_to_edit.data)
                        temp_instance.privileged_users.append(temp_privilege)
                    elif not temp_privilege.allowed_to_edit and form_privilege.allowed_to_edit.data:
                        temp_privilege.allowed_to_edit = True
                    else:
                        flash('Access already granted')
                        return redirect(url_for('main.instance', instance_uid=instance_uid))
                    db.session.commit()
                    msg = Message('Access to new ScrapeBot instance granted', sender='ScrapeBot <scrapebot@haim.it>',
                                  recipients=[temp_user.email])
                    msg.body = render_template('email/privilege_instance.txt',
                                               user=temp_user, instance=temp_instance, privilege=temp_privilege)
                    mail.send(msg)
                    flash('Privilege added and user informed via email')
            else:
                flash('You are not allowed to do this as only an instance\'s owner can permit privileges')
            return redirect(url_for('main.instance', instance_uid=instance_uid))
        form = InstanceForm()
        if form.validate_on_submit():
            temp_instance.description = form.description.data
            for temp_recipe in user_recipes:
                temp_order = db.session.query(RecipeOrder).filter(RecipeOrder.recipe == temp_recipe,
                                                                  RecipeOrder.instance == temp_instance).first()
                if request.form.get('recipe_' + str(temp_recipe.uid)) is 'y':
                    if temp_order is None:
                        temp_recipe.instances.append(RecipeOrder(instance=temp_instance))
                elif temp_order is not None:
                    db.session.delete(temp_order)
            db.session.commit()
            return redirect(url_for('main.instance', instance_uid=instance_uid))
        privileged_users = []
        recipes = []
        form.name.data = temp_instance.name
        form.description.data = temp_instance.description
        for temp_recipe in user_recipes:
            recipes.append({
                'uid': temp_recipe.uid,
                'name': temp_recipe.name,
                'interval': temp_recipe.interval,
                'active': temp_instance.runs_recipe(temp_recipe, False),
                'recipe_active': temp_recipe.active
            })
        if temp_instance.owner_uid == current_user.uid:
            for temp_privilege in temp_instance.privileged_users:
                privileged_users.append(temp_privilege.jsonify())
        return render_template('main/instance.html', instance=temp_instance, form=form, recipes=recipes,
                               form_privilege=form_privilege, privileged_users=privileged_users)
    flash('You do not have the permission to view this instance.')
    return render_template('main/dashboard.html')


@bp.route('/instance/<instance_uid>/remove_privilege/<privilege_uid>')
@login_required
def instance_remove_privilege(instance_uid, privilege_uid):
    temp_instance = db.session.query(Instance).filter(Instance.uid == int(instance_uid)).first()
    if temp_instance.owner_uid == current_user.uid:
        temp_privilege = db.session.query(UserInstancePrivilege)\
            .filter(UserInstancePrivilege.uid == int(privilege_uid)).first()
        if temp_privilege is None:
            flash('Privilege not found')
        else:
            db.session.delete(temp_privilege)
            db.session.commit()
            flash('Privilege removed successfully')
    else:
        flash('You do not have the permission to edit privileges on this instance.')
    return redirect(url_for('main.instance', instance_uid=instance_uid))


@bp.route('/recipe', methods=['GET', 'POST'], defaults={'recipe_uid': None})
@bp.route('/recipe/<recipe_uid>', methods=['GET', 'POST'])
@login_required
def recipe(recipe_uid):
    temp_recipe: Recipe = None
    if recipe_uid is not None:
        temp_recipe = db.session.query(Recipe).filter(Recipe.uid == int(recipe_uid)).first()
        if not temp_recipe.is_visible_to_user(current_user):
            flash('You do not have the permission to view this recipe.')
            return redirect(url_for('main.dashboard'))
    instances = current_user.instances_owned
    for privilege in current_user.instance_privileges:
        if privilege.allowed_to_edit:
            instances.append(privilege.instance)
    form = RecipeForm()
    if form.validate_on_submit() and form.name.data:
        if recipe_uid is None:
            temp_recipe = Recipe()
        temp_recipe.name = form.name.data
        temp_recipe.description = form.description.data
        temp_recipe.interval = form.interval.data
        temp_recipe.cookies = form.cookies.data
        temp_recipe.active = form.active.data
        for temp_instance in instances:
            if request.form.get('instance_' + str(temp_instance.uid)) is 'y':
                temp_order = None
                if recipe_uid is not None:
                    temp_order = db.session.query(RecipeOrder).filter(RecipeOrder.recipe == temp_recipe,
                                                                      RecipeOrder.instance == temp_instance).first()
                if temp_order is None:
                    temp_recipe.instances.append(RecipeOrder(instance=temp_instance))
            elif recipe_uid is not None:
                temp_order = db.session.query(RecipeOrder).filter(RecipeOrder.recipe == temp_recipe,
                                                                  RecipeOrder.instance == temp_instance).first()
                if temp_order is not None:
                    db.session.delete(temp_order)
        current_user.recipes_owned.append(temp_recipe)
        db.session.commit()
        if recipe_uid is None:
            temp_recipe = db.session.query(Recipe).filter(Recipe.owner == current_user)\
                .order_by(Recipe.created.desc()).first()
            recipe_uid = temp_recipe.uid
        return redirect(url_for('main.recipe', recipe_uid=recipe_uid))
    form_privilege = PrivilegeForm()
    if form_privilege.validate_on_submit() and form_privilege.email.data:
        if temp_recipe.owner_uid is current_user.uid:
            temp_user = db.session.query(User).filter(User.email == form_privilege.email.data).first()
            if temp_user is None or temp_user is temp_recipe.owner:
                flash('User not found')
            else:
                temp_privilege = db.session.query(UserRecipePrivilege)\
                    .filter(UserRecipePrivilege.user == temp_user, UserRecipePrivilege.recipe == temp_recipe)\
                    .first()
                if temp_privilege is None:
                    temp_privilege = UserRecipePrivilege(user=temp_user, allowed_to_edit=form_privilege.allowed_to_edit.data)
                    temp_recipe.privileged_users.append(temp_privilege)
                elif not temp_privilege.allowed_to_edit and form_privilege.allowed_to_edit.data:
                    temp_privilege.allowed_to_edit = True
                else:
                    flash('Access already granted')
                    return redirect(url_for('main.recipe', recipe_uid=recipe_uid))
                db.session.commit()
                msg = Message('Access to new ScrapeBot recipe granted', sender='ScrapeBot <scrapebot@haim.it>',
                              recipients=[temp_user.email])
                msg.body = render_template('email/privilege_recipe.txt',
                                           user=temp_user, recipe=temp_recipe, privilege=temp_privilege)
                mail.send(msg)
                flash('Privilege added and user informed via email')
        else:
            flash('You are not allowed to do this as only a recipe\'s owner can permit privileges')
        return redirect(url_for('main.recipe', recipe_uid=recipe_uid))
    user_instances = []
    privileged_users = []
    if temp_recipe is None:
        for temp_instance in instances:
            user_instances.append({
                'uid': temp_instance.uid,
                'name': temp_instance.name,
                'active': False
            })
    else:
        form.name.data = temp_recipe.name
        form.description.data = temp_recipe.description
        form.interval.data = temp_recipe.interval
        form.cookies.data = temp_recipe.cookies
        form.active.data = temp_recipe.active
        for temp_instance in instances:
            user_instances.append({
                'uid': temp_instance.uid,
                'name': temp_instance.name,
                'active': temp_instance.runs_recipe(temp_recipe, False)
            })
        if temp_recipe.owner_uid == current_user.uid:
            for temp_privilege in temp_recipe.privileged_users:
                privileged_users.append(temp_privilege.jsonify())
    return render_template('main/recipe.html', form=form, instances=user_instances, recipe=temp_recipe,
                           form_privilege=form_privilege, privileged_users=privileged_users)


@bp.route('/recipe/<recipe_uid>/remove_privilege/<privilege_uid>')
@login_required
def recipe_remove_privilege(recipe_uid, privilege_uid):
    temp_recipe = db.session.query(Recipe).filter(Recipe.uid == int(recipe_uid)).first()
    if temp_recipe.owner_uid == current_user.uid:
        temp_privilege = db.session.query(UserRecipePrivilege)\
            .filter(UserRecipePrivilege.uid == int(privilege_uid)).first()
        if temp_privilege is None:
            flash('Privilege not found')
        else:
            db.session.delete(temp_privilege)
            db.session.commit()
            flash('Privilege removed successfully')
    else:
        flash('You do not have the permission to edit privileges on this recipe.')
    return redirect(url_for('main.recipe', recipe_uid=recipe_uid))


@bp.route('/recipes/multiple/<recipe_uids>', defaults={'deactivate': 0})
@bp.route('/recipes/multiple/<recipe_uids>/<deactivate>')
@login_required
def recipe_multiple_action(recipe_uids, deactivate):
    recipe_uids = [int(uid) for uid in str(recipe_uids).split('-')]
    deactivate = True if int(deactivate) is 1 else False
    changes = 0
    for recipe_uid in recipe_uids:
        temp_recipe = db.session.query(Recipe).filter(Recipe.uid == recipe_uid).first()
        if temp_recipe is not None and temp_recipe.is_editable_by_user(current_user):
            if temp_recipe.active and deactivate:
                temp_recipe.active = False
                changes = changes + 1
            elif not temp_recipe.active and not deactivate:
                temp_recipe.active = True
                changes = changes + 1
    if changes > 0:
        db.session.commit()
        flash(str(changes) + ' recipes ' + ('de' if deactivate else '') + 'activated successfully')
    else:
        flash('No changes necessary or you do not have the permissions to do so (or both).')
    return redirect(url_for('main.dashboard'))


@bp.route('/recipe/<recipe_uid>/duplicate', methods=['GET', 'POST'])
@login_required
def recipe_duplicate(recipe_uid):
    temp_recipe: Recipe = None
    if recipe_uid is not None:
        temp_recipe = db.session.query(Recipe).filter(Recipe.uid == int(recipe_uid)).first()
        if not temp_recipe.is_editable_by_user(current_user):
            flash('You do not have the permission to copy this recipe.')
            return redirect(url_for('main.recipe', recipe_uid=recipe_uid))
    instances = current_user.instances_owned
    for privilege in current_user.instance_privileges:
        if privilege.allowed_to_edit:
            instances.append(privilege.instance)
    form = RecipeDuplicateForm()
    if form.validate_on_submit():
        copies = int(form.amount.data)
        if copies > 0:
            instance_count = 0
            for i in range(1, 1+copies):
                new_recipe = Recipe(
                    name=form.name.data.replace('%i', str(i)).replace('%n', str(copies)),
                    description=form.description.data,
                    active=form.active.data,
                    cookies=temp_recipe.cookies,
                    interval=temp_recipe.interval
                )
                for temp_step in temp_recipe.steps:
                    new_step = RecipeStep(
                        sort=temp_step.sort,
                        type=temp_step.type,
                        value=temp_step.value,
                        use_random_item_instead_of_value=temp_step.use_random_item_instead_of_value,
                        active=temp_step.active
                    )
                    for temp_item in temp_step.items:
                        new_step.items.append(RecipeStepItem(value=temp_item.value))
                    new_recipe.steps.append(new_step)
                if form.user_privileges.data is True:
                    new_recipe.owner = temp_recipe.owner
                    for temp_privilege in temp_recipe.privileged_users:
                        new_recipe.privileged_users.append(UserRecipePrivilege(
                            user=temp_privilege.user,
                            allowed_to_edit=temp_privilege.allowed_to_edit
                        ))
                else:
                    new_recipe.owner = current_user
                instance_count = 0
                for temp_instance in instances:
                    if request.form.get('instance_' + str(temp_instance.uid)) is 'y':
                        instance_count = instance_count + 1
                        new_recipe.instances.append(RecipeOrder(instance=temp_instance))
                db.session.commit()
            flash('Copied "' + temp_recipe.name + '" a total of ' + str(copies) + ' times ' +
                  ('with' if form.user_privileges.data is True else 'without') + ' user privileges ' +
                  (('and applied it to ' + str(instance_count)) if instance_count > 0 else 'but did not apply any') +
                  ' instance(s). The ' + str(copies) + (' recipe is ' if copies is 1 else ' recipes are ') +
                  ('now active' if form.active.data is True else 'not active at the moment') +
                  (' as is' if form.active.data is temp_recipe.active else ', in contrast to') +
                  ' the current recipe.')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid number of copies to create')
    else:
        form.name.data = temp_recipe.name + ' %i/%n'
        form.active.data = temp_recipe.active
        form.description.data = temp_recipe.description + '\n\n' + \
                                'This recipe was copied on ' + str(date.today()) + \
                                ' from "' + temp_recipe.name + '" (' + \
                                url_for('main.recipe', recipe_uid=recipe_uid, _external=True) + ')'
        form.description.data = form.description.data.lstrip()
    user_instances = []
    for temp_instance in instances:
        user_instances.append({
            'uid': temp_instance.uid,
            'name': temp_instance.name,
            'active': temp_instance.runs_recipe(temp_recipe, False)
        })
    return render_template('main/recipe_copy.html', form=form, instances=user_instances, recipe=temp_recipe)


@bp.route('/recipe/<recipe_uid>/step', methods=['GET', 'POST'], defaults={'step_uid': None})
@bp.route('/recipe/<recipe_uid>/step/<step_uid>', methods=['GET', 'POST'])
@login_required
def step(recipe_uid, step_uid):
    temp_recipe = db.session.query(Recipe).filter(Recipe.uid == int(recipe_uid)).first()
    if not temp_recipe.is_visible_to_user(current_user):
        flash('You do not have the permission to view this recipe.')
        return redirect(url_for('main.dashboard'))
    temp_step: RecipeStep = None
    if step_uid is not None:
        temp_step = db.session.query(RecipeStep).filter(RecipeStep.uid == int(step_uid)).first()
        if not temp_step.recipe.is_visible_to_user(current_user):
            flash('You do not have the permission to view this recipe.')
            return redirect(url_for('main.dashboard'))
    form_step = RecipeStepForm()
    if form_step.validate_on_submit():
        if temp_step is None:
            temp_step = RecipeStep()
            temp_step.sort = 1
            for temp_sort in temp_recipe.steps:
                if temp_sort.sort >= temp_step.sort:
                    temp_step.sort = temp_sort.sort + 1
        temp_step.type = RecipeStepTypeEnum[RecipeStepTypeEnum.coerce(form_step.type.data)]
        temp_step.value = form_step.value.data
        temp_step.use_random_item_instead_of_value = form_step.use_random_item_instead_of_value.data
        temp_step.active = form_step.active.data
        if step_uid is None:
            temp_recipe.steps.append(temp_step)
        db.session.commit()
        if step_uid is None:
            temp = db.session.query(RecipeStep)\
                .filter(RecipeStep.recipe_uid == int(recipe_uid), RecipeStep.sort == temp_step.sort)\
                .order_by(RecipeStep.created.desc())\
                .first()
            step_uid = temp.uid
            flash('New step created successfully.')
            if not temp.use_random_item_instead_of_value:
                return redirect(url_for('main.recipe', recipe_uid=recipe_uid))
        else:
            flash('Step updated successfully.')
        return redirect(url_for('main.step', recipe_uid=recipe_uid, step_uid=step_uid))
    if temp_step is not None:
        form_step.type.data = temp_step.type.name
        form_step.value.data = temp_step.value
        form_step.use_random_item_instead_of_value.data = temp_step.use_random_item_instead_of_value
        form_step.active.data = temp_step.active
    return render_template(
        'main/recipe_step.html',
        form_step=form_step,
        form_item=RecipeStepItemForm(),
        recipe=temp_recipe,
        step=temp_step
    )


@bp.route('/step/<step_uid>/move/<direction>')
@login_required
def step_move(step_uid, direction):
    temp_step = db.session.query(RecipeStep).filter(RecipeStep.uid == int(step_uid)).first()
    if not temp_step.recipe.is_visible_to_user(current_user):
        flash('You do not have the permission to view this recipe.')
        return redirect(url_for('main.dashboard'))
    if len(temp_step.recipe.steps) > 1:
        if direction == 'up' and temp_step.sort > 1:
            for temp_step_before in temp_step.recipe.steps:
                if temp_step_before.sort == (temp_step.sort-1):
                    temp_step_before.sort = temp_step.sort
                    temp_step.sort -= 1
                    db.session.commit()
                    break
        elif direction == 'down' and temp_step.sort < len(temp_step.recipe.steps):
            for temp_step_after in temp_step.recipe.steps:
                if temp_step_after.sort > temp_step.sort:
                    temp_step_after.sort = temp_step.sort
                    temp_step.sort += 1
                    db.session.commit()
                    break
    return redirect(url_for('main.recipe', recipe_uid=temp_step.recipe_uid))


@bp.route('/recipe/<recipe_uid>/step/<step_uid>/item',
          methods=['GET', 'POST'],
          defaults={'item_uid': None, 'delete': 0})
@bp.route('/recipe/<recipe_uid>/step/<step_uid>/item/<item_uid>', methods=['GET', 'POST'], defaults={'delete': 0})
@bp.route('/recipe/<recipe_uid>/step/<step_uid>/item/<item_uid>/<delete>', methods=['GET'])
@login_required
def item(recipe_uid, step_uid, item_uid, delete):
    temp_recipe = db.session.query(Recipe).filter(Recipe.uid == int(recipe_uid)).first()
    temp_step = db.session.query(RecipeStep).filter(RecipeStep.uid == int(step_uid)).first()
    if not temp_recipe.is_visible_to_user(current_user) or not temp_step.recipe.is_visible_to_user(current_user):
        flash('You do not have the permission to view this recipe.')
        return redirect(url_for('main.dashboard'))
    form = RecipeStepItemForm()
    if item_uid is None:
        if form.validate_on_submit():
            # add
            temp_step.items.append(RecipeStepItem(value=form.value.data))
            db.session.commit()
            return redirect(url_for('main.step', recipe_uid=recipe_uid, step_uid=step_uid))
    else:
        temp_item = db.session.query(RecipeStepItem).filter(RecipeStepItem.uid == int(item_uid)).first()
        if temp_item is not None:
            if form.validate_on_submit():
                # edit
                temp_item.value = form.value.data
                db.session.commit()
                return redirect(url_for('main.step', recipe_uid=recipe_uid, step_uid=step_uid))
            elif int(delete) is 1:
                # delete
                db.session.delete(temp_item)
                return redirect(url_for('main.step', recipe_uid=recipe_uid, step_uid=step_uid))
            else:
                form.value.data = temp_item.value
    return render_template('main/recipe_step_item.html', form=form, step=temp_step)

