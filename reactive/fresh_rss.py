from pathlib import Path
from subprocess import check_call

from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import status_set, log
from charms.reactive import endpoint_from_flag, when, when_not, set_flag
from charms.layer.nginx import configure_site

fresh_rss_dir = Path('/usr/share/FreshRSS')
config = hookenv.config()


@when_not('freshrss.installed')
@when('database.available',
      'apt.installed.php7.2',
      'apt.installed.php7.2-fpm',
      'apt.installed.php7.2-curl',
      'apt.installed.php7.2-gmp',
      'apt.installed.php7.2-intl',
      'apt.installed.php7.2-mbstring',
      'apt.installed.php7.2-sqlite3',
      'apt.installed.php7.2-xml',
      'apt.installed.php7.2-zip')
def install_freshrss():
    """Install FreshRSS
    """

    source = hookenv.resource_get('fresh-rss-tarball')
    if not source:
        log('Could not find resource fresh-rss-tarball')
        status_set('blocked', 'Need fresh-rss-tarball resource')
        return

    check_call(['mkdir', '-p', str(fresh_rss_dir)])
    cmd = ['tar', '-zxf', source, '-C', str(fresh_rss_dir),
           '--strip-components', '1']
    log('Extracting FreshRSS: {}'.format(' '.join(cmd)))
    check_call(cmd)

    # ensure the needed directories in ./data/
    run_script('prepare')
    run_script('do-install', get_config_options())

    apply_permissions()

    status_set('active', 'FreshRSS installed')
    set_flag('freshrss.installed')


@when('freshrss.installed',
      'database.available')
@when_not('freshrss.defaultuser.created')
def create_default_user():
    user = config['default-user-name']
    password = config['default-user-password']

    if not password:
        status_set('blocked', 'Please set user password')
        return

    run_script('create-user', ['--user', user, '--password', password])

    status_set('active', 'Default user created')
    set_flag('freshrss.defaultuser.created')


@when('freshrss.defaultuser.created')
@when_not('freshrss.nginx.configured')
def configure_nginx():
    """Configure NGINX server for fresh_rss
    """

    configure_site('freshrss', 'fresh-rss.conf')
    status_set('active', 'ready')
    status_set('active', 'nginx configured')
    set_flag('freshrss.nginx.configured')


@when('freshrss.nginx.configured', 'website.available')
def configure_website():
    """Send port data to website endpoint.
    """
    endpoint = endpoint_from_flag('website.available')
    endpoint.configure(port=config['port'])


@when('freshrss.installed',
      'config.changed')
def update_config():
    run_script('reconfigure', get_config_options())


def get_config_options():
    opts = []

    opts.extend(['--default_user', config['default-user']])
    opts.extend(['--base_url', config['base-url']])
    opts.extend(['--environment', config['environment']])

    # db specific
    database = endpoint_from_flag('database.available')
    if not database:
        log('error', 'Database can not be found')
        status_set('error', 'Database can not be found')
        raise Exception('Database can not be found')

    log('DB: {}'.format(database))
    log('DIR: {}'.format(dir(database)))

    opts.extend(['--db-type', 'mysql'])
    opts.extend(['--db-base', 'freshrss'])
    opts.extend(['--db-user', database.db_user('freshrss')])
    opts.extend(['--db-password', database.db_password('freshrss')])
    opts.extend(['--db-host', database.db_host('freshrss')])
    opts.extend(['--db-prefix', config['db-prefix']])

    return opts


@when('database.connected')
@when_not('database.available')
def setup_database():
    log('Waiting for database to connect')
    status_set('blocked', 'waiting for database')


@when('database.available')
def setup_mysql(db):
    get_config_options()
    status_set('active', 'database available')


def apply_permissions():
    log('Applying permissions')
    check_call(['chown', '-R', ':www-data', str(fresh_rss_dir)])
    check_call(['chmod', '-R', 'g+r', str(fresh_rss_dir)])
    check_call(['chmod', '-R', 'g+w', str(fresh_rss_dir)])
    check_call(['chmod', '-R', 'g+w', str(fresh_rss_dir.joinpath('data'))])


def run_script(script, opts=[]):
    cmd = [str(fresh_rss_dir.joinpath('cli', '{}.php'.format(script))), *opts]
    log('Running script: {}'.format(cmd))


@when_not('freshrss.database.configured',
          'database.connected')
def wait_for_relation():
    status_set('blocked', 'Please add database relation')


@when('database.connected')
def configure_database(db):
    database = endpoint_from_flag('database.connected')
    log('DIR2: {}'.format(dir(database)))
    log('DIR3: {}'.format(dir(db)))
    database.configure('freshrss', config['db-user'],
                       prefix=config['db-prefix'])


@when('database.connected')
@when_not('database.available')
def wait_for_db():
    status_set('waiting', 'Waiting for database')
