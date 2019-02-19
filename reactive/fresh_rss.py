from pathlib import Path
from subprocess import check_call, PIPE, STDOUT

from charmhelpers.core import hookenv, unitdata
from charmhelpers.core.hookenv import status_set, log

from charms.reactive import (
        endpoint_from_flag,
        when,
        when_not,
        set_flag,
        is_flag_set
)

from charms.layer.nginx import configure_site

fresh_rss_dir = Path('/usr/share/FreshRSS')
config = hookenv.config()
kv = unitdata.kv()


@when_not('freshrss.installed')
@when('database.master.available',
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
    if not is_flag_set('database.master.available'):
        status_set('error', 'Database can not be found')
        raise Exception('Database can not be found')

    opts = []

    opts.extend(['--default_user', config['default-user']])
    opts.extend(['--base_url', config['base-url']])
    opts.extend(['--environment', config['environment']])

    # db specific
    opts.extend(['--db-type', 'pgsql'])
    opts.extend(['--db-base', 'fresh-rss'])
    opts.extend(['--db-user', kv.get('db-user')])
    opts.extend(['--db-password', kv.get('db-password')])
    opts.extend(['--db-host', kv.get('db-host')])
    opts.extend(['--db-prefix', config['db-prefix']])

    log('Opts: {}'.format(' '.join(opts)))

    return opts


def apply_permissions():
    log('Applying permissions')
    check_call(['chown', '-R', ':www-data', str(fresh_rss_dir)])
    check_call(['chmod', '-R', 'g+r', str(fresh_rss_dir)])
    check_call(['chmod', '-R', 'g+w', str(fresh_rss_dir)])
    check_call(['chmod', '-R', 'g+w', str(fresh_rss_dir.joinpath('data'))])


def run_script(script, opts=[]):
    cmd = [str(fresh_rss_dir.joinpath('cli', '{}.php'.format(script))), *opts]
    log('Running script: {}'.format(cmd))
    check_call(cmd, stdout=PIPE, stderr=STDOUT)


@when_not('database.connected')
def waiting_for_db():
    status_set('blocked', 'Waiting for postgres connection')


@when('database.connected')
def choose_db():
    pgsql = endpoint_from_flag('database.connected')
    pgsql.set_database('fresh-rss')


@when('database.master.available')
def get_db_config():
    pgsql = endpoint_from_flag('database.master.available')
    db = pgsql.master
    hookenv.status_set('active', 'connected to PostgreSQL at {}'
                                 .format(db.host))

    kv.set('db-user', db.user)
    kv.set('db-password', db.password)
    kv.set('db-host', db.host)
