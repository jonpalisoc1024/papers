# Jonathan Palisoc — CV and Working Papers

Ph.D. Candidate, Health Services Organization & Policy, University of Michigan.

- **CV:** <https://papers.jonpalisoc.com/cv.pdf>
- **Working papers:** see [`papers/`](papers/) — each PDF is the latest working draft.

Custom domain: <https://papers.jonpalisoc.com>. The PDFs hosted here are linked from my [CV](https://papers.jonpalisoc.com/cv.pdf) and from <https://www.jonpalisoc.com>; replacing a file here automatically updates the link target.

For published work, see my CV.

## Updating

The repo is fed by [`sync.py`](sync.py), which copies the latest manuscript PDF for each paper out of the private research pipelines and refreshes `cv.pdf` from `~/Documents/Jobs/JPalisocCV.pdf`.

```sh
# Common operations
python3 sync.py                  # sync all papers + CV, commit, push
python3 sync.py --dry-run        # show what would change, no writes
python3 sync.py public-charge-chilling   # sync just one paper
python3 sync.py --cv-only        # only refresh cv.pdf
python3 sync.py --no-push        # commit locally but don't push
```

For each public slug the script prefers, in order:

1. `<pipeline>/<subdir>/<paper>/manuscript/draft_combined.pdf`
2. `manuscript/draft_combined_with_figures.pdf`
3. `manuscript/submission/<journal>/manuscript.pdf`
4. `manuscript/submission/<journal>/submission-manuscript.pdf`

To add a new paper, append a row to the `PAPERS` list at the top of `sync.py`.
