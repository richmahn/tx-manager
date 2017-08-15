from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
import mock
from libraries.general_tools.file_utils import unzip, add_contents_to_zip
from libraries.linters.obs_linter import ObsLinter
from libraries.resource_container.ResourceContainer import RC


class TestObsLinter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    obs_zip_file = os.path.join(resources_dir, 'obs_linter', 'en_obs.zip')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='temp_obs_')
        unzip(self.obs_zip_file, self.temp_dir)
        self.repo_dir = os.path.join(self.temp_dir, 'en_obs')
        self.rc = RC(directory=self.repo_dir)

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_lint(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = False
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingChapter(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        os.remove(os.path.join(self.repo_dir, '25.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingFrame(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        shutil.copy(os.path.join(self.repo_dir, '01-no-frame.md'), os.path.join(self.repo_dir, '01.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingReference(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        shutil.copy(os.path.join(self.repo_dir, '01-no-reference.md'), os.path.join(self.repo_dir, '01.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingTitle(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        shutil.copy(os.path.join(self.repo_dir, '01-no-title.md'), os.path.join(self.repo_dir, '01.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingFront(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        os.remove(os.path.join(self.repo_dir, 'front.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingBack(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        os.remove(os.path.join(self.repo_dir, 'back.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorEnglishFront(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        shutil.copy(os.path.join(self.repo_dir, 'en-front.md'), os.path.join(self.repo_dir, 'front.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorEnglishBack(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        shutil.copy(os.path.join(self.repo_dir, 'en-back.md'), os.path.join(self.repo_dir, 'back.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    def run_linter(self):
        zip_file = tempfile.mktemp(prefix='en_obs_', suffix='.zip', dir=self.temp_dir)
        add_contents_to_zip(zip_file, self.repo_dir)
        linter = ObsLinter('bogus url', rc=self.rc)
        linter.source_zip_file = zip_file
        linter.run()
        return linter

    def verify_results(self, expected_errors, expected_warnings, linter):
        self.assertEqual(len(linter.log.logs["warning"]) > 0, expected_warnings)