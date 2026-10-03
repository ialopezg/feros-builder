# Third-Party Components

The project source license is in [LICENSE](LICENSE). It does not replace the
licenses of components embedded in a standalone executable.

PyInstaller packages the active CPython runtime, its used standard-library
components, and required native libraries. The PyInstaller bootloader carries
its own license and distribution exception. Build dependencies such as
setuptools and platform helpers may not all be embedded.

The packaging script copies CPython's installed license and available license
files from the installed PyInstaller distribution into `licenses/`. It records
installed Python distributions in `BUILD-INFO.json`; that list is a build
environment inventory, not a complete binary SBOM or license determination.

Before publication, review the actual native dependencies (`otool -L` on macOS,
`ldd` on a trusted Linux build, and `dumpbin /DEPENDENTS` when available on
Windows), PyInstaller analysis output, and applicable
notices for bundled libraries such as OpenSSL and compression libraries. Add
additional required notices under `licenses/` in the repository; the packager
copies that directory into the archive. Do not publish until that review is
complete. No firmware or Core payload is included in a Builder release.

References:

- https://docs.python.org/3/license.html
- https://pyinstaller.org/en/stable/license.html
- https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt
