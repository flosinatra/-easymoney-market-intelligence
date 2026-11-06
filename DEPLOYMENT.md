# EasyMoney source-verification preview — deployment checklist

This is a **public-source research preview**, not a completed five-gate engine or trade signal system.

1. Create a **private or public** GitHub repository and upload the contents of `easymoney_prototype/` at the repository root (not the enclosing folder). For GitHub Pages on some account plans, a public repository may be required; check current plan limits.
2. Under repository Settings → Actions → General, allow GitHub Actions and give workflow `Read and write permissions` if permitted. This workflow commits public research snapshots.
3. In Actions, open **Treasury daily evidence** and select **Run workflow**. Inspect each step and the collection receipt; do not treat a green job as proof every data source succeeded.
4. Under Settings → Pages, select **GitHub Actions** as the publishing source before the first workflow run. Open the URL GitHub displays. It may take several minutes to publish.
5. Verify the page shows a real observation date, retrieval timestamp, latest collection health and unresolved research statuses. A successful page load alone does not verify feeds.
6. Scheduled collection runs weekdays at 23:15 UTC; the GitHub Actions schedule may be delayed or skipped during service load. The page must flag stale data.

**Security:** The `/docs` site and its history can be publicly visible. Never commit brokerage credentials, API keys, trading journals or private account details. Do not put secrets into `docs/`.

**Known limitations:** Live endpoint success has not been demonstrated in this environment. The dashboard cannot assign five-factor scores, pass gates or generate validated futures trades. FRED CSV observations are context-only without verified release dates. The collector may require endpoint maintenance. Hosting requires an account owner to authorize repository and Pages settings.

## Preflight and acceptance criteria

Run `python deployment_preflight.py` before uploading. This verifies required files and workflow references, not live endpoints or GitHub authorization.

After a GitHub Actions run, inspect `docs/hosted_collection_receipt.json` and `docs/macro_collection_health.json`. Confirm source-specific success and real observation dates before calling the feed operational. If both providers fail, the dashboard is not live.

The `EasyMoney_GitHub_Ready_v0_25.zip` has repository-root files rather than an enclosing folder. It is not automatically deployed.
