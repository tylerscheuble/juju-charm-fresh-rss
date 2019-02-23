from charmhelpers.core.hookenv import log

from subprocess import check_call
from charmhelpers.core import hookenv, unitdata
from charms.reactive import (
    endpoint_from_flag,
    is_flag_set,
    when,
    when_not,
    set_flag
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


@when_not('fresh-rss.system.initalized')
@when('apt.installed.php7.2',
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
    set_flag('fresh-rss.system.initialized')


@when_not('database.connected')
def waiting_for_db():
    status.blocked('Waiting for postgres connection')
    return


@when('database.connected')
@when_not('fresh-rss.db.requested')
def request_db():
    pgsql = endpoint_from_flag('database.connected')
    pgsql.set_database('fresh-rss')
    set_flag('fresh-rss.db.requested')


@when('database.master.available',
      'fresh-rss.db.requested')
@when_not('fresh-rss.db.config.acquired')
def acquire_db_config():
    pgsql = endpoint_from_flag('database.master.available')

    if pgsql is None:
        log('Master not found', level='ERROR')

    db = pgsql.master
    kv.set('db-user', db.user)
    kv.set('db-password', db.password)
    kv.set('db-host', db.host)

    status.active('connected to PostgreSQL')
    set_flag('fresh-rss.db.config.acquired')


@when_not('fresh-rss.installed')
@when('fresh-rss.db.config.acquired',
      'fresh-rss.system.initialized')
def install_fresh_rss():
    """Install FreshRSS
    """

    source = hookenv.resource_get('fresh-rss-tarball')
    if not source:
        log('Could not find resource fresh-rss-tarball')
        status.blocked('Need fresh-rss-tarball resource')
        return

    check_call(['mkdir', '-p', str(fresh_rss_dir)])
    cmd = ['tar', '-zxf', source, '-C', str(fresh_rss_dir),
           '--strip-components', '1']
    log('Extracting FreshRSS: {}'.format(' '.join(cmd)))
    check_call(cmd)

    apply_permissions()

    install_opts = []
    install_opts.extend(['--default_user', config['default-admin-username']])
    install_opts.extend(['--base_url', config['fqdn']])
    install_opts.extend(['--environment', config['environment']])

    # db specific
    install_opts.extend(['--db-type', 'pgsql'])
    install_opts.extend(['--db-base', 'fresh-rss'])
    install_opts.extend(['--db-user', kv.get('db-user')])
    install_opts.extend(['--db-password', kv.get('db-password')])
    install_opts.extend(['--db-host', kv.get('db-host')])
    install_opts.extend(['--db-prefix', config['db-prefix']])

    # ensure the needed directories in ./data/
    run_script('prepare')
    run_script('do-install', install_opts)

    if not is_flag_set('leadership.set.default_admin_init'):
        run_script('create-user', [
             '--user', config['default-admin-username'],
             '--password', config['default-admin-password']])
        charms.leadership.leader_set(default_admin_init="true")

    apply_permissions()

    status.active('FreshRSS installed')
    set_flag('fresh-rss.installed')


@when('fresh-rss.installed')
@when_not('fresh-rss.nginx.configured')
def configure_nginx():
    """Configure NGINX server for fresh_rss
    """

    ctxt = {'fqdn': config['fqdn'],
            'port': config['port']}

    configure_site('fresh-rss', 'fresh-rss.conf', **ctxt)
    hookenv.open_port(ctxt['port'])

    status.active('nginx configured')
    set_flag('fresh-rss.nginx.configured')


@when('fresh-rss.installed',
      'fresh-rss.nginx.configured')
@when_not('fresh-rss.ready')
def acquire_goal_state():
    status.active('Ready')
    set_flag('fresh-rss.ready')


@when('fresh-rss.ready',
      'website.available')
def configure_website():
    """Send port data to website endpoint.
    """
    endpoint = endpoint_from_flag('website.available')
    endpoint.configure(port=config['port'])
