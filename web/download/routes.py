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


@bp.route('/download/<instance_uids>/<recipe_uids>')
@login_required
def download(instance_uids, recipe_uids):
    instance_uids = [int(uid) for uid in str(instance_uids).split('-')]
    recipe_uids = [int(uid) for uid in str(recipe_uids).split('-')]
    if len(instance_uids) > 0 and len(recipe_uids) > 0:
        Thread(
            target=init_threaded_download,
            args=(current_app._get_current_object(), current_user._get_current_object(), instance_uids, recipe_uids)
        ).start()
        flash('Download added to queue. As soon as it is ready, a notification will be sent to ' + current_user.email)
        return redirect(url_for('main.dashboard'))


def init_threaded_download(web, user, instance_uids, recipe_uids):
    with web.app_context():
        data = StringIO()
        csv_data = csv.DictWriter(data, fieldnames=['run', 'instance',
                                                    'recipe', 'recipe_name', 'recipe_status',
                                                    'step', 'step_name',
                                                    'data_creation', 'data_value'])
        csv_data.writeheader()
        for instance_uid in instance_uids:
            for recipe_uid in recipe_uids:
                for run in db.session.query(Run).filter(Run.instance_uid == instance_uid, Run.recipe_uid == recipe_uid):
                    if run.recipe.is_visible_to_user(user) and run.instance.is_visible_to_user(user):
                        for run_data in run.data:
                            csv_data.writerow({
                                'run': str(run.created),
                                'instance': run.instance.name,
                                'recipe': str(run.recipe_uid),
                                'recipe_name': run.recipe.name,
                                'recipe_status': str(run.status.name),
                                'step': str(run_data.step.sort),
                                'step_name': str(run_data.step.type.name),
                                'data_creation': str(run_data.created),
                                'data_value': run_data.value
                            })
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
