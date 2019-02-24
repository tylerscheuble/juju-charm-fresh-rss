from pathlib import Path

from subprocess import check_call, PIPE
from charmhelpers.core.hookenv import log


fresh_rss_dir = Path('/usr/share/FreshRSS')


def run(args):
    log('Executing: {}'.format(' '.join(args)))
    check_call(['sudo', '-u', 'www-data', *args], stdout=PIPE, stderr=PIPE)


def run_root(args):
    log('Executing: {} as root'.format(' '.join(args)))
    check_call(args, stdout=PIPE, stderr=PIPE)


def apply_permissions():
    log('Applying permissions')
    run_root(['chown', '-R', 'www-data', str(fresh_rss_dir)])
    run(['chmod', '-R', 'g+r', str(fresh_rss_dir)])
    run(['chmod', '-R', 'g+w', str(fresh_rss_dir)])
    run(['chmod', '-R', 'g+w', str(fresh_rss_dir.joinpath('data'))])


def run_script(script, opts=[]):
    cmd = [str(fresh_rss_dir.joinpath('cli', '{}.php'.format(script))), *opts]
    run(cmd)
