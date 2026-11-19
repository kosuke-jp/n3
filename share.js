// 満点サプリ：共有用リンクのコピーボタン
// URLの末尾に更新日（?v=YYYYMMDD）を付けてコピーする。日付が変わるとカカオトークがカードを読み直す。
(function () {
  var m = document.querySelector('meta[name="n3-updated"]');
  var v = m ? m.content.replace(/-/g, '') : '';
  var url = location.origin + location.pathname.replace(/index\.html$/, '') + (v ? '?v=' + v : '');
  var css = document.createElement('style');
  css.textContent =
    '.n3share{margin-left:8px;border:1px solid #d9d4ca;background:#fff;color:#333;border-radius:9px;' +
    'padding:5px 10px;font:700 13px/1.2 inherit;cursor:pointer;white-space:nowrap;flex:none}' +
    '.n3share.fixed{position:fixed;top:14px;right:14px;z-index:20;box-shadow:0 2px 8px rgba(0,0,0,.08)}' +
    '.n3toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#222;color:#fff;' +
    'border-radius:10px;padding:10px 16px;font:700 14px/1.5 inherit;z-index:99;max-width:92vw;word-break:break-all;text-align:center}';
  document.head.appendChild(css);
  var b = document.createElement('button');
  b.type = 'button';
  b.className = 'n3share';
  b.textContent = '🔗 共有';
  b.title = '共有用リンクをコピー（링크 복사）';
  var bar = document.getElementById('bar');
  if (bar) bar.appendChild(b); else { b.classList.add('fixed'); document.body.appendChild(b); }
  function toast(html) {
    var t = document.createElement('div');
    t.className = 'n3toast';
    t.innerHTML = html;
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 3500);
  }
  b.addEventListener('click', function () {
    var ok = function () { toast('共有用リンクをコピーしました<br><small>링크를 복사했어요</small>'); };
    var ng = function () { toast(url); };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(ok, ng);
      else ng();
    } catch (e) { ng(); }
  });
})();
