up-resource: fetch-resource | fresh-rss.zip
	juju attach-resource freshrss fresh-rss-stable=fresh-rss.zip

fetch-resource: | fresh-rss.zip
	git clone https://github.com/FreshRSS/FreshRSS.git --depth 1 && \
	zip -r fresh-rss.zip FreshRSS
