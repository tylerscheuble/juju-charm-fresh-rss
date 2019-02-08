from charms.reactive import when, when_not, set_flag
from charms.layer.nginx import configure_site
from charms.layer import fresh_rss
from charmhelpers.core import hookenv


config = hookenv.config()


@when_not('fresh_rss.files.fetched')
def fetch_files():
    archive = fresh_rss.download_archive()
    fresh_rss.extract_archive(archive)
    set_flag('fresh_rss.files.fetched')


@when('apt.installed.php7.2')
@when_not('fresh_rss.nginx.configured')
def configure_nginx():
    configure_site('fresh_rss', 'fresh-rss.conf')
    set_flag('fresh_rss.nginx.configured')

    hookenv.status_set('active', 'ready')


@when('nginx.available', 'website.available')
def configure_website(website):
    website.configure(port=config['port'])
