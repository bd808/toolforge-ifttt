# -*- coding: utf-8 -*-
"""
  Wikipedia channel for IFTTT
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Copyright 2015 Ori Livneh <ori@wikimedia.org>

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

"""
import operator
import urllib.request
import urllib.error
import urllib.parse

import feedparser
import flask
import flask.views
import werkzeug.contrib.cache

from .utils import url_to_uuid5, utc_to_epoch, utc_to_iso8601


__all__ = ("FeaturedFeedTriggerView",)

feed_cache = werkzeug.contrib.cache.SimpleCache()


class FeaturedFeedTriggerView(flask.views.MethodView):
    """Generic view for IFTT Triggers based on FeaturedFeeds."""

    URL_FORMAT = "https://{0.wiki}/w/api.php?action=featuredfeed&feed={0.feed}"

    def get_feed(self):
        """Fetch and parse the feature feed for this class."""
        url = self.URL_FORMAT.format(self)
        feed = feed_cache.get(url)
        if not feed:
            feed = feedparser.parse(urllib.request.urlopen(url))  # nosec: B310
            feed_cache.set(url, feed, timeout=5 * 60)
        return feed

    def parse_entry(self, entry):
        """Parse a single feed entry into an IFTTT trigger item."""
        id = url_to_uuid5(entry.id)
        created_at = utc_to_iso8601(entry.published_parsed)
        ts = utc_to_epoch(entry.published_parsed)
        return {"created_at": created_at, "meta": {"id": id, "timestamp": ts}}

    def get_items(self):
        """Get the set of items for this trigger."""
        feed = self.get_feed()
        feed.entries.sort(key=operator.attrgetter("published_parsed"), reverse=True)
        return list(map(self.parse_entry, feed.entries))

    def post(self):
        """Handle POST requests."""
        params = flask.request.get_json(force=True, silent=True) or {}
        limit = params.get("limit", 50)
        items = self.get_items()
        items = items[:limit]
        return flask.jsonify(data=items)
