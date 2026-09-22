# PyObjC 12.2.2 notice provenance

`LICENSE.txt` is copied byte-for-byte from `pyobjc_core-12.2.2/License.txt`
in the upstream PyPI source distribution. `ADDITIONAL-NOTICES.txt` preserves
additional copyright/permission comments from the five named source files.

Source metadata: https://pypi.org/pypi/pyobjc-core/12.2.2/json
Source archive: https://files.pythonhosted.org/packages/a5/78/abc4ce5920305780aeb36b4067a86253378b36e29ba96673a3deb02eb03a/pyobjc_core-12.2.2.tar.gz
Archive SHA256: 3906452339cd06a3bb07df103c2511d4cb0f7a22d8771c0b802eba15d9a642b6

The digest was checked against PyPI metadata before extracting these notices.

This PyObjC release links to macOS `/usr/lib/libffi.dylib`; it does not bundle
libffi source or a libffi binary. The source `setup.py` uses `-lffi`, and the
packaged `_objc.cpython-314-darwin.so` confirms that system-library dependency.
The historical `libffi-src` wording in the upstream license is retained as
published. No separate downloaded libffi license is attributed to this build.
