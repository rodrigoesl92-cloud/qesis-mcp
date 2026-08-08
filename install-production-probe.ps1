# ============================================================
# QESIS+ :: install the hourly production probe
# Run in pwsh from C:\Users\Lenovo\qesis-mcp
# ============================================================
Set-Location C:\Users\Lenovo\qesis-mcp
$ErrorActionPreference = 'Stop'

$wf = @'
name: Production probe

on:
  schedule:
    - cron: "17 * * * *"      # hourly, offset off the hour to dodge runner congestion
  workflow_dispatch:           # lets you run it by hand from the Actions tab

permissions:
  contents: read
  issues: write                # needed to raise an alert

concurrency:
  group: production-probe
  cancel-in-progress: false

jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Read the expected index hash from the committed artifact
        id: expect
        run: |
          python - <<'PY' >> "$GITHUB_OUTPUT"
          import hashlib, pathlib
          sha = hashlib.sha256(pathlib.Path("data/qesis_v8.json").read_bytes()).hexdigest()
          print(f"index_sha={sha}")
          PY

      - name: Probe production
        id: run
        continue-on-error: true
        run: |
          python scripts/verify_production.py "${{ steps.expect.outputs.index_sha }}" "${{ github.sha }}" | tee probe.txt
          echo "exit=${PIPESTATUS[0]}" >> "$GITHUB_OUTPUT"

      - name: Raise an issue if production is not verified
        if: steps.run.outputs.exit != '0'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const out = fs.readFileSync('probe.txt', 'utf8');
            const title = 'Production probe failed';
            const existing = await github.rest.issues.listForRepo({
              owner: context.repo.owner, repo: context.repo.repo,
              state: 'open', labels: 'production-probe'
            });
            const body = [
              'The hourly probe could not certify production.',
              '',
              '```',
              out.trim(),
              '```',
              '',
              `Run: ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`,
              `Expected commit: ${context.sha}`,
              '',
              'Note: a `commit bound` failure alone usually means a newer deploy is',
              'still propagating. Two consecutive failures is the real signal.'
            ].join('\n');
            if (existing.data.length > 0) {
              await github.rest.issues.createComment({
                owner: context.repo.owner, repo: context.repo.repo,
                issue_number: existing.data[0].number, body
              });
            } else {
              await github.rest.issues.create({
                owner: context.repo.owner, repo: context.repo.repo,
                title, body, labels: ['production-probe']
              });
            }

      - name: Close the alert when production is healthy again
        if: steps.run.outputs.exit == '0'
        uses: actions/github-script@v7
        with:
          script: |
            const open = await github.rest.issues.listForRepo({
              owner: context.repo.owner, repo: context.repo.repo,
              state: 'open', labels: 'production-probe'
            });
            for (const i of open.data) {
              await github.rest.issues.createComment({
                owner: context.repo.owner, repo: context.repo.repo,
                issue_number: i.number,
                body: 'Production verified 5/5. Closing automatically.'
              });
              await github.rest.issues.update({
                owner: context.repo.owner, repo: context.repo.repo,
                issue_number: i.number, state: 'closed'
              });
            }

      - name: Fail the run so the Actions tab shows red
        if: steps.run.outputs.exit != '0'
        run: exit 1
'@

New-Item -ItemType Directory -Force -Path .github\workflows | Out-Null
Set-Content -Path .github\workflows\production-probe.yml -Value $wf -Encoding UTF8

git add .github/workflows/production-probe.yml
git commit -m "ops: hourly production probe, raises and closes an issue on state change"
$env:QESIS_HUMAN_PUSH="1"; git push origin main

Write-Host "`nInstalled. Run it once by hand now:" -ForegroundColor Cyan
Write-Host "  GitHub > Actions > Production probe > Run workflow" -ForegroundColor Cyan