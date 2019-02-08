from subprocess import check_call
from charmhelpers.core import hookenv


class ResourceFailure(Exception):
    pass


def download_archive():
    source = hookenv.resource_get('fresh-rss-tarball')
    if not source:
        hookenv.log('Could not find resource fresh-rss-tarball')
        raise ResourceFailure()
    hookenv.log('Downloaded FreshRSS archive: to {}'.format(source))
    return source


def extract_archive(source):
    check_call(('mkdir', '-p', '/usr/share/FreshRSS'))
    cmd = ('tar', '-zxvf', source, '-C', '/usr/share/FreshRSS',
           '--strip-components', '1')
    hookenv.log('Extracting FreshRSS: {}'.format(' '.join(cmd)))
    check_call(cmd)

    # set permissions
    cmd = ('chmod', '-R', 'g+w', '/usr/share/FreshRSS/')
    hookenv.log('Setting permissions: {}'.format(''.join(cmd)))
    check_call(cmd)
