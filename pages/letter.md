---
title: "信"
layout: page
permalink: /letter/
---

<ul>
{% for post in site.posts %}
  {% if post.categories contains "letter" %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>{{ post.date | date: "%Y-%m-%d" }}</span>
    </li>
  {% endif %}
{% endfor %}
</ul>
