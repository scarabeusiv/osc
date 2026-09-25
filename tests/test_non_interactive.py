import unittest
import unittest.mock

from osc import conf, oscerr
from osc.util import helper


class TestNonInteractiveConfig(unittest.TestCase):
    def setUp(self):
        self._prev = conf.config["non_interactive"]
        conf.config["non_interactive"] = False

    def tearDown(self):
        conf.config["non_interactive"] = self._prev

    def test_default_is_false(self):
        # fresh Options has it disabled
        self.assertFalse(conf.Options().non_interactive)

    def test_config_file_value(self):
        # set via the config Field machinery (as get_config would)
        conf.config["non_interactive"] = True
        self.assertTrue(conf.config["non_interactive"])


class TestRawInputNonInteractive(unittest.TestCase):
    def setUp(self):
        self._prev = conf.config["non_interactive"]
        conf.config["non_interactive"] = False

    def tearDown(self):
        conf.config["non_interactive"] = self._prev

    def test_interactive_reads_stdin(self):
        with unittest.mock.patch("builtins.input", return_value="y") as m:
            self.assertEqual(helper.raw_input("Proceed? "), "y")
            m.assert_called_once_with("Proceed? ")

    def test_interactive_eof_is_user_abort(self):
        with unittest.mock.patch("builtins.input", side_effect=EOFError):
            self.assertRaises(oscerr.UserAbort, helper.raw_input, "Proceed? ")

    def test_non_interactive_raises(self):
        conf.config["non_interactive"] = True
        with self.assertRaises(oscerr.NonInteractiveInput) as ctx:
            helper.raw_input("Proceed? (y/n) ")
        self.assertIn("Proceed? (y/n)", str(ctx.exception))
        self.assertIn("non-interactive", str(ctx.exception))

    def test_non_interactive_includes_hint(self):
        conf.config["non_interactive"] = True
        with self.assertRaises(oscerr.NonInteractiveInput) as ctx:
            helper.raw_input("Proceed? ", hint="Use --force to proceed without prompting.")
        self.assertIn("--force", str(ctx.exception))

    def test_non_interactive_error_is_osc_base_error(self):
        # babysitter.run() turns OscBaseError into exit code 1
        self.assertTrue(issubclass(oscerr.NonInteractiveInput, oscerr.OscBaseError))

    def test_non_interactive_returns_default_without_prompting(self):
        conf.config["non_interactive"] = True
        with unittest.mock.patch("builtins.input") as m:
            # simulates Enter: the documented default applies, nothing is read
            self.assertEqual(helper.raw_input("Proceed? (y/N) ", default=""), "")
            m.assert_not_called()

    def test_non_interactive_default_none_still_raises(self):
        conf.config["non_interactive"] = True
        with self.assertRaises(oscerr.NonInteractiveInput):
            helper.raw_input("Proceed? ", default=None, hint="Use --force.")


class TestPreflightHelpers(unittest.TestCase):
    def setUp(self):
        self._prev = conf.config["non_interactive"]
        conf.config["non_interactive"] = False

    def tearDown(self):
        conf.config["non_interactive"] = self._prev

    def test_require_all_present_passes(self):
        conf.config["non_interactive"] = True
        # no exception when all options are given
        helper.require_non_interactive_options("osc test", [("msg", "-m/--message")])

    def test_require_missing_raises(self):
        conf.config["non_interactive"] = True
        with self.assertRaises(oscerr.NonInteractiveInput) as ctx:
            helper.require_non_interactive_options("osc test", [(None, "-m/--message")])
        self.assertIn("-m/--message", str(ctx.exception))
        self.assertIn("osc test", str(ctx.exception))

    def test_require_names_all_missing(self):
        conf.config["non_interactive"] = True
        with self.assertRaises(oscerr.NonInteractiveInput) as ctx:
            helper.require_non_interactive_options(
                "osc test", [(None, "-a"), ("", "-b"), ("x", "-c")]
            )
        msg = str(ctx.exception)
        self.assertIn("-a", msg)
        self.assertIn("-b", msg)
        self.assertNotIn("-c", msg)

    def test_require_does_nothing_interactively(self):
        # interactive mode: missing options are fine (will prompt later)
        helper.require_non_interactive_options("osc test", [(None, "-m/--message")])

    def test_refuse_raises_in_non_interactive(self):
        conf.config["non_interactive"] = True
        with self.assertRaises(oscerr.NonInteractiveInput) as ctx:
            helper.refuse_non_interactive(
                "'osc test' always opens an editor",
                hint="Run without --non-interactive.",
            )
        self.assertIn("always opens an editor", str(ctx.exception))

    def test_refuse_does_nothing_interactively(self):
        helper.refuse_non_interactive("'osc test' always opens an editor", hint="hint")

    def test_raise_non_interactive(self):
        with self.assertRaises(oscerr.NonInteractiveInput) as ctx:
            helper.raise_non_interactive("some prompt", hint="Use --flag.")
        self.assertIn("some prompt", str(ctx.exception))
        self.assertIn("--flag", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
