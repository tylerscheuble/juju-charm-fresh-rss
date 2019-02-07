from charms.reactive import when, when_not, set_flag
from charms.layer.nginx import configure_site
from charms.layer import freshrss
from charmhelpers.core import hookenv


config = hookenv.config()


@when_not('freshrss.files.fetched')
def fetch_files():
    archive = freshrss.download_archive()
    freshrss.extract_archive(archive)
    set_flag('freshrss.files.fetched')


# Not sure if waiting for the php packages is necessary
@when('apt.installed.php7.2')
# @when('apt.installed.php', 'apt.installed.php-curl')
# @when('apt.installed.php-intl', 'apt.installed.php-mbstring')
# @when('apt.installed.php-sqlite3', 'apt.installed.php-xml')
# @when('apt.installed.php-zip', 'apt.installed.php-gmp')
# @when('nginx.available', 'freshrss.files.fetched')
@when_not('freshrss.nginx.configured')
def configure_nginx():
    configure_site('freshrss', 'fresh-rss.conf')
    set_flag('freshrss.nginx.configured')

    hookenv.status_set('active', 'ready')


@when('nginx.available', 'website.available')
def configure_website(website):
    website.configure(port=config['port'])
