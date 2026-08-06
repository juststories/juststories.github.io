---
title: "文章列表"
layout: archive
permalink: /list/
author_profile: true
---

<ul>
{% assign posts = site.posts | sort: 'date' | reverse %}
{% for post in posts %}
  <li style="margin-bottom: 15px;">
    <span style="color: #666; font-size: 0.9em;">{{ post.date | date: "%Y-%m-%d" }}</span>
    <a href="{{ post.url | relative_url }}" style="margin-left: 10px;">{{ post.title }}</a>
  </li>
{% endfor %}
</ul>
