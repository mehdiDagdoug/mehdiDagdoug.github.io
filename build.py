"""Build the website into _site/ from _data/*.yml, _pages/*.md and _templates/*.html.

    python3 build.py
"""
import hashlib
import re
import shutil
from datetime import date
from itertools import groupby
from pathlib import Path
from urllib.parse import quote

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
ME = "M. Dagdoug"
PEOPLE = {}  # colleague name (full or short form) -> web page, from _data/people.yml

# Pages built from data files: output name -> (template, title)
PAGES = {
    "index.html": ("home.html", None),
    "research.html": ("research.html", "Research"),
    "publications.html": ("publications.html", "Publications"),
    "talks.html": ("talks.html", "Talks"),
    "students.html": ("students.html", "Students"),
    "teaching.html": ("teaching.html", "Teaching"),
    "service.html": ("service.html", "Service"),
}


# Addresses of the previous website, forwarded to the new pages so old links keep working
REDIRECTS = {
    "about/": "index.html", "about.html": "index.html",
    "publications/": "publications.html", "talks/": "talks.html", "teaching/": "teaching.html",
    "students/": "students.html", "cv/": "service.html", "responsibilities/": "service.html",
}


def write_redirect(old, target, site_url):
    path = OUT / old / "index.html" if old.endswith("/") else OUT / old
    path.parent.mkdir(parents=True, exist_ok=True)
    rel = "../" * old.count("/") + target
    path.write_text(
        '<!doctype html><meta charset="utf-8"><title>Page moved</title>'
        f'<link rel="canonical" href="{site_url}/{target}">'
        f'<meta http-equiv="refresh" content="0; url={rel}">'
        f'<p>This page has moved: <a href="{rel}">{site_url}/{target}</a></p>\n', encoding="utf-8")


def load(name):
    return yaml.safe_load((ROOT / "_data" / name).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ filters

def fileurl(path):
    if not path or re.match(r"^[a-z]+:", path) or path.startswith("#"):
        return path
    return quote(path, safe="/()#")


def md(text):
    """Tiny Markdown subset for short text: [links](url) and *italics*."""
    html = str(escape(text))
    html = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                  lambda m: f'<a href="{fileurl(m.group(2))}">{m.group(1)}</a>', html)
    html = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", html)
    return Markup(_link_people(html))


def _link_people(html):
    """Link the first mention of each known colleague that is not already a link."""
    for name, url in PEOPLE.items():
        if " " not in name or f">{name}</a>" in html:  # full names only, skip if already linked
            continue
        parts = re.split(r"(<a\b.*?</a>)", html, flags=re.S)
        for i in range(0, len(parts), 2):
            if name in parts[i]:
                parts[i] = parts[i].replace(name, f'<a class="person" href="{url}">{name}</a>', 1)
                break
        html = "".join(parts)
    return html


def person(name):
    """A colleague's name, linked to their page when it is listed in people.yml."""
    if isinstance(name, Markup):
        return name
    url = PEOPLE.get(name)
    return Markup('<a class="person" href="{}">{}</a>').format(url, name) if url else escape(name)


def join_names(names):
    names = [person(n) for n in names]
    return names[0] if len(names) == 1 else Markup(", ").join(names[:-1]) + Markup(" and ") + names[-1]


def authors(p):
    return join_names(Markup('<span class="me">{}</span>').format(a) if a == ME else a for a in p["authors"])


def coauthors(p):
    others = [a for a in p["authors"] if a != ME]
    return Markup("with ") + join_names(others) if others else "Sole author"


def _journal(p):
    return Markup('<span class="journal">{}</span>').format(p["venue"])


def venue_full(p):
    status = p.get("status")
    if status == "submitted":
        return "Submitted"
    if status == "to-appear":
        return Markup("To appear in ") + _journal(p)
    if status == "accepted":
        return Markup("Accepted for publication in ") + _journal(p)
    if status is None:  # proceedings
        return Markup("In ") + _journal(p)
    details = Markup(", {}").format(p["details"]) if p.get("details") else ""
    return _journal(p) + details


def venue_plain(p):
    status = p.get("status")
    if status == "submitted":
        return "Submitted"
    prefix = {"to-appear": "To appear in ", "accepted": "Accepted in "}.get(status, "")
    return prefix + p["venue"]


def venue_short(p):
    status = p.get("status")
    if status == "submitted":
        return f"Submitted, {p['year']}"
    prefix = {"to-appear": "To appear in ", "accepted": "Accepted in "}.get(status, "")
    return f"{prefix}{p['venue']}, {p['year']}"


def mainlink(p):
    links = p.get("links", {})
    for key in ("journal", "arxiv", "pdf"):
        if links.get(key):
            return fileurl(links[key])
    return "publications.html"


def figure(name):
    """A paper illustration: an image file in assets/fig/, or a generated SVG by name."""
    if Path(name).suffix:
        return Markup('<img src="assets/fig/{}" alt="" loading="lazy">').format(fileurl(name))
    return Markup((ROOT / "assets" / "fig" / f"{name}.svg").read_text(encoding="utf-8"))


def groupby_year(items):
    return [(year, list(group)) for year, group in groupby(items, key=lambda p: p["year"])]


def month_year(d):
    return str(d) if isinstance(d, int) else d.strftime("%b %Y")


def _talk_date(t):
    d = t["date"]
    return date(d, 1, 1) if isinstance(d, int) else d


def end_period(text):
    """Finish a line with a full stop unless it already ends with punctuation."""
    s = str(text).rstrip()
    plain = re.sub(r"<[^>]+>", "", s).rstrip()
    if not plain or plain[-1] in ".?!…":
        return text
    return Markup(s + ".") if isinstance(text, Markup) else s + "."


