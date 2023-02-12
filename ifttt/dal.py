# -*- coding: utf-8 -*-
"""
  Wikipedia channel for IFTTT
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Copyright 2015 Stephen LaPorte <stephen.laporte@gmail.com>

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

import pymysql
import pymysql.cursors
import toolforge
from flask import current_app as app


DEFAULT_HOURS = 1
DEFAULT_LANG = "en"
DEFAULT_LIMIT = 50


def ht_db_connect():
    connection = toolforge.toolsdb(app.config["HT_DB_NAME"])
    return connection


def run_query(query, query_params, lang):
    db_title = lang + "wiki_p"
    connection = toolforge.connect(db_title)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute(query, query_params)
    ret = cursor.fetchall()
    return ret


def get_hashtags(tag, lang=DEFAULT_LANG, limit=DEFAULT_LIMIT):
    if tag and tag[0] == "#":
        tag = tag[1:]
    connection = ht_db_connect()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    query = """
    SELECT *
    FROM recentchanges AS rc
    JOIN hashtag_recentchanges AS htrc
      ON htrc.htrc_id = rc.htrc_id
    JOIN hashtags AS ht
      ON ht.ht_id = htrc.ht_id
    WHERE ht.ht_text = ?
    AND rc.htrc_lang = ?
    ORDER BY rc.rc_id DESC
    LIMIT ?"""
    params = (tag, lang, limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def get_all_hashtags(lang=DEFAULT_LANG, limit=DEFAULT_LIMIT):
    connection = ht_db_connect()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    query = """
    SELECT *
    FROM recentchanges AS rc
    WHERE rc.rc_type = 0
    ORDER BY rc.rc_id DESC
    LIMIT ?"""
    params = (limit,)
    cursor.execute(query, params)
    return cursor.fetchall()


def get_category_members(
    category_name, lang=DEFAULT_LANG, hours=DEFAULT_HOURS, limit=DEFAULT_LIMIT
):
    query = """SELECT rc.rc_title,
       rc.rc_cur_id,
       rc.rc_namespace,
       cl.cl_timestamp
       FROM recentchanges as rc
       INNER JOIN recentchanges AS rc_talk
             ON rc.rc_title = rc_talk.rc_title
             AND rc_talk.rc_type = 0
             AND rc.rc_namespace = (rc_talk.rc_namespace - (rc_talk.rc_namespace %% 2))
       INNER JOIN categorylinks AS cl
             ON rc_talk.rc_cur_id = cl.cl_from
       WHERE cl.cl_to = %s
       AND rc.rc_type = 0
       AND cl.cl_timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
       GROUP BY rc.rc_cur_id
       ORDER BY rc.rc_id DESC
       LIMIT %s"""
    query_params = (category_name.replace(" ", "_"), hours, limit)
    ret = run_query(query, query_params, lang)
    return ret


def get_article_list_revisions(
    articles, lang=DEFAULT_LANG, hours=DEFAULT_HOURS, limit=DEFAULT_LIMIT
):
    query = """SELECT DISTINCT rc.rc_id,
                      rc.rc_cur_id,
                      rc.rc_title,
                      rc.rc_timestamp,
                      rc.rc_this_oldid,
                      rc.rc_last_oldid,
                      a.actor_name,
                      rc.rc_old_len,
                      rc.rc_new_len,
                      rc.rc_comment
               FROM recentchanges rc
               LEFT JOIN actor a ON rc.rc_actor = a.actor_id
               WHERE rc.rc_title IN ({})
               AND rc.rc_type = 0
               AND rc.rc_timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
               ORDER BY rc.rc_id DESC
               LIMIT %s
            """.format(
        ", ".join(["%s" for i in range(len(articles))])
    )
    query_params = tuple([article.replace(" ", "_") for article in articles]) + (
        hours,
        limit,
    )
    ret = run_query(query, query_params, lang)
    return ret


def get_category_member_revisions(
    category_name, lang=DEFAULT_LANG, hours=DEFAULT_HOURS, limit=DEFAULT_LIMIT
):
    query = """SELECT rc.rc_id,
                      rc.rc_cur_id,
                      rc.rc_title,
                      rc.rc_timestamp,
                      rc.rc_this_oldid,
                      rc.rc_last_oldid,
                      a.actor_name,
                      rc.rc_old_len,
                      rc.rc_new_len,
                      rc.rc_comment
               FROM recentchanges AS rc
               LEFT JOIN actor a ON rc.rc_actor = a.actor_id
               INNER JOIN recentchanges AS rc_talk
                   ON rc.rc_title = rc_talk.rc_title
                   AND rc_talk.rc_type = 0
                   AND rc.rc_namespace = (rc_talk.rc_namespace - (rc_talk.rc_namespace %% 2))
               INNER JOIN categorylinks AS cl
                   ON rc_talk.rc_cur_id = cl.cl_from
               WHERE cl.cl_to = %s
               AND rc.rc_type = 0
               AND rc.rc_timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
               AND rc.rc_type = 0
               GROUP BY rc.rc_this_oldid
               ORDER BY rc.rc_id DESC
               LIMIT %s"""
    query_params = (category_name.replace(" ", "_"), hours, limit)
    ret = run_query(query, query_params, lang)
    return ret
