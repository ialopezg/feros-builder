# Release Procedure

## Current status

The first release is planned as `v0.1.0`; it has not been published. The package
version alone does not mean a Git tag or GitHub Release exists.

## Prepare the candidate

1. Review the changes, confirm the MIT license, and update `CHANGELOG.md` from
   Unreleased to a dated version section when the candidate is ready.
2. Designate the private conduct contact and enable/test GitHub Private
   Vulnerability Reporting. Review CODEOWNERS and repository permissions.
3. Run source and executable tests on the supported CI matrix. Exercise actual
   image generation through the workspace menu (`make`), then retain the result.
4. Review third-party notices and native dependencies as described in
   `THIRD_PARTY.md`. Add required extra notices under `licenses/`.
5. Commit the completed candidate. Ensure the working tree is clean and the
   `pyproject.toml` version matches the intended tag. Push the reviewed commit.
6. Create an annotated or signed `vMAJOR.MINOR.PATCH` tag on that exact commit
   and push it. Never move a published release tag.

## Build a draft on GitHub

Run the **Release candidate** workflow manually from `main` and enter the
existing tag. The workflow checks out that tag, verifies its package version,
builds and tests native binaries on macOS ARM64 and Linux x86_64, packages them,
and verifies the extracted binaries with the CLI suite. Both platforms must
succeed before a separate job creates a draft GitHub Release.

Only that final job has `contents: write`. It uses the workflow's own artifacts
and never executes a downloaded binary. The workflow does not publish the draft
and refuses to overwrite an existing release. Restrict tag creation and workflow
changes to authorized maintainers using repository rulesets. Set the default
GITHUB_TOKEN permissions to read-only. CODEOWNERS alone does not enforce review;
configure required checks/reviews separately. Enable MFA for maintainer accounts.

## Local package verification

From the Builder repository, maintainers may use:

```bash
make release PYTHON=python3.13
.venv/bin/python scripts/package.py
```

This is the standalone product's release tooling. Workspace build operations
remain menu-driven. Packaging itself does not upload or publish anything.

The archive contains `builder`, README, LICENSE, CHANGELOG, SECURITY, VERSIONING,
STABILITY, THIRD_PARTY, `BUILD-INFO.json`, and collected license notices.
`dist/` receives a `.tar.gz` and its `.sha256` sidecar. To verify the download,
run `shasum -a 256 -c ARCHIVE.tar.gz.sha256` beside the archive. Inspect/extract
only a trusted package, then run its executable's help and the CLI regression
suite via the `BUILDER` environment variable from an unrelated working directory.

## Publish after review

Review the draft notes, tag/commit, CI results, archive contents, checksums,
license notices, and host compatibility information. State that the macOS
artifact is not notarized and that integrity validation does not establish
firmware authenticity or physical boot success. Publish the reviewed draft
manually. A release does not require or authorize a physical-media write.

If preparation fails, retain logs and fix the candidate before publication.
If a published release is wrong, mark the issue and ship a new version rather
than replacing the existing tag or assets.
