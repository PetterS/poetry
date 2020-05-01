# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import shutil

import pytest

from poetry.factory import Factory
from poetry.io.null_io import NullIO
from poetry.masonry.builders.editable import EditableBuilder
from poetry.utils._compat import Path
from poetry.utils.env import EnvManager
from poetry.utils.env import MockEnv
from poetry.utils.env import VirtualEnv


@pytest.fixture()
def simple_poetry():
    poetry = Factory().create_poetry(
        Path(__file__).parent.parent.parent / "fixtures" / "simple_project"
    )

    return poetry


@pytest.fixture()
def extended_poetry():
    poetry = Factory().create_poetry(
        Path(__file__).parent.parent.parent / "fixtures" / "extended_project"
    )

    return poetry


@pytest.fixture()
def env_manager(simple_poetry):
    return EnvManager(simple_poetry)


@pytest.fixture
def tmp_venv(tmp_dir, env_manager):
    venv_path = Path(tmp_dir) / "venv"

    env_manager.build_venv(str(venv_path))

    venv = VirtualEnv(venv_path)
    yield venv

    shutil.rmtree(str(venv.path))


def test_builder_installs_proper_files_for_standard_packages(simple_poetry, tmp_venv):
    builder = EditableBuilder(simple_poetry, tmp_venv, NullIO())

    builder.build()

    assert tmp_venv._bin_dir.joinpath("foo").exists()
    assert tmp_venv.site_packages.joinpath("simple_project.pth").exists()
    assert (
        str(simple_poetry.file.parent.resolve())
        == tmp_venv.site_packages.joinpath("simple_project.pth").read_text()
    )

    dist_info = tmp_venv.site_packages.joinpath("simple_project-1.2.3.dist-info")
    assert dist_info.exists()
    assert dist_info.joinpath("INSTALLER").exists()
    assert dist_info.joinpath("METADATA").exists()
    assert dist_info.joinpath("RECORD").exists()
    assert dist_info.joinpath("entry_points.txt").exists()

    assert "poetry" == dist_info.joinpath("INSTALLER").read_text()
    assert (
        "[console_scripts]\nfoo=foo:bar\n\n"
        == dist_info.joinpath("entry_points.txt").read_text()
    )

    metadata = """\
Metadata-Version: 2.1
Name: simple-project
Version: 1.2.3
Summary: Some description.
Home-page: https://python-poetry.org
License: MIT
Keywords: packaging,dependency,poetry
Author: Sébastien Eustace
Author-email: sebastien@eustace.io
Requires-Python: >=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*
Classifier: License :: OSI Approved :: MIT License
Classifier: Programming Language :: Python :: 2
Classifier: Programming Language :: Python :: 2.7
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python :: 3.4
Classifier: Programming Language :: Python :: 3.5
Classifier: Programming Language :: Python :: 3.6
Classifier: Programming Language :: Python :: 3.7
Classifier: Programming Language :: Python :: 3.8
Classifier: Topic :: Software Development :: Build Tools
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Project-URL: Documentation, https://python-poetry.org/docs
Project-URL: Repository, https://github.com/python-poetry/poetry
Description-Content-Type: text/x-rst

My Package
==========

"""
    assert metadata == dist_info.joinpath("METADATA").read_text(encoding="utf-8")

    records = dist_info.joinpath("RECORD").read_text()
    assert str(tmp_venv.site_packages.joinpath("simple_project.pth")) in records
    assert str(tmp_venv._bin_dir.joinpath("foo")) in records
    assert str(dist_info.joinpath("METADATA")) in records
    assert str(dist_info.joinpath("INSTALLER")) in records
    assert str(dist_info.joinpath("entry_points.txt")) in records
    assert str(dist_info.joinpath("RECORD")) in records


def test_builder_falls_back_on_setup_and_pip_for_packages_with_build_scripts(
    extended_poetry,
):
    env = MockEnv(path=Path("/foo"))
    builder = EditableBuilder(extended_poetry, env, NullIO())

    builder.build()

    assert [
        [
            "python",
            "-m",
            "pip",
            "install",
            "-e",
            str(extended_poetry.file.parent),
            "--no-deps",
        ]
    ] == env.executed
