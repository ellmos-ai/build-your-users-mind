# Third-Party Licenses & Software Inventory

**Project:** `build-your-users-mind`  
**License:** [MIT License](LICENSE)  
**Audit Date:** 2026-09-11  

---

## Runtime Architecture & Dependencies

`build-your-users-mind` is designed and implemented as a **100% local-first, zero-egress, zero-external-dependency** system for local AI agents. The core extraction, normalization, merge, chunking, classification validation, statistics aggregation, and calibrated decision-prediction pipeline operates strictly within Python 3.10+ standard library boundaries.

### Zero-Runtime-Dependency Guarantee

| Package | Version Spec | License | Type | Purpose |
|---------|--------------|---------|------|---------|
| *None* | `n/a` | `n/a` | External | `build-your-users-mind` requires **0** external third-party packages at runtime (`dependencies = []` in `pyproject.toml`). |
| *Python Standard Library* | `>=3.10` | PSF License | Built-in | `__future__`, `argparse`, `collections`, `contextlib`, `copy`, `csv`, `datetime`, `hashlib`, `json`, `math`, `os`, `pathlib`, `random`, `re`, `sqlite3`, `subprocess`, `sys`, `tempfile`, `typing`, `urllib` (loopback only) |

### Network & Egress Invariants

- **Zero-Egress by Default**: All corpus extraction (`corpus_extract.py`), log merging (`merge_corpora.py`), chunking (`chunk_corpus.py`), validation (`validate_classifications.py`), and prediction scoring (`score_predictions.py`) run entirely offline.
- **Strict Loopback Boundary in Secure-Mode**: The optional Secure-Mode avatar prototype (`secure_text_avatar.py`) strictly validates endpoints via `urllib.parse` and rejects any hostname outside `{"127.0.0.1", "localhost", "::1"}` and schemes other than `http`. No external network socket can be initiated.

---

## Development & Test Dependencies

The following packages and tools are utilized exclusively during development, linting, packaging, and automated test execution:

| Package / Tool | Version Spec | License | Scope | Purpose |
|----------------|--------------|---------|-------|---------|
| [pytest](https://pytest.org/) | `>=7.0.0` | MIT | `[dev]` | Automated unit, contract, projection, and regression test execution |
| [ruff](https://github.com/astral-sh/ruff) | `>=0.5.0` | MIT OR Apache-2.0 | `[dev]` | High-performance Python linter and code formatting validation |
| [setuptools](https://github.com/pypa/setuptools) | `>=61.0` | MIT | `[build-system]` | Standard Python packaging and build backend |
| [build](https://github.com/pypa/build) | `>=1.0.0` | MIT OR Apache-2.0 | `[dev]` | PEP 517 package build frontend |

---

## License Texts & Attribution

### MIT License (`build-your-users-mind`, `pytest`, `ruff`, `setuptools`, `build`)

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Apache License 2.0 (`ruff`, `build` dual-license option)

```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### Python Software Foundation License (Python Standard Library)

```
1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and
   the Individual or Organization ("Licensee") accessing and otherwise using Python
   3.10+ software in source or binary form and its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
   grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
   analyze, test, perform and/or display publicly, prepare derivative works, distribute,
   and otherwise use Python alone or in any derivative version, provided, however, that
   PSF's License Agreement and PSF's notice of copyright, i.e., "Copyright © 2001-2026
   Python Software Foundation; All Rights Reserved" are included in Python alone or
   in any derivative version prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on or incorporates
   Python or any part thereof, and wants to make the derivative work available to
   others as provided herein, then Licensee hereby agrees to include in any such
   work a brief summary of the changes made to Python.

4. PSF is making Python available to Licensee on an "AS IS" basis. PSF MAKES NO
   REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED. BY WAY OF EXAMPLE, BUT NOT
   LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION OR WARRANTY OF
   MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF
   PYTHON WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON FOR ANY
   INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A RESULT OF MODIFYING,
   DISTRIBUTING, OR OTHERWISE USING PYTHON, OR ANY DERIVATIVE THEREOF, EVEN IF
   ADVISED OF THE POSSIBILITY THEREOF.
```
