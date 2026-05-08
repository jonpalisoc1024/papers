#!/usr/bin/env python3
"""
Sync the latest manuscript PDFs from the private research pipelines into
this public repo, then commit + push any changes.

Usage:
    python3 sync.py                # sync all papers + CV, commit, push
    python3 sync.py --no-push      # sync + commit, skip push
    python3 sync.py --dry-run      # show what would change, no writes
    python3 sync.py <slug> [...]   # sync only the named slugs
    python3 sync.py --cv-only      # just refresh cv.pdf

Source-of-truth for each slug is, in order:
    1. <pipeline>/papers/<src_dir>/manuscript/draft_combined.pdf
    2. <pipeline>/papers/<src_dir>/manuscript/submission/<journal>/manuscript.pdf
    3. <pipeline>/papers/<src_dir>/manuscript/submission/<journal>/submission-manuscript.pdf
    4. <pipeline>/future/<src_dir>/manuscript/<same as above>

Add new papers by appending to PAPERS below. To rename a public slug, edit
the first column; to point at a different source dir, edit src_dir.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

PAPERS_PUBLIC = Path("/Users/jonpalisoc/papers-public")
HEALTH = Path("/Users/jonpalisoc/research-pipeline")
PETS = Path("/Users/jonpalisoc/pet-research-pipeline")
CV_SRC = Path("/Users/jonpalisoc/Documents/Jobs/JPalisocCV.pdf")

# (public_slug, pipeline_root, paper_subdir, src_dirname, preferred_submission_journal)
# preferred_submission_journal is used only if draft_combined.pdf is missing.
PAPERS = [
    # public_slug                              pipeline_root  subdir   src_dirname                              journal
    ("administrative-wedge",                   HEALTH, "papers", "administrative-wedge",                  "health-affairs"),
    ("adult-dental",                           HEALTH, "future", "adult-dental",                          "hsr"),
    ("buprenorphine-pa",                       HEALTH, "papers", "buprenorphine-pa",                      "health-affairs"),
    ("ca-medi-cal-2024-expansion",             HEALTH, "future", "ca-medi-cal-26-49-expansion",           None),
    ("doula-coverage",                         HEALTH, "papers", "doula-coverage",                        "health-affairs"),
    ("evv-rollout",                            HEALTH, "papers", "evv-rollout",                           "health-affairs"),
    ("postpartum-extension-chronic-care",      HEALTH, "papers", "fertility-option-larc-ipi",             None),
    ("fmap-floor-ltss-rkd",                    HEALTH, "papers", "fmap-floor-ltss-rkd",                   "medical_care"),
    ("fqhc-nap-bartik-iv",                     HEALTH, "papers", "fqhc-nap-bartik-iv",                    None),
    ("medicaid-drug-pools",                    HEALTH, "papers", "medicaid-drug-pools",                   "health-affairs"),
    ("noncitizen-coverage",                    HEALTH, "papers", "noncitizen-coverage",                   "health-affairs"),
    ("oregon-healthier-oregon",                HEALTH, "future", "oregon-healthier-oregon-sdid",          None),
    ("pbm-spread-pricing",                     HEALTH, "papers", "pbm-spread-pricing",                    "hsr"),
    ("post-release-mortality",                 HEALTH, "papers", "post-release-mortality",                "health-affairs"),
    ("public-charge-chilling",                 HEALTH, "papers", "public-charge-chilling",                "health-affairs"),
    ("public-data-medicaid-fraud-playbook",    HEALTH, "papers", "public-data-medicaid-fraud-playbook",   None),
    ("reentry-waivers",                        HEALTH, "future", "reentry-waivers",                       None),
    ("rural-emergency-hospitals",              HEALTH, "papers", "rural-emergency-hospitals",             "health-services-research"),
    ("section-17000-backstop",                 HEALTH, "future", "section-17000-backstop",                None),
    ("ssa-office-closures-medicaid",           HEALTH, "papers", "ssa-office-closures-medicaid",          None),
    ("state-directed-payments-panel",          HEALTH, "future", "state-directed-payments-panel",         None),
    ("suspension-termination",                 HEALTH, "papers", "suspension-termination",                None),
    ("unwind-compliance",                      HEALTH, "papers", "unwind-compliance",                     "hsr"),
    ("unwinding-adult-health",                 HEALTH, "future", "unwinding-adult-health",                "health-affairs"),
    ("work-requirements",                      HEALTH, "future", "work-requirements",                     "hsr"),
    ("senior-dog-adoption-fee-waivers",        PETS,   "papers", "senior-dog-adoption-fee-waivers",       None),
]


def find_pdf(pipeline: Path, subdir: str, src_dirname: str, journal: str | None) -> Path | None:
    """Return the canonical manuscript PDF for one paper.

    Strict preference order:
        1. manuscript/draft_combined.pdf
        2. manuscript/draft_combined_with_figures.pdf
        3. manuscript/submission/<journal>/manuscript.pdf       (if journal given)
        4. manuscript/submission/<journal>/submission-manuscript.pdf
        5. manuscript/submission/<any>/manuscript.pdf           (most-recent first)
        6. manuscript/submission/<any>/submission-manuscript.pdf
    """
    paper_dir = pipeline / subdir / src_dirname
    if not paper_dir.exists():
        return None

    ms = paper_dir / "manuscript"

    # 1 & 2: draft_combined variants always win
    for name in ("draft_combined.pdf", "draft_combined_with_figures.pdf"):
        p = ms / name
        if p.exists():
            return p

    submission = ms / "submission"
    if not submission.exists():
        return None

    # 3 & 4: preferred journal
    if journal:
        for name in ("manuscript.pdf", "submission-manuscript.pdf"):
            p = submission / journal / name
            if p.exists():
                return p

    # 5 & 6: any journal, most recent
    fallbacks: list[Path] = []
    for jd in submission.iterdir():
        if not jd.is_dir():
            continue
        for name in ("manuscript.pdf", "submission-manuscript.pdf"):
            p = jd / name
            if p.exists():
                fallbacks.append(p)
    if not fallbacks:
        return None
    fallbacks.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return fallbacks[0]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sync_one(public_slug: str, src: Path, dry_run: bool) -> str:
    """Copy src into papers-public if it differs. Return status: 'updated', 'unchanged', 'new'."""
    dst = PAPERS_PUBLIC / f"{public_slug}.pdf"
    if not dst.exists():
        if dry_run:
            return "new (would copy)"
        shutil.copy2(src, dst)
        return "new"
    if sha256(src) == sha256(dst):
        return "unchanged"
    if dry_run:
        return "changed (would update)"
    shutil.copy2(src, dst)
    return "updated"


def sync_cv(dry_run: bool) -> str:
    if not CV_SRC.exists():
        return "skipped (CV pdf missing)"
    dst = PAPERS_PUBLIC / "cv.pdf"
    if dst.exists() and sha256(CV_SRC) == sha256(dst):
        return "unchanged"
    if dry_run:
        return "would update"
    shutil.copy2(CV_SRC, dst)
    return "updated"


def git_commit_and_push(no_push: bool, dry_run: bool) -> bool:
    """Stage, commit, push any changes in papers-public. Return True if anything pushed/committed."""
    repo = PAPERS_PUBLIC
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if not status:
        return False
    print("\nChanges:")
    print(status)
    if dry_run:
        print("(dry-run; not committing)")
        return False
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo),
         "-c", "user.email=jpalisoc@umich.edu",
         "-c", "user.name=Jonathan Palisoc",
         "commit", "-q", "-m", "Auto-sync from research pipelines"],
        check=True,
    )
    if no_push:
        print("(committed locally; --no-push so skipping push)")
        return True
    subprocess.run(["git", "-C", str(repo), "push", "-q", "origin", "main"], check=True)
    print("Pushed.")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*", help="Specific public slugs to sync (default: all)")
    ap.add_argument("--no-push", action="store_true", help="Commit locally but don't push")
    ap.add_argument("--dry-run", action="store_true", help="Print what would change; no writes")
    ap.add_argument("--cv-only", action="store_true", help="Only refresh cv.pdf")
    ap.add_argument("--no-cv", action="store_true", help="Skip CV refresh")
    args = ap.parse_args()

    print(f"Sync target: {PAPERS_PUBLIC}")
    print(f"Dry run: {args.dry_run}\n")

    updated = 0
    unchanged = 0
    missing = 0

    if not args.cv_only:
        for public_slug, pipeline, subdir, src_dirname, journal in PAPERS:
            if args.slugs and public_slug not in args.slugs:
                continue
            src = find_pdf(pipeline, subdir, src_dirname, journal)
            if src is None:
                print(f"  - {public_slug:42s} no PDF found (skipped)")
                missing += 1
                continue
            status = sync_one(public_slug, src, args.dry_run)
            print(f"  - {public_slug:42s} {status}  <- {src.relative_to(pipeline)}")
            if status in ("updated", "new"):
                updated += 1
            else:
                unchanged += 1

    if not args.no_cv:
        cv_status = sync_cv(args.dry_run)
        print(f"\nCV: {cv_status}")
        if cv_status == "updated":
            updated += 1

    print(f"\nSummary: {updated} updated, {unchanged} unchanged, {missing} missing.")
    if args.dry_run:
        return 0
    if updated == 0:
        print("Nothing to commit.")
        return 0
    git_commit_and_push(args.no_push, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
