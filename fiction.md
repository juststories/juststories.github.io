---
title: "小说"
layout: page
permalink: /fiction/
---

<ul>
{% for post in site.posts %}
  {% if post.categories contains "小说" %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>{{ post.date | date: "%Y-%m-%d" }}</span>
    </li>
  {% endif %}
{% endfor %}
</ul>
