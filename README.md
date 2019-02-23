# Overview

FreshRSS is an RSS aggregator and reader. It allows you to read and follow several
news websites at a glance without the need to browse from one website to another.

# Usage

Step by step instructions on using the charm:

    $ juju deploy fresh-rss
    $ juju deploy postgresql
    $ juju relate fresh-rss postgresql:db
    $ juju expose fresh-rss

You can then browse to `http://<ip-address-of-freshrss>` to configure FreshRSS.

#### Copyright
Tyler Scheuble (c) <tyler@scheuble.us>

#### License
AGPLv3 - See `LICENSE` file in the same directory as this readme.

#### Issues/Bugs/Feature Requests
Report bugs/feature requests on the [github issues page for this charm](https://github.com/tylerscheuble/juju-charm-fresh-rss/issues)
