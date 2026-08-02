# GitHub Actions workflow for qesis-mcp: notes
- This workflow installs R and the QCA package, then runs pytest.
- The R installation uses r-lib/actions/setup-r which provides a ready R environment.
- The QCA package is installed from CRAN. If additional system libraries are required, add apt-get install steps.
- tests/test_fsqca_integration.py runs the Rscript directly and does not require the signing key.