def _period_part(value):
    if value == "present":
        return "present"
    if isinstance(value, int):
        return str(value)
    return date(*map(int, value.split("-")), 1).strftime("%b %Y")


def period(item):
    """'Sep 2025 – Jun 2027', 'Mar 2024', '2020 – 2021', or '' when undated."""
    start, end = item.get("start"), item.get("end")
    if start is None:
        return ""
    if end is None or end == start:
        return _period_part(start)
    return f"{_period_part(start)} – {_period_part(end)}"


def period_open(item):
    """Like period(), but a missing end means the item is ongoing."""
    return period(dict(item, end=item.get("end", "present")))


def is_current(item, today, open_ended=False):
    """Still going: end is "present", in the future, or (when open_ended) not given."""
    end = item.get("end")
    if end == "present":
        return True
    if end is None:
        return open_ended
    y, m = (end, 1) if isinstance(end, int) else map(int, end.split("-"))  # a bare year counts as ended
    return (y, m) >= (today.year, today.month)


def _start_key(item):
    s = item.get("start")
    return (0, "") if s is None else (1, f"{s}-12" if isinstance(s, int) else str(s))


def _end_key(item):
    e = item.get("end")
    if e is None:
        return _start_key(item)
    return (1, f"{e}-12" if isinstance(e, int) else str(e))


SERVICE_KINDS = [("admin", "Administrative responsibilities"), ("organization", "Scientific organization"),
                 ("editorial", "Editorial work")]
STUDENT_LEVELS = [("postdoc", "Postdoctoral researchers"), ("phd", "Ph.D. students"), ("msc", "M.Sc. students"),
                  ("undergrad", "Undergraduate research"), ("visiting", "Visiting graduate students")]


def split_by_time(items, today, field, labels, open_ended=False):
    """{'current': [(label, [items])], 'past': [...]}, newest first, empty groups dropped."""
    out = {"current": {k: [] for k, _ in labels}, "past": {k: [] for k, _ in labels}}
    for item in sorted(items, key=_start_key, reverse=True):
        out["current" if is_current(item, today, open_ended) else "past"][item[field]].append(item)
    for group in out["past"].values():  # past items: most recently ended first
        group.sort(key=lambda item: (_end_key(item), _start_key(item)), reverse=True)
    return {when: [(label, groups[k]) for k, label in labels if groups[k]] for when, groups in out.items()}


def topic_groups(pubs):
    """[(topic, [papers])] for the "By topic" view, in the order the topics are listed."""
    return [(t, [p for p in pubs["articles"] if t["id"] in p.get("topics", [])]) for t in pubs["topics"]]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ------------------------------------------------------------------ build

def read_page(path):
    """A Markdown page with a YAML header between --- lines."""
    _, header, body = path.read_text(encoding="utf-8").split("---", 2)
    meta = yaml.safe_load(header)
    return meta, Markup(markdown.markdown(body))


def main():
    site, pubs = load("site.yml"), load("publications.yml")
    talks, students = load("talks.yml"), load("students.yml")
    teaching, service = load("teaching.yml"), load("service.yml")
    for c in load("people.yml"):
        PEOPLE[c["name"]] = PEOPLE[c["short"]] = c["url"]
    for group in (pubs["articles"], pubs["proceedings"]):
        for i, p in enumerate(group):
            p["_idx"] = i
    for section in talks:  # talks are numbered within each section, counting down (newest = highest)
        for i, t in enumerate(section["talks"]):
            t["_num"] = len(section["talks"]) - i
    recent_talks = sorted((t for s in talks for t in s["talks"]), key=_talk_date, reverse=True)[:4]

    env = Environment(loader=FileSystemLoader(ROOT / "_templates"), autoescape=True,
                      trim_blocks=True, lstrip_blocks=True)
    env.filters.update(fileurl=fileurl, md=md, authors=authors, coauthors=coauthors,
                       venue_full=venue_full, venue_short=venue_short, venue_plain=venue_plain,
                       mainlink=mainlink, person=person,
                       figure=figure, groupby_year=groupby_year, month_year=month_year,
                       slug=slug, join_names=join_names, period=period,
                       period_open=period_open, end_period=end_period)
    css_version = hashlib.sha1((ROOT / "assets" / "style.css").read_bytes()).hexdigest()[:8]
    context = dict(css_version=css_version, site=site, pubs=pubs, talks=talks, students=students, recent_talks=recent_talks,
                   teaching=teaching,
                   service=split_by_time(service["roles"], date.today(), "kind", SERVICE_KINDS),
                   people=split_by_time(students, date.today(), "level", STUDENT_LEVELS, open_ended=True),
                   topic_groups=topic_groups(pubs),
                   topic_papers={t["id"]: papers for t, papers in topic_groups(pubs)})

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    for out_name, (template, title) in PAGES.items():
        html = env.get_template(template).render(**context, page=out_name, title=title)
        (OUT / out_name).write_text(html, encoding="utf-8")

    pages = sorted((ROOT / "_pages").glob("*.md"))  # optional free-form Markdown pages
    for path in pages:
        meta, body = read_page(path)
        out_name = f"{path.stem}.html"
        html = env.get_template("page.html").render(**context, page=out_name, title=meta["title"], body=body)
        (OUT / out_name).write_text(html, encoding="utf-8")

    for old, target in REDIRECTS.items():
        write_redirect(old, target, site["url"])

    shutil.copytree(ROOT / "assets", OUT / "assets")
    if (ROOT / "files").exists():
        shutil.copytree(ROOT / "files", OUT / "files")
    (OUT / ".nojekyll").touch()
    print(f"built {len(PAGES) + len(pages)} pages into {OUT}")


if __name__ == "__main__":
    main()
