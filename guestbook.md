---
title: "Guestbook 留言板"
permalink: /guestbook/
layout: single
author_profile: true
comments: true
---

<p style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">
  💬 已有 <span id="giscus-comment-count">0</span> 条留言
</p>

<p style="font-size: 14px; color: #888; margin-top: 4px;">
  💡 如果留言区没有出现，多刷新几次页面就好了
</p>

<script src="https://giscus.app/client.js"
        data-repo="juststories/juststories.github.io"
        data-repo-id="R_kgDOTpbEhw"
        data-category="General"
        data-category-id="DIC_kwDOTpbEh84DCnXx"
        data-mapping="pathname"
        data-strict="0"
        data-reactions-enabled="1"
        data-emit-metadata="1"
        data-input-position="bottom"
        data-theme="preferred_color_scheme"
        data-lang="zh-CN"
        data-loading="eager"
        crossorigin="anonymous"
        async>
</script>

<script>
  // 等待 Giscus 加载完成并接收评论数
  function waitForGiscus() {
    const interval = setInterval(() => {
      const iframe = document.querySelector('iframe[src*="giscus"]');
      if (iframe) {
        clearInterval(interval);
        // 监听 Giscus 发送的消息
        window.addEventListener('message', function handler(event) {
          if (event.origin !== 'https://giscus.app') return;
          if (event.data && event.data.type === 'metadata') {
            const count = event.data.discussion?.totalCommentCount || 0;
            const countEl = document.getElementById('giscus-comment-count');
            if (countEl) countEl.textContent = count;
            window.removeEventListener('message', handler);
          }
        });
      }
    }, 500);
  }

  // 页面加载后开始等待
  document.addEventListener('DOMContentLoaded', waitForGiscus);
</script>
