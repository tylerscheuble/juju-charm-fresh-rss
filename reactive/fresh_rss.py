from urllib.parse import urlparse

from charmhelpers.core.hookenv import log

from subprocess import check_call
from charmhelpers.core import hookenv, unitdata
from charms.reactive import (
    endpoint_from_flag,
    is_flag_set,
    when,
    when_not,
    when_any,
    set_flag,
    clear_flag
)

import charms.leadership

from charms.layer.nginx import configure_site
from charms.layer import status
from charms.layer.fresh_rss import (
    fresh_rss_dir,
    apply_permissions,
    run_script
)

config = hookenv.config()
kv = unitdata.kv()


@when_not('manual.database.check.complete')
def check_user_provided_database():
    log('check_user_provided_database called', level='ERROR')
    if config['db-uri']:
        db_uri = urlparse(config['db-uri'])
        kv.set('db-scheme', db_uri.scheme)
        kv.set('db-user', db_uri.username)
        kv.set('db-password', db_uri.password)
        kv.set('db-host', db_uri.hostname)
        kv.set('db-base', db_uri.path)

        log("Manual database configured")
        set_flag('fresh-rss.db.config.acquired')
    else:
        log("Manual database not configured")
    set_flag('manual.database.check.complete')


@when_not('fresh-rss.system.initialized')
@when('snap.installed.fresh-rss',
      'apt.installed.php7.2',
      'apt.installed.php7.2-fpm',
      'apt.installed.php7.2-curl',
      'apt.installed.php7.2-gmp',
      'apt.installed.php7.2-intl',
      'apt.installed.php7.2-mbstring',
      'apt.installed.php7.2-sqlite3',
      'apt.installed.php7.2-xml',
      'apt.installed.php7.2-zip',
      'apt.installed.php7.2-pgsql')
def init_fresh_rss():
    log('init_fresh_rss called', level='ERROR')
    set_flag('fresh-rss.system.initialized')


@when_not('fresh-rss.db.config.acquired')
def waiting_for_db():
    log('waiting_for_db called', level='ERROR')
    status.waiting('Waiting for database relation or configuration')


# Postgresql db relation handlers
@when_any('pgsql.connected', 'mysql.connected')
@when_not('fresh-rss.db.requested')
def request_db():
    log('request_db called', level='ERROR')
    """Request the database from postgresql or mysql
    """
    db_name = "fresh-rss"
    db_prefix = "fresh-rss"
    db_user = "juju_fresh-rss"

    if is_flag_set('pgsql.connected'):
        pgsql = endpoint_from_flag('pgsql.connected')
        pgsql.set_database(db_name)
    elif is_flag_set('mysql.connected'):
        mysql = endpoint_from_flag('mysql.connected')
        mysql.configure(db_name, db_user, prefix=db_prefix)
    set_flag('fresh-rss.db.requested')


@when('fresh-rss.db.requested')
@when_any('pgsql.master.available', 'mysql.available')
@when_not('fresh-rss.db.config.acquired')
def acquire_db_config():
    log('acquire_db_config called', level='ERROR')
    """Acquire juju provided database config
    """

    if is_flag_set('pgsql.master.available'):
        pgsql = endpoint_from_flag('pgsql.master.available')

        if pgsql is None:
            log('PostgeSQL not found', level='ERROR')
            return

        db = pgsql.master

        kv.set('db-scheme', 'pgsql')
        kv.set('db-user', db.user)
        kv.set('db-password', db.password)
        kv.set('db-host', db.host)
        kv.set('db-base', db.dbname)

    elif is_flag_set('mysql.available'):
        mysql = endpoint_from_flag('mysql.available')
        prefix = "fresh-rss"

        if mysql is None:
            log('MySQL not found', level='ERROR')
            return

        kv.set('db-scheme', 'mysql')
        kv.set('db-user', mysql.username(prefix))
        kv.set('db-password', mysql.password(prefix))
        kv.set('db-host', mysql.hostname(prefix))
        kv.set('db-base', mysql.database(prefix))

    status.active('Fresh-RSS Database Acquired')
    set_flag('fresh-rss.db.config.acquired')


@when_not('fresh-rss.installed')
@when('fresh-rss.db.config.acquired',
      'fresh-rss.system.initialized')
def install_fresh_rss():
    log('install_fresh_rss called', level='ERROR')
    """Install FreshRSS
    """

#    source = hookenv.resource_get('fresh-rss-tarball')
#    if not source:
#        log('Could not find resource fresh-rss-tarball')
#        status.blocked('Need fresh-rss-tarball resource')
#        return
#
#    check_call(['mkdir', '-p', str(fresh_rss_dir)])
#    cmd = ['tar', '-zxf', source, '-C', str(fresh_rss_dir),
#           '--strip-components', '1']
#    log('Extracting FreshRSS: {}'.format(' '.join(cmd)))
#    check_call(cmd)
#
#    apply_permissions()
#
#    install_opts = []
#    install_opts.extend(['--default_user', config['default-admin-username']])
#    install_opts.extend(['--base_url', config['fqdn']])
#    install_opts.extend(['--environment', config['environment']])
#
#    # db specific
#    install_opts.extend(['--db-type', kv.get('db-scheme')])
#    install_opts.extend(['--db-base', kv.get('db-base')])
#    install_opts.extend(['--db-user', kv.get('db-user')])
#    install_opts.extend(['--db-password', kv.get('db-password')])
#    install_opts.extend(['--db-host', kv.get('db-host')])
#    install_opts.extend(['--db-prefix', config['db-prefix']])
#
#    # ensure the needed directories in ./data/
#    run_script('prepare')
#    run_script('do-install', install_opts)
#
#    if not is_flag_set('leadership.set.default_admin_init'):
#        run_script('create-user', [
#             '--user', config['default-admin-username'],
#             '--password', config['default-admin-password']])
#        charms.leadership.leader_set(default_admin_init="true")
#
#    apply_permissions()

    status.active('FreshRSS installed')
    set_flag('fresh-rss.installed')


@when('fresh-rss.installed')
@when_not('fresh-rss.nginx.configured')
def configure_nginx():
    log('configure_nginx called', level='ERROR')
    """Configure NGINX server for fresh_rss
    """

    ctxt = {'fqdn': config['fqdn'], 'port': config['port']}

    configure_site('fresh-rss', 'fresh-rss.conf', **ctxt)
    hookenv.open_port(ctxt['port'])

    status.active('nginx configured')
    set_flag('fresh-rss.nginx.configured')


@when('fresh-rss.installed',
      'fresh-rss.nginx.configured')
@when_not('fresh-rss.ready')
def ready():
    log('acquire_goal_state called', level='ERROR')
    status.active('Ready')
    set_flag('fresh-rss.ready')


@when('fresh-rss.ready',
      'website.available')
def configure_website():
    log('configure_website called', level='ERROR')
    """Send port data to website endpoint.
    """
    endpoint = endpoint_from_flag('website.available')
    endpoint.configure(port=config['port'])


@when('config.changed.db-uri',
      'manual.database.check.complete')
@when_not('fresh-rss.ready',
          'fresh-rss.db.config.acquired')
def reset_manual_db_check():
    log('reset_manual_db_check called', level='ERROR')
    """If the user intends to use a manually specified db-uri
    but forgets to specify it at deploy time the charm will block.
    In this case the user can then set a manually configured database by
    setting the charm's 'db-uri' config option.
    This handler will unset the manual database checked flag, so the manual
    check may run again and set the db creds if the config is set while the
    charm is in the blocked state.
    """
    clear_flag('manual.database.check.complete')
