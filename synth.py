# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This script is used to synthesize generated parts of this library."""
import synthtool as s
from synthtool import gcp

AUTOSYNTH_MULTIPLE_PRS = True
AUTOSYNTH_MULTIPLE_COMMITS = True

gapic = gcp.GAPICMicrogenerator()
common = gcp.CommonTemplates()
versions = ["v1"]
admin_versions = ["v1"]


# ----------------------------------------------------------------------------
# Generate firestore GAPIC layer
# ----------------------------------------------------------------------------
for version in versions:
    library = gapic.py_library(
        service="firestore",
        version=version,
        proto_path=f"google/firestore/{version}",
        generator_version="v0.26.5"
    )

    s.move(
        library / f"google/firestore_{version}",
        f"google/cloud/firestore_{version}",
        excludes=[ library / f"google/firestore_{version}/__init__.py"]
    )
    
    s.move(library / "scripts" )


# ----------------------------------------------------------------------------
# Generate firestore admin GAPIC layer
# ----------------------------------------------------------------------------
for version in admin_versions:
    library = gapic.py_library(
        service="firestore_admin",
        version=version,
        # bazel_target=f"//google/firestore/admin/{version}:firestore-admin-{version}-py",
        # include_protos=True,
        proto_path=f"google/firestore/admin/{version}",
        generator_version="v0.33.3"
    )
    s.move(library / f"google/firestore/admin_{version}", f"google/cloud/firestore_admin_{version}")
    s.move(library / "tests")
    s.move(library / "scripts")

    s.replace(
        f"google/cloud/**/*.py",
        f"google.firestore.admin_v1",
        f"google.cloud.firestore_admin_v1",
    )
    s.replace(
        f"tests/unit/gapic/**/*.py",
        f"google.firestore.admin_v1",
        f"google.cloud.firestore_admin_v1",
    )
    s.replace(
        f"google/cloud/firestore_admin_v1/services/firestore_admin/client.py",
        f"from google.api_core import operation as ga_operation",
        f"from google.api_core import operation as ga_operation\nfrom google.api_core import operation",
    )


# ----------------------------------------------------------------------------
# Edit paths to firestore remove after resolving 
# https://github.com/googleapis/gapic-generator-python/issues/471
# ----------------------------------------------------------------------------
s.replace(
    f"tests/unit/gapic/**/*.py",
    f"google.firestore",
    f"google.cloud.firestore",
)
s.replace(
    f"google/cloud/**/*.py",
    f"google-firestore-admin",
    f"google-cloud-firestore",
)
s.replace(
    f"google/cloud/**/*.py",
    f"google-firestore",
    f"google-cloud-firestore",
)
s.replace(
    f"google/cloud/**/*.py",
    f"from google.firestore",
    f"from google.cloud.firestore",
)
s.replace(
    f"docs/**/*.rst",
    f"google.firestore",
    f"google.cloud.firestore",
)


# ----------------------------------------------------------------------------
# Add templated files
# ----------------------------------------------------------------------------
templated_files = common.py_library(
    samples=False,  # set to True only if there are samples
    unit_test_python_versions=["3.6", "3.7", "3.8"],
    system_test_python_versions=["3.7"],
    microgenerator=True,
)

s.move(
    templated_files,
    excludes=[".coveragerc"] # microgenerator has a good .coveragerc file
)

s.replace(
    "noxfile.py",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "FIRESTORE_APPLICATION_CREDENTIALS",
)

s.replace(
    "noxfile.py",
    '"--quiet", system_test',
    '"--verbose", system_test',
)

# Add pytype support

s.replace(
    ".gitignore",
    """\
.pytest_cache
""",
    """\
.pytest_cache
.pytype
""",
)

s.replace(
    "setup.cfg",
    """\
universal = 1
""",
    """\
universal = 1

[pytype]
python_version = 3.8
inputs =
    google/cloud/
exclude =
    tests/
output = .pytype/
# Workaround for https://github.com/google/pytype/issues/150
disable = pyi-error
""",
)

s.replace(
    "noxfile.py",
    """\
BLACK_VERSION = "black==19.10b0"
""",
    """\
PYTYPE_VERSION = "pytype==2020.7.24"
BLACK_VERSION = "black==19.10b0"
""",
)

s.replace(
    "noxfile.py",
    '''\
@nox.session\(python=DEFAULT_PYTHON_VERSION\)
def lint_setup_py\(session\):
''',
    '''\
@nox.session(python="3.7")
def pytype(session):
    """Run pytype
    """
    session.install(PYTYPE_VERSION)
    session.run("pytype",)


@nox.session(python=DEFAULT_PYTHON_VERSION)
def lint_setup_py(session):
''',
)

# Fix up unit test dependencies

s.replace(
    "noxfile.py",
    '''\
    session.install\("asyncmock", "pytest-asyncio"\)
''',
    '''\
    session.install("pytest-asyncio", "aiounittest")
''',
)

# Fix up system test dependencies

s.replace(
    "noxfile.py",
    '''"mock", "pytest", "google-cloud-testutils",''',
    '''"mock", "pytest", "pytest-asyncio", "google-cloud-testutils",''',
)

s.shell.run(["nox", "-s", "blacken"], hide_output=False)

s.replace(
    ".kokoro/build.sh",
    "# Setup service account credentials.",
    """\
# Setup firestore account credentials
export FIRESTORE_APPLICATION_CREDENTIALS=${KOKORO_GFILE_DIR}/firebase-credentials.json

# Setup service account credentials."""
)
