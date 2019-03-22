from threading import Thread
from web import mail
from flask_mail import Message
from flask import render_template, flash, redirect, url_for, current_app
from web.main import bp
from flask_login import current_user, login_required
from web import db, config
from scrapebot.database import *
import csv
from io import StringIO
import hashlib
import time
from web.download.forms import DownloadForm


@bp.route('/download', methods=['POST'])
@login_required
def download():
    form = DownloadForm()
    if form.validate_on_submit():
        if form.instance_list.data != '' and form.recipe_list.data != '':
            instance_uids = [int(uid) for uid in form.instance_list.data.split('-')]
            recipe_uids = [int(uid) for uid in form.recipe_list.data.split('-')]
            if len(instance_uids) > 0 and len(recipe_uids) > 0:
                Thread(
                    target=init_threaded_download,
                    args=(current_app._get_current_object(), current_user._get_current_object(),
                          instance_uids, recipe_uids)
                ).start()
                flash('Download added to queue. As soon as it is ready, ' + current_user.email + ' will be notified.')
                return redirect(url_for('main.dashboard'))


def init_threaded_download(web, user, instance_uids, recipe_uids):
    with web.app_context():
        data = StringIO()
        # extrasaction='ignore' tells DictWriter not to check on the keys in every single iteration
        csv_data = csv.DictWriter(data, fieldnames=['run', 'instance',
                                                    'recipe', 'recipe_name', 'recipe_status',
                                                    'step', 'step_name',
                                                    'data_creation', 'data_value'], extrasaction='ignore')
        csv_data.writeheader()
        for instance_uid in instance_uids:
            instance = db.session.query(Instance).filter(Instance.uid == instance_uid).one_or_none()
            if instance and instance.is_visible_to_user(user):
                for recipe_uid in recipe_uids:
                    recipe = db.session.query(Recipe).filter(Recipe.uid == recipe_uid).one_or_none()
                    if recipe and recipe.is_visible_to_user(user):
                        rows = []
                        for run_data in \
                                db.session.query(
                                    Data.created, Data.value,
                                    RecipeStep.sort, RecipeStep.type,
                                    Run.created, Run.status
                                )\
                                .filter(
                                    Data.step_uid == RecipeStep.uid, Data.run_uid == Run.uid,
                                    Run.instance_uid == instance_uid, Run.recipe_uid == recipe_uid
                                ):
                            rows.append({
                                'run': str(run_data[4]),
                                'instance': instance.name,
                                'recipe': str(recipe_uid),
                                'recipe_name': recipe.name,
                                'recipe_status': run_data[5].name,
                                'step': run_data[2],
                                'step_name': run_data[3].name,
                                'data_creation': str(run_data[0]),
                                'data_value': run_data[1]
                            })
                        csv_data.writerows(rows)
        msg = Message('Your ScrapeBot data request', sender='ScrapeBot <scrapebot@haim.it>', recipients=[user.email])
        if data.tell() < 2000000:
            msg.body = render_template('email/download.txt', user=user, link='')
            msg.attach('data.csv', 'text/csv', data.getvalue())
        else:
            link = 'order_' + hashlib.md5(bytes(user.email + str(time.time()), encoding='utf-8')).hexdigest() + '.csv'
            if config.get('Database', 'AWSaccess') is not None and \
               config.get('Database', 'AWSsecret') is not None and \
               config.get('Database', 'AWSbucket') is not None:
                import boto3
                client = boto3.client(
                    's3',
                    aws_access_key_id=config.get('Database', 'AWSaccess'),
                    aws_secret_access_key=config.get('Database', 'AWSsecret')
                )
                s3_file = client.put_object(
                    Bucket=config.get('Database', 'AWSbucket'),
                    Key=link,
                    Body=bytes(data.getvalue(), encoding='utf-8')
                )
                link = 's3://' + config.get('Database', 'AWSbucket') + '/' + link
            else:
                screenshot_dir = config.get('Instance', 'ScreenshotDirectory')
                if screenshot_dir is not None:
                    if not screenshot_dir.endswith('/'):
                        screenshot_dir = screenshot_dir + '/'
                else:
                    screenshot_dir = './'
                link = screenshot_dir + link
                local_file = open(link, 'w')
                local_file.write(data.getvalue())
                local_file.close()
            msg.body = render_template('email/download.txt', user=user, link=link)
        data.close()
        mail.send(msg)
