#!/usr/bin/env python3
"""満点サプリ：カード画像（OG画像）と更新日を、GitHubの記録から自動で作り直す。

- 各ページの「追加日」「更新日」を git の記録から読む（韓国時間）。
  コミットメッセージに [auto] か [no-update] が入っているものは数えない
  （見た目だけの変更や、この自動処理そのものの変更を「更新」にしないため）。
- og/base/<ページ名>.png に「NEW m/d」「UPDATE m/d」の帯を重ねて og/<ページ名>.png を作る。
  帯は追加・更新から7日間だけ付き、そのあとは自動で外れる（毎日の定期実行で）。
- og:image のURLに ?v=日付 を付けて、カカオトークなどに新しい画像を読み直させる。
- <meta name="n3-updated"> に更新日を書く（共有ボタンがURL末尾の ?v= に使う）。
- トップページの各リンクの data-added / data-updated を書き換える。
"""
import datetime as dt
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://kosuke-jp.github.io/n3/'
KST = dt.timezone(dt.timedelta(hours=9))
DAYS = 7
SKIP = ('[auto]', '[no-update]')
FONT_PATHS = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
              '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf']


def git_dates(path):
    out = subprocess.run(['git', 'log', '--format=%ct%x09%s', '--', path],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    ds = []
    for line in out.splitlines():
        ts, _, msg = line.partition('\t')
        if any(k in msg for k in SKIP):
            continue
        ds.append(dt.datetime.fromtimestamp(int(ts), KST).date())
    return (min(ds), max(ds)) if ds else (None, None)


def badge_for(added, updated, today):
    if updated is None:
        return None
    if (today - added).days < DAYS and added == updated:
        return 'NEW'
    if (today - updated).days < DAYS:
        return 'UPDATE'
    return None


def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise SystemExit('DejaVu Sans Bold が見つかりません')


def render(base, out, badge, day):
    im = Image.open(base).convert('RGB')
    if badge:
        d = ImageDraw.Draw(im)
        label = f'{badge}  {day.month}/{day.day}'
        f = font(40)
        x0, y0 = 72, 70
        w = d.textlength(label, font=f)
        d.rounded_rectangle([x0 + 6, y0 + 6, x0 + w + 62, y0 + 78], radius=18, fill=(34, 34, 34))
        d.rounded_rectangle([x0, y0, x0 + w + 56, y0 + 72], radius=18, fill=(232, 116, 59))
        d.text((x0 + 28, y0 + 14), label, font=f, fill=(255, 255, 255))
    data = im.copy()
    if os.path.exists(out):
        old = Image.open(out).convert('RGB')
        if old.size == data.size and old.tobytes() == data.tobytes():
            return False
    data.save(out, optimize=True)
    return True


def set_meta(html, prop_or_name, key, value):
    pat = re.compile(r'<meta %s="%s" content="[^"]*">' % (prop_or_name, re.escape(key)))
    tag = '<meta %s="%s" content="%s">' % (prop_or_name, key, value)
    if pat.search(html):
        return pat.sub(tag, html, count=1)
    anchor = '<meta name="viewport"'
    i = html.index(anchor)
    j = html.index('>', i) + 1
    return html[:j] + '\n' + tag + html[j:]


def main():
    today = dt.datetime.now(KST).date()
    pages = sorted(f for f in os.listdir(ROOT) if f.endswith('.html') and f != 'index.html')
    info = {}
    changed = []
    for f in pages:
        stem = f[:-5]
        added, updated = git_dates(f)
        if added is None:
            continue
        badge = badge_for(added, updated, today)
        info[f] = (added, updated, badge)
        base = os.path.join(ROOT, 'og', 'base', stem + '.png')
        if not os.path.exists(base):
            base = os.path.join(ROOT, 'og', 'base', 'index.png')
        if render(base, os.path.join(ROOT, 'og', stem + '.png'), badge, updated):
            changed.append('og/' + stem + '.png')
        v = updated.strftime('%Y%m%d') + {'NEW': 'n', 'UPDATE': 'u', None: ''}[badge]
        p = os.path.join(ROOT, f)
        html = open(p, encoding='utf-8').read()
        new = set_meta(html, 'property', 'og:image', f'{SITE}og/{stem}.png?v={v}')
        new = set_meta(new, 'name', 'n3-added', added.isoformat())
        new = set_meta(new, 'name', 'n3-updated', updated.isoformat())
        if new != html:
            open(p, 'w', encoding='utf-8').write(new)
            changed.append(f)

    # トップページ
    p = os.path.join(ROOT, 'index.html')
    html = open(p, encoding='utf-8').read()
    new = html
    for f, (added, updated, _) in info.items():
        pat = re.compile(r'<a href="%s"[^>]*>' % re.escape(f))
        new = pat.sub(f'<a href="{f}" data-added="{added.isoformat()}" data-updated="{updated.isoformat()}">', new, count=1)
    latest = max(info.values(), key=lambda x: x[1])
    badges = [b for (_, _, b) in info.values() if b]
    top_badge = 'UPDATE' if badges else None
    if render(os.path.join(ROOT, 'og', 'base', 'index.png'), os.path.join(ROOT, 'og', 'index.png'), top_badge, latest[1]):
        changed.append('og/index.png')
    v = latest[1].strftime('%Y%m%d') + ('u' if top_badge else '')
    new = set_meta(new, 'property', 'og:image', f'{SITE}og/index.png?v={v}')
    new = set_meta(new, 'name', 'n3-updated', latest[1].isoformat())
    if new != html:
        open(p, 'w', encoding='utf-8').write(new)
        changed.append('index.html')

    for f, (a, u, b) in info.items():
        print(f'{f:22s} 追加 {a}  更新 {u}  {b or ""}')
    print('変更:', ', '.join(changed) or 'なし')


if __name__ == '__main__':
    main()
