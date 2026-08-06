---
title: "日记"
layout: page
permalink: /diary/
---

<ul>
{% for post in site.posts %}
  {% if post.categories contains "日记" %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>{{ post.date | date: "%Y-%m-%d" }}</span>
    </li>
  {% endif %}
{% endfor %}
</ul>
