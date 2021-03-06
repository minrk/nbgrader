import os
from os.path import join, exists, isfile

from .. import run_python_module
from .base import BaseTestApp


class TestNbGraderFeedback(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_python_module(["nbgrader", "feedback", "--help-all"])

    def test_single_file(self, gradebook, course_dir):
        """Can feedback be generated for an unchanged assignment?"""
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])
        run_python_module(["nbgrader", "feedback", "ps1", "--db", gradebook])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))

    def test_force(self, gradebook, course_dir):
        """Ensure the force option works properly"""
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "source", "ps1", "data", "bar.txt"), "bar")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data", "bar.txt"), "bar")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])

        self._make_file(join(course_dir, "autograded", "foo", "ps1", "blah.pyc"), "asdf")
        run_python_module(["nbgrader", "feedback", "ps1", "--db", gradebook])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

        # check that it skips the existing directory
        os.remove(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        run_python_module(["nbgrader", "feedback", "ps1", "--db", gradebook])
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))

        # force overwrite the supplemental files
        run_python_module(["nbgrader", "feedback", "ps1", "--db", gradebook, "--force"])
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))

        # force overwrite
        os.remove(join(course_dir, "autograded", "foo", "ps1", "foo.txt"))
        run_python_module(["nbgrader", "feedback", "ps1", "--db", gradebook, "--force"])
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

    def test_filter_notebook(self, gradebook, course_dir):
        """Does feedback filter by notebook properly?"""
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "source", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "source", "ps1", "data", "bar.txt"), "bar")
        run_python_module(["nbgrader", "assign", "ps1", "--db", gradebook])

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "foo.txt"), "foo")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "data", "bar.txt"), "bar")
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "blah.pyc"), "asdf")
        run_python_module(["nbgrader", "autograde", "ps1", "--db", gradebook])
        run_python_module(["nbgrader", "feedback", "ps1", "--db", gradebook, "--notebook", "p1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

        # check that removing the notebook still causes it to run
        os.remove(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        os.remove(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        run_python_module(["nbgrader", "feedback", "ps1", "--db", gradebook, "--notebook", "p1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

        # check that running it again doesn"t do anything
        os.remove(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        run_python_module(["nbgrader", "feedback", "ps1", "--db", gradebook, "--notebook", "p1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

        # check that removing the notebook doesn"t cause it to run
        os.remove(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        run_python_module(["nbgrader", "feedback", "ps1", "--db", gradebook])

        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "foo.txt"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "data", "bar.txt"))
        assert not isfile(join(course_dir, "feedback", "foo", "ps1", "blah.pyc"))

    def test_permissions(self, course_dir):
        """Are permissions properly set?"""
        self._empty_notebook(join(course_dir, "source", "ps1", "foo.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "foo.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--create"])
        run_python_module(["nbgrader", "feedback", "ps1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.html"))
        assert self._get_permissions(join(course_dir, "feedback", "foo", "ps1", "foo.html")) == "444"

    def test_custom_permissions(self, course_dir):
        """Are custom permissions properly set?"""
        self._empty_notebook(join(course_dir, "source", "ps1", "foo.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._empty_notebook(join(course_dir, "submitted", "foo", "ps1", "foo.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--create"])
        run_python_module(["nbgrader", "feedback", "ps1", "--FeedbackApp.permissions=644"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "foo.html"))
        assert self._get_permissions(join(course_dir, "feedback", "foo", "ps1", "foo.html")) == "644"

    def test_force_single_notebook(self, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "autograde", "ps1", "--create"])
        run_python_module(["nbgrader", "feedback", "ps1"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        p1 = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        p2 = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p2.html"))

        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "feedback", "ps1", "--notebook", "p1", "--force"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        assert p1 != self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert p2 == self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p2.html"))

    def test_update_newer(self, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 PST")
        run_python_module(["nbgrader", "autograde", "ps1", "--create"])
        run_python_module(["nbgrader", "feedback", "ps1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt")) == "2015-02-02 15:58:23.948203 PST"
        p = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))

        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        self._make_file(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"), "2015-02-02 16:58:23.948203 PST")
        run_python_module(["nbgrader", "feedback", "ps1"])

        assert isfile(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt")) == "2015-02-02 16:58:23.948203 PST"
        assert p != self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))

    def test_update_newer_single_notebook(self, course_dir):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))
        run_python_module(["nbgrader", "assign", "ps1", "--create"])

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p2.ipynb"))
        self._make_file(join(course_dir, "submitted", "foo", "ps1", "timestamp.txt"), "2015-02-02 15:58:23.948203 PST")
        run_python_module(["nbgrader", "autograde", "ps1", "--create"])
        run_python_module(["nbgrader", "feedback", "ps1"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt")) == "2015-02-02 15:58:23.948203 PST"
        p1 = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        p2 = self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p2.html"))

        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p1.ipynb"))
        self._empty_notebook(join(course_dir, "autograded", "foo", "ps1", "p2.ipynb"))
        self._make_file(join(course_dir, "autograded", "foo", "ps1", "timestamp.txt"), "2015-02-02 16:58:23.948203 PST")
        run_python_module(["nbgrader", "feedback", "ps1", "--notebook", "p1"])

        assert exists(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert exists(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
        assert isfile(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt"))
        assert self._file_contents(join(course_dir, "feedback", "foo", "ps1", "timestamp.txt")) == "2015-02-02 16:58:23.948203 PST"
        assert p1 != self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p1.html"))
        assert p2 == self._file_contents(join(course_dir, "feedback", "foo", "ps1", "p2.html"))
