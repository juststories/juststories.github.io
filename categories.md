---
title: "分类"
layout: single
permalink: /categories/
author_profile: true
---

{% for category in site.categories %}
  <h2>{{ category | first }}</h2>
  <ul>
    {% for post in category.last %}
      <li>
        <a href="{{ post.url }}">{{ post.title }}</a>
        <span>{{ post.date | date: "%Y-%m-%d" }}</span>
      </li>
    {% endfor %}
  </ul>
{% endfor %}
