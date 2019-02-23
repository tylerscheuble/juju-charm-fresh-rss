# Overview
Use this charm to deploy Fresh-RSS backed by either PostgreSQL or MySQL.

# Usage
This charm can be deployed with either a Juju deployed mysql or postgresql database or
a user supplied database.

##### PostgreSQL Deploy

    $ juju deploy fresh-rss
    $ juju deploy postgresql
    $ juju relate fresh-rss postgresql:db
    $ juju expose fresh-rss

##### MySQL Deploy

    $ juju deploy fresh-rss
    $ juju deploy percona-cluster mysql
    $ juju relate fresh-rss mysql
    $ juju expose fresh-rss

##### User Supplied Database Deploy

    $ juju deploy fresh-rss --config db-uri="mysql://user:password@host:port/dbname"
    $ juju expose fresh-rss


You can then browse to `http://<ip-address-of-freshrss>` to configure FreshRSS.

### Copyright
Tyler Scheuble (c) <tyler@scheuble.us>

### License
AGPLv3 - See `LICENSE` file in the same directory as this readme.

### Issues/Bugs/Feature Requests
Report bugs/feature requests on the [github issues page for this charm](https://github.com/tylerscheuble/juju-charm-fresh-rss/issues)
