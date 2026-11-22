import argparse
import datetime
import json
import unittest
from unittest import mock

from tools import pr_ready

PACKAGES = {"apex-core": "crates/apex-core", "apex-client": "crates/apex-client",
            "apex-theme": "crates/apex-theme", "xtask": "xtask"}
LIBRARIES = set(PACKAGES) - {"xtask"}
DEPENDENCIES = {"apex-client": {"apex-core"}}
MODS = " --features apex-client/mods,apex-mods/pack"
CLIPPY = pr_ready.CI_CLIPPY + " && " + pr_ready.CI_CLIPPY_SERVER


def args(host="local", quick=False):
    return argparse.Namespace(host=host, quick=quick)


class PrReadyTests(unittest.TestCase):
    def test_paths_map_to_the_crates_that_own_them(self):
        self.assertEqual(pr_ready.touched_crates({"crates/apex-core/src/jmath.rs", "crates/apex-client/build.rs",
                                                  "xtask/src/main.rs", "tools/parity.py"}, PACKAGES),
                         ["apex-client", "apex-core", "xtask"])
        self.assertEqual(pr_ready.touched_crates({"crates/apex-core/README.md"}, PACKAGES), [])
        # The generated stylesheet is checked by apex-theme's tests.
        self.assertEqual(pr_ready.touched_crates({"crates/apex-theme/tokens.css"}, PACKAGES), ["apex-theme"])
        # A crate whose name prefixes another's directory doesn't own it.
        self.assertEqual(pr_ready.touched_crates({"crates/apex-core-extra/x.rs"}, PACKAGES), [])
        # The workspace manifest and lock touch every crate.
        self.assertIsNone(pr_ready.touched_crates({"Cargo.lock", "crates/apex-core/src/lib.rs"}, PACKAGES))

    def test_which_workspace_builds_a_path(self):
        self.assertTrue(pr_ready.workspace_rust("crates/apex-theme/fonts/x.ttf"))
        self.assertTrue(pr_ready.workspace_rust("Cargo.toml"))
        self.assertFalse(pr_ready.workspace_rust("crates/apex-client/README.md"))
        self.assertFalse(pr_ready.workspace_rust("launcher/src/main.rs"))
        self.assertTrue(pr_ready.launcher_rust("launcher/src/main.rs"))
        # CI's launcher job also runs for the root workspace's manifests and for its own check.
        self.assertTrue(pr_ready.launcher_rust("Cargo.lock"))
        self.assertTrue(pr_ready.launcher_rust("tools/ci/rust_changes.py"))
        self.assertTrue(pr_ready.launcher_rust("crates/apex-prepare/src/lib.rs"))
        self.assertTrue(pr_ready.launcher_rust("crates/apex-theme/src/lib.rs"))
        self.assertTrue(pr_ready.launcher_rust("crates/apex-telemetry/src/lib.rs"))
        self.assertFalse(pr_ready.launcher_rust("launcher/links.json"))
        self.assertFalse(pr_ready.launcher_rust("launcher/README.md"))
        self.assertFalse(pr_ready.launcher_rust("crates/apex-client/src/game.rs"))

    def test_crate_checks_do_not_link_unrelated_examples(self):
        with mock.patch.object(pr_ready, "affected_here", return_value=[]):
            steps = pr_ready.plan(args(quick=True), "origin/main", {"crates/apex-client/src/game.rs"}, PACKAGES, LIBRARIES, DEPENDENCIES)
        by_name = {step.name: step for step in steps}
        self.assertEqual(by_name["clippy"].command, CLIPPY)
        self.assertEqual(by_name["tests: apex-client"].command,
                         "cargo test --locked -p apex-client --features apex-client/mods --tests")
        self.assertEqual(by_name["doc tests"].command, "cargo test --locked -p apex-client --doc")
        self.assertIsNone(by_name["doc tests"].status)

    def test_content_root_tests_run_only_when_what_they_load_changes(self):
        def content_step(path):
            with mock.patch.object(pr_ready, "affected_here", return_value=[]):
                steps = pr_ready.plan(args(quick=True), "origin/main", {path}, PACKAGES, LIBRARIES, DEPENDENCIES)
            return {step.name: step for step in steps}["content root tests"]
        self.assertEqual(content_step("crates/apex-client/src/game.rs").skip, "content root untouched")
        for path in ["crates/apex-client/src/mod_content.rs", "crates/apex-client/src/mod_content_tests.rs",
                     "crates/apex-mods/src/content.rs", "crates/apex-assets/src/lib.rs", "Cargo.lock"]:
            with self.subTest(path=path):
                step = content_step(path)
                self.assertIsNone(step.skip)
                self.assertEqual(step.command, pr_ready.CONTENT_ROOT_TESTS)

    def test_shared_rust_configuration_keeps_workspace_coverage(self):
        for path in sorted(pr_ready.ROOT_RUST | {".cargo/config.toml", "crates/unknown/src/lib.rs"}):
            with self.subTest(path=path), mock.patch.object(pr_ready, "affected_here", return_value=[]):
                steps = pr_ready.plan(args(quick=True), "origin/main", {path}, PACKAGES, LIBRARIES, DEPENDENCIES)
                by_name = {step.name: step for step in steps}
                self.assertEqual(by_name["clippy"].command, CLIPPY)
                self.assertEqual(by_name["tests: workspace"].command,
                                 "cargo test --locked --workspace" + MODS + " --tests")
                self.assertEqual(by_name["doc tests"].command, "cargo test --locked --workspace --doc")

    def test_tests_get_the_features_ci_s_workspace_run_gives_them(self):
        self.assertEqual(pr_ready.mod_features(["apex-world"]), "")
        self.assertEqual(pr_ready.mod_features(["apex-client"]), " --features apex-client/mods")
        self.assertEqual(pr_ready.mod_features(["apex-mods"]),
                         " --features apex-mods/runtime,apex-mods/pack,apex-mods/index")
        self.assertEqual(pr_ready.mod_features(None), MODS)

    def test_python_tests_always_run(self):
        with mock.patch.object(pr_ready, "affected_here", return_value=[]):
            steps = pr_ready.plan(args(quick=True), "origin/main", {"crates/apex-core/src/lib.rs"},
                                  PACKAGES, LIBRARIES, DEPENDENCIES)
        self.assertIsNone({step.name: step for step in steps}["Python tests"].status)

    def test_non_rust_changes_skip_workspace_checks(self):
        for path in ("README.md", "tools/pr_ready.py", "launcher/src/main.rs"):
            with self.subTest(path=path), mock.patch.object(pr_ready, "affected_here", return_value=[]):
                steps = pr_ready.plan(args(quick=True), "origin/main", {path}, PACKAGES, LIBRARIES, DEPENDENCIES)
                by_name = {step.name: step for step in steps}
                for name in ("clippy", "tests", "doc tests"):
                    self.assertEqual(by_name[name].status, "skip")

    def test_multiple_touched_crates_share_the_same_check_scope(self):
        with mock.patch.object(pr_ready, "affected_here", return_value=[]):
            steps = pr_ready.plan(args(), "origin/main",
                                  {"crates/apex-core/src/lib.rs", "crates/apex-client/examples/probe.rs"}, PACKAGES, LIBRARIES, DEPENDENCIES)
        for step in steps:
            if step.name in ("tests: apex-client, apex-core", "doc tests"):
                self.assertIn("-p apex-client -p apex-core", step.command)
                self.assertIsNone(step.status)

    def test_binary_only_crates_skip_doc_tests(self):
        with mock.patch.object(pr_ready, "affected_here", return_value=[]):
            steps = pr_ready.plan(args(), "origin/main", {"xtask/src/main.rs"}, PACKAGES, LIBRARIES, DEPENDENCIES)
        by_name = {step.name: step for step in steps}
        self.assertEqual(by_name["tests: xtask"].command, "cargo test --locked -p xtask --tests")
        self.assertIsNone(by_name["tests: xtask"].status)
        self.assertEqual(by_name["doc tests"].status, "skip")
        with mock.patch.object(pr_ready, "affected_here", return_value=[]):
            steps = pr_ready.plan(args(), "origin/main",
                                  {"xtask/src/main.rs", "crates/apex-core/src/lib.rs"}, PACKAGES, LIBRARIES, DEPENDENCIES)
        by_name = {step.name: step for step in steps}
        self.assertEqual(by_name["doc tests"].command, "cargo test --locked -p apex-core --doc")

    def test_clippy_is_ci_s_and_the_server_build_when_the_game_is_affected(self):
        packages = {name: f"crates/{name}" for name in ("core", "world", "apex-client", "unrelated")}
        dependencies = {"world": {"core"}, "apex-client": {"world"}, "unrelated": set()}
        with mock.patch.object(pr_ready, "affected_here", return_value=[]):
            steps = pr_ready.plan(args(), "origin/main", {"crates/core/src/lib.rs"},
                                  packages, set(packages), dependencies)
            unrelated = pr_ready.plan(args(), "origin/main", {"crates/unrelated/src/lib.rs"},
                                      packages, set(packages), dependencies)
        self.assertEqual({step.name: step for step in unrelated}["clippy"].command, pr_ready.CI_CLIPPY)
        by_name = {step.name: step for step in steps}
        self.assertEqual(by_name["clippy"].command, CLIPPY)
        self.assertEqual(by_name["tests: core"].command, "cargo test --locked -p core --tests")
        self.assertEqual(by_name["doc tests"].command, "cargo test --locked -p core --doc")

    def test_dependent_scope_handles_cycles_and_multiple_changed_crates(self):
        dependencies = {"a": {"b"}, "b": {"a"}, "c": {"b"}, "d": set()}
        self.assertEqual(pr_ready.dependent_crates(["a"], dependencies), ["a", "b", "c"])
        self.assertEqual(pr_ready.dependent_crates(["a", "d"], dependencies), ["a", "b", "c", "d"])
        self.assertEqual(pr_ready.dependent_crates([], dependencies), [])
        self.assertIsNone(pr_ready.dependent_crates(None, dependencies))

    def test_metadata_includes_renamed_optional_platform_build_and_dev_consumers(self):
        core = str(pr_ready.ROOT / "crates/core")
        metadata = {"workspace_members": ["core", "optional", "build", "dev"], "packages": [
            {"id": "core", "name": "core", "manifest_path": core + "/Cargo.toml",
             "targets": [{"kind": ["lib"]}], "dependencies": []},
        ]}
        for name, kind in (("optional", None), ("build", "build"), ("dev", "dev")):
            metadata["packages"].append({
                "id": name, "name": name, "manifest_path": str(pr_ready.ROOT / f"crates/{name}/Cargo.toml"),
                "targets": [{"kind": ["bin"]}], "dependencies": [
                    {"name": "core", "rename": "alias", "path": core, "kind": kind,
                     "optional": name == "optional", "target": "cfg(windows)"},
                    {"name": "external", "path": None},
                ],
            })
        # A path dependency outside this workspace must not become a selectable package.
        metadata["packages"].append({"id": "outside", "name": "outside", "manifest_path": "/outside/Cargo.toml"})
        with mock.patch.object(pr_ready.subprocess, "run", return_value=mock.Mock(stdout=json.dumps(metadata))):
            directories, libraries, dependencies = pr_ready.packages()
        self.assertEqual(set(directories), {"core", "optional", "build", "dev"})
        self.assertEqual(libraries, {"core"})
        self.assertEqual(pr_ready.dependent_crates(["core"], dependencies), ["build", "core", "dev", "optional"])

    def test_scope_warns_on_size_and_mixed_areas(self):
        self.assertEqual(pr_ready.scope_warnings({"crates/apex-client/src/game.rs", "tools/test_food_parity.py",
                                                  "mods/apex/src/test/java/dev/apexlab/parity/X.java",
                                                  "docs/native-client.md"}, 120), [])
        self.assertEqual(pr_ready.scope_warnings({"crates/apex-theme/src/lib.rs", "launcher/src/theme.rs"}, 10), [])
        warnings = pr_ready.scope_warnings({"crates/apex-client/src/game.rs", "launcher/src/main.rs",
                                            ".github/workflows/ci.yml"}, 900)
        self.assertEqual(len(warnings), 2)
        self.assertIn("900 lines of code: over 500", warnings[0])
        self.assertEqual(warnings[1], "mixes CI, game, launcher")

    def test_documentation_and_tests_are_not_counted_in_the_size(self):
        self.assertTrue(pr_ready.reviewed("tools/pr_ready.py"))
        self.assertTrue(pr_ready.reviewed("crates/apex-client/src/game.rs"))
        self.assertFalse(pr_ready.reviewed("CONTRIBUTING.md"))
        self.assertFalse(pr_ready.reviewed("tests/test_pr_ready.py"))
        self.assertFalse(pr_ready.reviewed("tools/test_food_parity.py"))
        self.assertFalse(pr_ready.reviewed("crates/apex-core/tests/jmath.rs"))

    def test_cargo_lock_changes_only_with_a_manifest(self):
        self.assertIsNone(pr_ready.lock_problem({"crates/apex-core/src/lib.rs"}))
        self.assertIsNone(pr_ready.lock_problem({"Cargo.lock", "crates/apex-client/Cargo.toml"}))
        self.assertIsNone(pr_ready.lock_problem({"launcher/Cargo.lock", "crates/apex-theme/Cargo.toml"}))
        self.assertIn("Cargo.lock", pr_ready.lock_problem({"Cargo.lock", "crates/apex-core/src/lib.rs"}))

    def test_label_follows_what_players_get(self):
        self.assertEqual(pr_ready.suggested_label({"tools/pr_ready.py", "CONTRIBUTING.md"}), "`skip-release`")
        self.assertEqual(pr_ready.suggested_label({"crates/apex-world/examples/probe.rs"}), "`skip-release`")
        self.assertIn("feature", pr_ready.suggested_label({"crates/apex-client/src/game.rs"}))
        self.assertIn("feature", pr_ready.suggested_label({"launcher/src/main.rs"}))

    def test_affected_harnesses_come_from_the_parity_runner(self):
        found = {"food": "tools/test_food_parity.py", "datafix#1": "tools/test_datafix_parity.py",
                 "datafix#2": "tools/test_datafix_parity.py"}
        with mock.patch.object(pr_ready.parity, "harnesses", return_value=found), \
                mock.patch.object(pr_ready.parity, "load_state", return_value={"harnesses": {
                    "food": {"dependencies": ["crates/apex-world/src/food.rs"]},
                    "datafix#1": {"dependencies": ["crates/apex-world/src/datafix.rs"]},
                    "datafix#2": {"dependencies": ["crates/apex-world/src/datafix.rs"]}}}), \
                mock.patch.object(pr_ready.parity, "ROOT", pr_ready.parity.Path(".")):
            self.assertEqual(pr_ready.affected_here({"crates/apex-world/src/datafix.rs"}), ["datafix"])
            self.assertEqual(pr_ready.affected_here({"README.md"}), [])
            self.assertEqual(pr_ready.affected_here({"Cargo.lock"}), ["food", "datafix"])

    def test_harnesses_are_listed_when_they_cannot_run(self):
        changed = {"crates/apex-world/src/food.rs"}
        with mock.patch.object(pr_ready, "affected_here", return_value=["food", "light"]):
            steps = pr_ready.plan(args(quick=True), "origin/main", changed, {"apex-world": "crates/apex-world"}, {"apex-world"}, {})
        harness = steps[-1]
        self.assertEqual(harness.status, "list")
        self.assertIn("2 affected, to run in CI (--quick): food, light", harness.detail)
        by_name = {step.name: step for step in steps}
        self.assertIn("tests: apex-world", by_name)
        self.assertEqual(by_name["launcher clippy"].status, "skip")
        self.assertIsNone(by_name["clippy"].status)
        with mock.patch.object(pr_ready, "affected_here", return_value=["food"]):
            steps = pr_ready.plan(args(host="macmini"), "origin/main", changed, {"apex-world": "crates/apex-world"}, {"apex-world"}, {})
        self.assertIn("--changed-files", steps[-1].command)
        self.assertIn("crates/apex-world/src/food.rs", steps[-1].command)

    def test_ci_s_rust_follows_the_six_week_train(self):
        self.assertEqual(pr_ready.ci_rust(datetime.date(2025, 2, 20)), 85)
        self.assertEqual(pr_ready.ci_rust(datetime.date(2025, 6, 26)), 88)
        self.assertEqual(pr_ready.ci_rust(datetime.date(2026, 10, 31)), 99)
        self.assertEqual(pr_ready.ci_rust(datetime.date(2026, 11, 12)), 100)

    def test_an_older_rust_warns_without_failing(self):
        today = datetime.date(2026, 10, 31)
        self.assertIsNone(pr_ready.old_rust((1, 99, 1), today))
        self.assertIsNone(pr_ready.old_rust(None, today))
        warning = pr_ready.old_rust((1, 97, 0), today)
        self.assertIn("1.97.0 is older than CI's stable (1.99)", warning)
        self.assertIn("`rustup update`", warning)
        steps = pr_ready.plan(args(quick=True), "origin/main", {"crates/apex-core/src/jmath.rs"}, PACKAGES, LIBRARIES,
                              DEPENDENCIES)
        by_name = {step.name: step for step in steps}
        by_name["clippy"].status, by_name["clippy"].detail = "fail", "failed"
        pr_ready.mark_old_rust(steps, warning)
        names = [step.name for step in steps]
        self.assertEqual(names.index("Rust") + 1, names.index("clippy"))
        self.assertEqual(steps[names.index("Rust")].status, "warn")
        self.assertEqual(by_name["clippy"].detail, "failed; likely the old Rust above")
        steps = pr_ready.plan(args(quick=True), "origin/main", {"README.md"}, PACKAGES, LIBRARIES, DEPENDENCIES)
        pr_ready.mark_old_rust(steps, warning)
        self.assertNotIn("Rust", [step.name for step in steps])

    def test_summaries_of_check_output(self):
        output = "test result: ok. 3 passed; 0 failed;\ntest result: FAILED. 4 passed; 1 failed;\n"
        self.assertEqual(pr_ready.tests_passed(output), "7 passed, 1 failed")
        self.assertEqual(pr_ready.unittest_passed("....\nRan 12 tests in 1.0s\n\nOK\n"), "12 passed")
        self.assertEqual(pr_ready.unittest_passed("Ran 12 tests in 1.0s\n\nFAILED (failures=2)\n"),
                         "12 run, FAILED (failures=2)")
        parity_output = ("3 files changed: 2 harnesses depend on them, 2 without a pass for their current inputs.\n"
                         "\n1 passed, 1 failed in 2.0 min.\n  light: /x/.local/parity-runner/logs/light.log\n")
        self.assertEqual(pr_ready.parity_summary(parity_output), "2 affected, 1 passed, failed: light")
        self.assertEqual(pr_ready.parity_summary("2 files changed: 0 harnesses depend on them, 0 without a pass for "
                                                 "their current inputs.\nNothing to run: every harness passed."),
                         "no harness affected")
        self.assertEqual(pr_ready.duration(125), "2 min 5 s")


if __name__ == "__main__":
    unittest.main()
