---
title: "随笔"
layout: page
permalink: /essay/
---

<ul>
{% for post in site.posts %}
  {% if post.categories contains "essay" %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>{{ post.date | date: "%Y-%m-%d" }}</span>
    </li>
  {% endif %}
{% endfor %}
</ul>
