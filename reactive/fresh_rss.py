from pathlib import Path
from subprocess import check_call

from charmhelpers.core import hookenv
from charms.reactive import endpoint_from_flag, when, when_not, set_flag
from charms.layer.nginx import configure_site


fresh_rss_dir = Path('/usr/share/FreshRSS')


@when_not('fresh_rss.installed')
def install_freshrss():
    """Install FreshRSS
    """

    source = hookenv.resource_get('fresh-rss-tarball')
    if not source:
        hookenv.log('Could not find resource fresh-rss-tarball')
        hookenv.status_set('blocked', "Need fresh-rss-tarball resource")
        return

    check_call(['mkdir', '-p', str(fresh_rss_dir)])
    cmd = ['tar', '-zxvf', source, '-C', str(fresh_rss_dir),
           '--strip-components', '1']
    hookenv.log('Extracting FreshRSS: {}'.format(' '.join(cmd)))
    check_call(cmd)

    # set permissions
    cmd = ['chmod', '-R', 'g+w', str(fresh_rss_dir)]
    hookenv.log('Setting permissions: {}'.format(''.join(cmd)))
    check_call(cmd)

    set_flag('fresh_rss.installed')


@when('fresh_rss.installed',
      'apt.installed.php7.2',
      'apt.installed.php7.2-fpm',
      'apt.installed.php7.2-curl',
      'apt.installed.php7.2-gmp',
      'apt.installed.php7.2-intl',
      'apt.installed.php7.2-mbstring',
      'apt.installed.php7.2-sqlite3',
      'apt.installed.php7.2-xml',
      'apt.installed.php7.2-zip')
@when_not('fresh_rss.nginx.configured')
def configure_nginx():
    """Configure NGINX server for fresh_rss
    """

    configure_site('fresh_rss', 'fresh-rss.conf')
    hookenv.status_set('active', 'ready')
    set_flag('fresh_rss.nginx.configured')


@when('fresh_rss.nginx.configured', 'website.available')
def configure_website():
    """Send port data to website endpoint.
    """

    config = hookenv.config()
    endpoint = endpoint_from_flag('website.available')
    endpoint.configure(port=config['port'])
