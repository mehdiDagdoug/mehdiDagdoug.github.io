# mehdidagdoug.github.io

Personal website of Mehdi Dagdoug, published at <https://mehdidagdoug.github.io>.

All the content lives in plain text files. Change a file, push (or edit it directly on GitHub),
and the site rebuilds and republishes itself within a couple of minutes.

## Where things are

| To change…                                   | Edit                         |
|----------------------------------------------|------------------------------|
| Homepage text, bio, research page, links     | `_data/site.yml`             |
| Papers, research topics, Ph.D. thesis        | `_data/publications.yml`     |
| Talks and short courses                      | `_data/talks.yml`            |
| Courses taught, outreach                     | `_data/teaching.yml`         |
| Students and postdocs                        | `_data/students.yml`         |
| Committees and service                       | `_data/service.yml`          |
| Links on colleagues' names                   | `_data/people.yml`           |
| PDFs (papers, CV, thesis)                    | `files/`                     |
| CV source (LaTeX)                            | `cv/CV_Dagdoug.tex`          |

Each data file starts with a short comment explaining its format.
New papers and talks go at the top of their list; numbering and sorting are automatic.

## Previewing on your computer

```
pip install -r requirements.txt
python3 build.py      # builds the site into _site/
python3 serve.py      # then open http://localhost:4173
```

## Other tools

- `figures.py` makes the optional paper illustrations (`show_figures` in `_data/site.yml`).
- `preview_card.py` makes `assets/img/preview.png`, the image shown when the site is shared (macOS fonts).
- `.github/workflows/deploy.yml` builds and publishes the site on GitHub, on every push and once a week.

The previous version of the site is kept in the `old-site` branch.
