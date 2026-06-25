# Capstone Documentation Index

This folder contains the reviewer-facing Kaggle capstone package for TradeFlow AgentOS.

## Final Submission Docs

- [Kaggle writeup](kaggle_writeup.md)
- [Five-minute video script and storyboard](video_script_5min.md)
- [Media gallery checklist](media_gallery_checklist.md)
- [Capstone readiness summary](CAPSTONE_READINESS.md)
- [Public repository checklist](PUBLIC_REPO_CHECKLIST.md)
- [Legacy writeup draft](KAGGLE_WRITEUP_DRAFT.md)
- [Legacy demo video script](DEMO_VIDEO_SCRIPT.md)
- [Legacy media gallery plan](MEDIA_GALLERY_PLAN.md)

## Judge Quickstart

The public judge quickstart lives in the repository [README.md For Kaggle Judges section](../../README.md#for-kaggle-judges).

## Evidence and Dashboard Generation

Generate the deterministic evidence index:

```bash
.venv/bin/python scripts/build_agentops_evidence_index.py
```

Generate the static local dashboard:

```bash
.venv/bin/python scripts/build_agentops_dashboard.py
```

Run final submission-package checks:

```bash
.venv/bin/python scripts/check_submission_package.py
```

Generated evidence and dashboard files are written under `artifacts/`, which is ignored by Git. This keeps the public repository clean while making all local artifacts reproducible from documented commands.
