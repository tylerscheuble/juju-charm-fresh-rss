from pathlib import Path

from subprocess import check_call, PIPE
from charmhelpers.core.hookenv import log


fresh_rss_dir = Path('/var/snap/fresh-rss/current')


def run(args):
    log('Executing: {}'.format(' '.join(args)))
    check_call(['sudo', '-u', 'www-data', *args], stdout=PIPE, stderr=PIPE)


def run_root(args):
    log('Executing: {} as root'.format(' '.join(args)))
    check_call(args, stdout=PIPE, stderr=PIPE)


def apply_permissions():
    log('Applying permissions')
    run_root(['chown', '-R', ':www-data', str(fresh_rss_dir)])
    run_root(['chown', '-RL', ':www-data', str(fresh_rss_dir / 'data')])
    run_root(['chmod', '-R', 'g+r', str(fresh_rss_dir)])
    run_root(['chmod', '-R', 'g+rw', str(fresh_rss_dir / 'data')])


def run_script(script, opts=[]):
    run([str(fresh_rss_dir / 'cli' / '{}.php'.format(script)), *opts])
