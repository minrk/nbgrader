import os
import pytest

from os.path import join
from sqlalchemy.exc import InvalidRequestError

from ...api import Gradebook
from .. import run_python_module
from .base import BaseTestApp


class TestNbGraderAssign(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_python_module(["nbgrader", "assign", "--help-all"])

    def test_no_args(self):
        """Is there an error if no arguments are given?"""
        run_python_module(["nbgrader", "assign"], retcode=1)

    def test_conflicting_args(self):
        """Is there an error if assignment is specified both in config and as an argument?"""
        run_python_module(["nbgrader", "assign", "--assignment", "foo", "foo"], retcode=1)

    def test_multiple_args(self):
        """Is there an error if multiple arguments are given?"""
        run_python_module(["nbgrader", "assign", "foo", "bar"], retcode=1)

    def test_no_assignment(self, course_dir):
        """Is an error thrown if the assignment doesn't exist?"""
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        run_python_module(["nbgrader", "assign", "ps1"], retcode=1)

    def test_single_file(self, course_dir):
        """Can a single file be assigned?"""
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        run_python_module(["nbgrader", "assign", "ps1", "--create"])
        assert os.path.isfile(join(course_dir, "release", "ps1", "foo.ipynb"))

    def test_multiple_files(self, course_dir):
        """Can multiple files be assigned?"""
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'bar.ipynb'))
        run_python_module(["nbgrader", "assign", "ps1", "--create"])
        assert os.path.isfile(join(course_dir, 'release', 'ps1', 'foo.ipynb'))
        assert os.path.isfile(join(course_dir, 'release', 'ps1', 'bar.ipynb'))

    def test_dependent_files(self, course_dir):
        """Are dependent files properly linked?"""
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'foo.csv'), 'foo')
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'bar.csv'), 'bar')
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'bar.ipynb'))
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        assert os.path.isfile(join(course_dir, 'release', 'ps1', 'foo.ipynb'))
        assert os.path.isfile(join(course_dir, 'release', 'ps1', 'bar.ipynb'))
        assert os.path.isfile(join(course_dir, 'release', 'ps1', 'data', 'foo.csv'))
        assert os.path.isfile(join(course_dir, 'release', 'ps1', 'data', 'bar.csv'))

        with open(join(course_dir, 'release', 'ps1', 'data', 'foo.csv'), 'r') as fh:
            assert fh.read() == 'foo'
        with open(join(course_dir, 'release', 'ps1', 'data', 'bar.csv'), 'r') as fh:
            assert fh.read() == 'bar'

    def test_save_cells(self, db, course_dir):
        """Ensure cells are saved into the database"""
        self._copy_file(join('files', 'test.ipynb'), join(course_dir, 'source', 'ps1', 'test.ipynb'))

        gb = Gradebook(db)
        gb.add_assignment("ps1")

        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        notebook = gb.find_notebook("test", "ps1")
        assert len(notebook.grade_cells) == 6

    def test_force(self, course_dir):
        """Ensure the force option works properly"""
        self._copy_file(join('files', 'test.ipynb'), join(course_dir, 'source', 'ps1', 'test.ipynb'))
        self._make_file(join(course_dir, 'source', 'ps1', 'foo.txt'), "foo")
        self._make_file(join(course_dir, 'source', 'ps1', 'data', 'bar.txt'), "bar")
        self._make_file(join(course_dir, 'source', 'ps1', 'blah.pyc'), "asdf")

        run_python_module(["nbgrader", "assign", "ps1", "--create"])
        assert os.path.isfile(join(course_dir, 'release', 'ps1', 'test.ipynb'))
        assert os.path.isfile(join(course_dir, 'release', 'ps1', 'foo.txt'))
        assert os.path.isfile(join(course_dir, 'release', 'ps1', 'data', 'bar.txt'))
        assert not os.path.isfile(join(course_dir, 'release', 'ps1', 'blah.pyc'))

        # check that it skips the existing directory
        os.remove(join(course_dir, 'release', 'ps1', 'foo.txt'))
        run_python_module(["nbgrader", "assign", "ps1"])
        assert not os.path.isfile(join(course_dir, 'release', 'ps1', 'foo.txt'))

        # force overwrite the supplemental files
        run_python_module(["nbgrader", "assign", "ps1", "--force"])
        assert os.path.isfile(join(course_dir, 'release', 'ps1', 'foo.txt'))

        # force overwrite
        os.remove(join(course_dir, 'source', 'ps1', 'foo.txt'))
        run_python_module(["nbgrader", "assign", "ps1", "--force"])
        assert os.path.isfile(join(course_dir, "release", "ps1", "test.ipynb"))
        assert os.path.isfile(join(course_dir, "release", "ps1", "data", "bar.txt"))
        assert not os.path.isfile(join(course_dir, "release", "ps1", "foo.txt"))
        assert not os.path.isfile(join(course_dir, "release", "ps1", "blah.pyc"))

    def test_permissions(self, course_dir):
        """Are permissions properly set?"""
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        self._make_file(join(course_dir, 'source', 'ps1', 'foo.txt'), 'foo')
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        assert os.path.isfile(join(course_dir, "release", "ps1", "foo.ipynb"))
        assert os.path.isfile(join(course_dir, "release", "ps1", "foo.txt"))
        assert self._get_permissions(join(course_dir, "release", "ps1", "foo.ipynb")) == "644"
        assert self._get_permissions(join(course_dir, "release", "ps1", "foo.txt")) == "644"

    def test_custom_permissions(self, course_dir):
        """Are custom permissions properly set?"""
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'foo.ipynb'))
        self._make_file(join(course_dir, 'source', 'ps1', 'foo.txt'), 'foo')
        run_python_module(["nbgrader", "assign", "ps1", "--create", "--AssignApp.permissions=666"])

        assert os.path.isfile(join(course_dir, "release", "ps1", "foo.ipynb"))
        assert os.path.isfile(join(course_dir, "release", "ps1", "foo.txt"))
        assert self._get_permissions(join(course_dir, "release", "ps1", "foo.ipynb")) == "666"
        assert self._get_permissions(join(course_dir, "release", "ps1", "foo.txt")) == "666"

    def test_add_remove_extra_notebooks(self, db, course_dir):
        """Are extra notebooks added and removed?"""
        gb = Gradebook(db)
        assignment = gb.add_assignment("ps1")

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "test.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        gb.db.refresh(assignment)
        assert len(assignment.notebooks) == 1
        notebook1 = gb.find_notebook("test", "ps1")

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "test2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db, "--force"])

        gb.db.refresh(assignment)
        assert len(assignment.notebooks) == 2
        gb.db.refresh(notebook1)
        notebook2 = gb.find_notebook("test2", "ps1")

        os.remove(join(course_dir, "source", "ps1", "test2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db, "--force"])

        gb.db.refresh(assignment)
        assert len(assignment.notebooks) == 1
        gb.db.refresh(notebook1)
        with pytest.raises(InvalidRequestError):
            gb.db.refresh(notebook2)

    def test_add_extra_notebooks_with_submissions(self, db, course_dir):
        """Is an error thrown when new notebooks are added and there are existing submissions?"""
        gb = Gradebook(db)
        assignment = gb.add_assignment("ps1")

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "test.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        gb.db.refresh(assignment)
        assert len(assignment.notebooks) == 1

        gb.add_student("hacker123")
        gb.add_submission("ps1", "hacker123")

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "test2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db, "--force"], retcode=1)

    def test_remove_extra_notebooks_with_submissions(self, db, course_dir):
        """Is an error thrown when notebooks are removed and there are existing submissions?"""
        gb = Gradebook(db)
        assignment = gb.add_assignment("ps1")

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "test.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "test2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        gb.db.refresh(assignment)
        assert len(assignment.notebooks) == 2

        gb.add_student("hacker123")
        gb.add_submission("ps1", "hacker123")

        os.remove(join(course_dir, "source", "ps1", "test2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db, "--force"], retcode=1)

    def test_same_notebooks_with_submissions(self, db, course_dir):
        """Is it ok to run nbgrader assign with the same notebooks and existing submissions?"""
        gb = Gradebook(db)
        assignment = gb.add_assignment("ps1")

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "test.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", db])

        gb.db.refresh(assignment)
        assert len(assignment.notebooks) == 1
        notebook = assignment.notebooks[0]

        gb.add_student("hacker123")
        submission = gb.add_submission("ps1", "hacker123")
        submission_notebook = submission.notebooks[0]

        run_python_module(["nbgrader", "assign", "ps1", "--db", db, "--force"])

        gb.db.refresh(assignment)
        assert len(assignment.notebooks) == 1
        gb.db.refresh(notebook)
        gb.db.refresh(submission)
        gb.db.refresh(submission_notebook)

    def test_force_single_notebook(self, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        assert os.path.exists(join(course_dir, "release", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "release", "ps1", "p2.ipynb"))
        p1 = self._file_contents(join(course_dir, "release", "ps1", "p1.ipynb"))
        p2 = self._file_contents(join(course_dir, "release", "ps1", "p2.ipynb"))
        assert p1 == p2

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--notebook", "p1", "--force"])

        assert os.path.exists(join(course_dir, "release", "ps1", "p1.ipynb"))
        assert os.path.exists(join(course_dir, "release", "ps1", "p2.ipynb"))
        assert p1 != self._file_contents(join(course_dir, "release", "ps1", "p1.ipynb"))
        assert p2 == self._file_contents(join(course_dir, "release", "ps1", "p2.ipynb"))

    def test_fail_no_notebooks(self):
        run_python_module(["nbgrader", "assign", "ps1", "--create"], retcode=1)
