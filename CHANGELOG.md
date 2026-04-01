# CHANGELOG

## v0.5.0 (2026-04-01)

### Chore

* chore: expand gitignore to cover build artifacts and additional IDEs

Co-Authored-By: Claude Sonnet 4.6 &lt;noreply@anthropic.com&gt; ([`0dd5256`](https://github.com/UCSD-E4E/e4e-data-management/commit/0dd52564092a7574105f60be8684d22f3887994c))

### Feature

* feat: support txt and pdf readmes ([`cad2873`](https://github.com/UCSD-E4E/e4e-data-management/commit/cad2873b95448b0881ce78b7ec4fac10eb7cb3ce))

* feat: progress bars ([`a7de0f7`](https://github.com/UCSD-E4E/e4e-data-management/commit/a7de0f7600f29d65d8ce823620c33e69727fc3dd))

* feat: use progress bar ([`9bdd722`](https://github.com/UCSD-E4E/e4e-data-management/commit/9bdd722f0ce089ca7afd804e458a4eaedacf0646))

* feat: can create dataset, mission, files ([`a67c822`](https://github.com/UCSD-E4E/e4e-data-management/commit/a67c82234b7a0eb308f9eeb3de445b9bd4c91c20))

* feat: initial UI system ([`b2ad629`](https://github.com/UCSD-E4E/e4e-data-management/commit/b2ad62963de1c31bf2e39b0b307de7d9f59b66ab))

### Fix

* fix: codeql python ([`98ede65`](https://github.com/UCSD-E4E/e4e-data-management/commit/98ede65e3fccf85cf51fdb3a35c3a7cb465aadfb))

* fix: codeql ([`029d692`](https://github.com/UCSD-E4E/e4e-data-management/commit/029d692e34b6e286f4e9dfeb66bd2c80ed1ad1ad))

* fix: pylint issues ([`c6521fe`](https://github.com/UCSD-E4E/e4e-data-management/commit/c6521feec7ff448e11b111e9fe3e2ad598c97e44))

* fix: failed dotnet test on github actions ([`6166f62`](https://github.com/UCSD-E4E/e4e-data-management/commit/6166f62fe0e78c5c5c5dde0141dfe71c07ac4f60))

* fix: pylint, pytest, dotnet build, dotnet test, and add additional test cases ([`6e5f0b1`](https://github.com/UCSD-E4E/e4e-data-management/commit/6e5f0b148ec709e7160111a09e722f2db300a3f3))

* fix: cargo build errors ([`c0094cb`](https://github.com/UCSD-E4E/e4e-data-management/commit/c0094cbf26d311538a63ed086dede73f81d01200))

### Unknown

* Merge pull request #120 from UCSD-E4E/feature/ui

Feature/UI ([`56ff611`](https://github.com/UCSD-E4E/e4e-data-management/commit/56ff6116a0d16b70178ec80bfaac3300588f1239))

## v0.4.1 (2026-03-28)

### Fix

* fix: support python 3.14 ([`6cad379`](https://github.com/UCSD-E4E/e4e-data-management/commit/6cad379f8ee2cf81e5a892d6d02d39f714543901))

* fix: suppress pylint R0904 too-many-public-methods on DataManager

Agent-Logs-Url: https://github.com/UCSD-E4E/e4e-data-management/sessions/dba4a1e9-344a-4780-ac99-f3fc27bd5861

Co-authored-by: ccrutchf &lt;25113015+ccrutchf@users.noreply.github.com&gt; ([`f6c4e2b`](https://github.com/UCSD-E4E/e4e-data-management/commit/f6c4e2b06a88d55b8efd599139304f1188376fa7))

* fix: upgrade PyO3 to 0.23 to support Python 3.14

- Update pyo3 from 0.22 to 0.23 in Cargo.toml
- Update Cargo.lock (pyo3 0.22.6 -&gt; 0.23.5)
- Remove gil-refs lint workaround that was specific to pyo3 0.22
- Fix deprecated API calls: new_bound -&gt; new, get_type_bound -&gt; get_type

Agent-Logs-Url: https://github.com/UCSD-E4E/e4e-data-management/sessions/2cff3a6a-a487-47b5-bdb5-fb8b58ca7b0b

Co-authored-by: ccrutchf &lt;25113015+ccrutchf@users.noreply.github.com&gt; ([`9cb3ed5`](https://github.com/UCSD-E4E/e4e-data-management/commit/9cb3ed55d9db42a506bd0e25ee6bc29f29121237))

### Unknown

* Merge pull request #115 from UCSD-E4E/copilot/fix-pylint-errors

Fix pylint R0904: too-many-public-methods on DataManager ([`8b3a001`](https://github.com/UCSD-E4E/e4e-data-management/commit/8b3a0013c1d391fcd7b6951ea7f2cea7c9b27bea))

* Initial plan ([`78184f3`](https://github.com/UCSD-E4E/e4e-data-management/commit/78184f35bc688569d5aa1091d255bbfa1f2601f0))

* Merge pull request #117 from UCSD-E4E/copilot/fix-pipx-install-errors

fix: upgrade PyO3 to 0.23 to support Python 3.14 ([`afe0be2`](https://github.com/UCSD-E4E/e4e-data-management/commit/afe0be21f2d75420bc72a7c691c3c4adb10e6b01))

* Initial plan ([`f96b853`](https://github.com/UCSD-E4E/e4e-data-management/commit/f96b853b7ccdb5d2f38ae84bb1b6349ebb3ecf1d))

## v0.4.0 (2026-03-28)

### Chore

* chore: pylint ([`9747661`](https://github.com/UCSD-E4E/e4e-data-management/commit/9747661bd69329a41ff5f92b6577f7c81a6c82bb))

* chore: rust lint ([`affc955`](https://github.com/UCSD-E4E/e4e-data-management/commit/affc955e5d5fb86754e62ab4e21a7bc078f71152))

### Feature

* feat: fully functional e4edm using rust ([`895cbab`](https://github.com/UCSD-E4E/e4e-data-management/commit/895cbabce85dc4a14ac7b10cf844c63b515dcf0a))

* feat: update command structure ([`3e3a212`](https://github.com/UCSD-E4E/e4e-data-management/commit/3e3a212a19e951aa02c8f41eec25e67d35759b06))

* feat: performance improvements ([`db3c070`](https://github.com/UCSD-E4E/e4e-data-management/commit/db3c070df0ce4930f3803de5263af6f7b8bdaeb1))

* feat: port to rust ([`f9d7160`](https://github.com/UCSD-E4E/e4e-data-management/commit/f9d71604118497d7f71f8504361f36cec8c6feee))

### Fix

* fix: address review feedback - shared utils, Incomplete base class, dir copy verification, release workflow outputs

Co-authored-by: ccrutchf &lt;25113015+ccrutchf@users.noreply.github.com&gt;
Agent-Logs-Url: https://github.com/UCSD-E4E/e4e-data-management/sessions/fab26efe-bc66-4640-80a8-8b9fb1e588f4 ([`9a700f2`](https://github.com/UCSD-E4E/e4e-data-management/commit/9a700f2a7fabdf3548918f596b411629dd67d4c5))

* fix: remove dependency on macos-13 ([`f6d5108`](https://github.com/UCSD-E4E/e4e-data-management/commit/f6d510818eeb9ef2ae265fb90c5005fe506ba2c0))

### Unknown

* Merge pull request #108 from UCSD-E4E/feature/rust

feat: port to rust ([`9ca5e1e`](https://github.com/UCSD-E4E/e4e-data-management/commit/9ca5e1e35e3be192e9f7bb45035df05fd75f42d1))

* Merge pull request #109 from UCSD-E4E/copilot/sub-pr-108

fix: address review feedback on Rust port ([`6108496`](https://github.com/UCSD-E4E/e4e-data-management/commit/61084969ac95fcc4978920f2f3599f92ad21e410))

* Initial plan ([`89e957f`](https://github.com/UCSD-E4E/e4e-data-management/commit/89e957fc79b8d8933301aea1aaf5a4acf64887e9))

* Potential fix for code scanning alert no. 3: Workflow does not contain permissions

Co-authored-by: Copilot Autofix powered by AI &lt;62310815+github-advanced-security[bot]@users.noreply.github.com&gt; ([`7fb7848`](https://github.com/UCSD-E4E/e4e-data-management/commit/7fb78486e5f8bb8727830189eebdd8dfa498ae62))

* Potential fix for code scanning alert no. 5: Workflow does not contain permissions

Co-authored-by: Copilot Autofix powered by AI &lt;62310815+github-advanced-security[bot]@users.noreply.github.com&gt; ([`e420881`](https://github.com/UCSD-E4E/e4e-data-management/commit/e420881a7642bf70ab721ef99e27a91386a179f3))

## v0.3.1 (2025-06-16)

### Fix

* fix: resolve pylint errors ([`309fb4d`](https://github.com/UCSD-E4E/e4e-data-management/commit/309fb4d0175228e03bda3a13494e4b71d8bcf44b))

## v0.3.0 (2025-06-16)

### Feature

* feat: introduce &#39;e4edm reset&#39; ([`f2cfdfd`](https://github.com/UCSD-E4E/e4e-data-management/commit/f2cfdfd0cc9808308e9aa5572c6cb14510b26c6e))

## v0.2.1 (2025-03-02)

### Chore

* chore: Re-adds project ignores ([`2fd4521`](https://github.com/UCSD-E4E/e4e-data-management/commit/2fd452195babbafaf013e71e0ef371225053d04c))

* chore: Updates gitignore ([`17713a8`](https://github.com/UCSD-E4E/e4e-data-management/commit/17713a8e9060e71cc8aae0af156aa9431ca62272))

* chore(deps-dev): bump jinja2 from 3.1.4 to 3.1.5

Bumps [jinja2](https://github.com/pallets/jinja) from 3.1.4 to 3.1.5.
- [Release notes](https://github.com/pallets/jinja/releases)
- [Changelog](https://github.com/pallets/jinja/blob/main/CHANGES.rst)
- [Commits](https://github.com/pallets/jinja/compare/3.1.4...3.1.5)

---
updated-dependencies:
- dependency-name: jinja2
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt; ([`373c3ff`](https://github.com/UCSD-E4E/e4e-data-management/commit/373c3ffa4dd543e79107c3f17d77473d00143dfc))

### Fix

* fix: Adds wakepy ([`e4a9e6f`](https://github.com/UCSD-E4E/e4e-data-management/commit/e4a9e6f4fbc02ea6a3b773c0cc4fbc5c90f0a2ce))

* fix: Adds sleep hold ([`3c7f73e`](https://github.com/UCSD-E4E/e4e-data-management/commit/3c7f73ee6ec79e4d7230207b5a40357c41b5ce68))

### Unknown

* Merge pull request #81 from UCSD-E4E/45-sleep-hold

fix: Adds sleep hold ([`2e89bb0`](https://github.com/UCSD-E4E/e4e-data-management/commit/2e89bb05dd9ae1e062cc32c7f4d31b52a7a731e0))

* Merge branch &#39;main&#39; into 45-sleep-hold ([`ae70041`](https://github.com/UCSD-E4E/e4e-data-management/commit/ae700415e8cb900a449b6b53db33053edb10f971))

* Merge branch &#39;main&#39; into 45-sleep-hold ([`320a6f6`](https://github.com/UCSD-E4E/e4e-data-management/commit/320a6f6afc0daffc39e43ed1199b3891123e5ce0))

* Merge branch &#39;main&#39; into 45-sleep-hold ([`8c8c867`](https://github.com/UCSD-E4E/e4e-data-management/commit/8c8c867312bf846a8e52694ff58c68acea16f885))

* Merge branch &#39;main&#39; into 45-sleep-hold ([`528c0ee`](https://github.com/UCSD-E4E/e4e-data-management/commit/528c0ee95a4e136939db42480f59a78bcba8395e))

* Merge pull request #101 from UCSD-E4E/58-bug-missing-ds_store

chore: Updates gitignore ([`7cb945e`](https://github.com/UCSD-E4E/e4e-data-management/commit/7cb945e008a4c5d1be7b5e26c2496a39714ee1a2))

* Merge pull request #94 from UCSD-E4E/dependabot/pip/jinja2-3.1.5

chore(deps-dev): bump jinja2 from 3.1.4 to 3.1.5 ([`c0664fe`](https://github.com/UCSD-E4E/e4e-data-management/commit/c0664fe2bdf4f5620c43683cc7745e9fa7346f29))

* Merge branch &#39;main&#39; into dependabot/pip/jinja2-3.1.5 ([`7dbe840`](https://github.com/UCSD-E4E/e4e-data-management/commit/7dbe840bb87d11c0a4efbdc96fe35000c7287962))

## v0.2.0 (2025-01-11)

### Chore

* chore: Fixes naming ([`268b2e0`](https://github.com/UCSD-E4E/e4e-data-management/commit/268b2e0b2b2a7261e18299b994374071e2809646))

### Feature

* feat: Adds zip ([`9288cc0`](https://github.com/UCSD-E4E/e4e-data-management/commit/9288cc0ba0b1ec1cd72500613b3e53c4f362488a))

### Style

* style: Fixes styling ([`15ff087`](https://github.com/UCSD-E4E/e4e-data-management/commit/15ff08730c9f7c7e33f447a04db0b94f647cbecf))

* style: Fixes spaces and unused variables ([`7d942a3`](https://github.com/UCSD-E4E/e4e-data-management/commit/7d942a32f659ec2e9860e719b313b56591b97eb2))

### Unknown

* Merge pull request #92 from UCSD-E4E/37-zip-command

37 zip command ([`6facd63`](https://github.com/UCSD-E4E/e4e-data-management/commit/6facd6366f6235894d13e8e243cbff120dc1e0cc))

* Merge branch &#39;main&#39; into 37-zip-command ([`91cbb7f`](https://github.com/UCSD-E4E/e4e-data-management/commit/91cbb7f3ff20f95e0daf733ce2d861652c3904fb))

* Merge branch &#39;main&#39; into 37-zip-command ([`bab9f25`](https://github.com/UCSD-E4E/e4e-data-management/commit/bab9f25c9c2152ec1efbc47b7c6e9c87b7278409))

* Merge branch &#39;34-remove-dataset-after-pushing-to-server&#39; into 37-zip-command ([`3a9b85d`](https://github.com/UCSD-E4E/e4e-data-management/commit/3a9b85dededb8742d641d0383af9a2bc03c75188))

* Merge branch &#39;main&#39; into 37-zip-command ([`e6a278d`](https://github.com/UCSD-E4E/e4e-data-management/commit/e6a278dad6c828765e1dae42b0330efba37d2585))

* wip: Creates zip file ([`e6fcd44`](https://github.com/UCSD-E4E/e4e-data-management/commit/e6fcd444641e0578ab1c1cf3d94244454b77932a))

* Merge pull request #47 from UCSD-E4E/42-implement-e4edm-validate

42 implement e4edm validate ([`be17c5f`](https://github.com/UCSD-E4E/e4e-data-management/commit/be17c5ff5856f426e93070de30bfce25fa36279e))

* Merge branch &#39;main&#39; into 42-implement-e4edm-validate ([`c2d84e5`](https://github.com/UCSD-E4E/e4e-data-management/commit/c2d84e55a3ca78067ba47edbe2a76feb8f7852de))

* Merge pull request #83 from UCSD-E4E/60-chore-datamangercli-vs-datamanagercli

chore: Fixes naming ([`d9ec1ad`](https://github.com/UCSD-E4E/e4e-data-management/commit/d9ec1add43008ca78b45f636982961905577e000))

* Merge branch &#39;main&#39; into 60-chore-datamangercli-vs-datamanagercli ([`a3f7234`](https://github.com/UCSD-E4E/e4e-data-management/commit/a3f72345d01efefce05560c4c9aaa0420c599d29))

* Merge branch &#39;main&#39; into 60-chore-datamangercli-vs-datamanagercli ([`eb6b329`](https://github.com/UCSD-E4E/e4e-data-management/commit/eb6b329850f32d0336ba3fdb6c91d2677e67f41a))

* Merge remote-tracking branch &#39;origin/main&#39; into 42-implement-e4edm-validate ([`5cb4f3c`](https://github.com/UCSD-E4E/e4e-data-management/commit/5cb4f3ca6437324800d59293b1f367f3a183a7cc))

## v0.1.5 (2025-01-11)

### Ci

* ci: Tests for prune behavior ([`d461c57`](https://github.com/UCSD-E4E/e4e-data-management/commit/d461c574868ccf0a2b0f9cc50dd765f2c6f854e8))

* ci: Fixes failing tests ([`77fee0d`](https://github.com/UCSD-E4E/e4e-data-management/commit/77fee0d6c99cbee9c2c3d3a8ca1d03284647afb7))

### Documentation

* docs: Documents fixture ([`edb3b97`](https://github.com/UCSD-E4E/e4e-data-management/commit/edb3b97e127468c7a53d27b3dbba2b09b76073ac))

### Fix

* fix: Adds exception logging to main invocation ([`ad75df3`](https://github.com/UCSD-E4E/e4e-data-management/commit/ad75df32089ad859cf938c980666392a094221a6))

### Style

* style: Fixes long line ([`fcb6058`](https://github.com/UCSD-E4E/e4e-data-management/commit/fcb6058a81c6db64b19b49650a545ab052fd1ab6))

### Unknown

* Merge pull request #57 from UCSD-E4E/44-add-exception-and-traceback-to-logs

fix: Adds exception logging to main invocation ([`f3d3675`](https://github.com/UCSD-E4E/e4e-data-management/commit/f3d367537a0e29ecca89e80725e11671aae8088f))

* Merge branch &#39;main&#39; into 44-add-exception-and-traceback-to-logs ([`589f02c`](https://github.com/UCSD-E4E/e4e-data-management/commit/589f02c60a83ba4d4a945612e66217cd01b9279e))

* Merge pull request #91 from UCSD-E4E/34-remove-dataset-after-pushing-to-server

34 remove dataset after pushing to server ([`88b8515`](https://github.com/UCSD-E4E/e4e-data-management/commit/88b85159f6d5da2af433484ce5e12da04b0bb4bb))

* Merge branch &#39;main&#39; into 42-implement-e4edm-validate ([`6492ffc`](https://github.com/UCSD-E4E/e4e-data-management/commit/6492ffc1ec67fb4007bc4ac230b644c2d709b0f6))

## v0.1.4 (2024-11-04)

### Fix

* fix: Fixes readme extension heuristic ([`ca50532`](https://github.com/UCSD-E4E/e4e-data-management/commit/ca505329f23f49c62b3d4259fcbe5fc10d8c62a3))

## v0.1.3 (2024-10-09)

### Unknown

* Merge branch &#39;main&#39; of github.com:UCSD-E4E/e4e-data-management ([`1a608cc`](https://github.com/UCSD-E4E/e4e-data-management/commit/1a608cc289d4a387b65edc93c44fd7bcbdcd2a10))

## v0.1.2 (2024-10-09)

### Fix

* fix: updates list datasets to display push flag ([`d01ea63`](https://github.com/UCSD-E4E/e4e-data-management/commit/d01ea6322bfeea0bbf1be9f5347f8077dad265a8))

* fix: Fixes push not setting flag ([`6d794b4`](https://github.com/UCSD-E4E/e4e-data-management/commit/6d794b4ae063a8adc862e51a4782ac86d6a9a488))

* fix: Fixes prune fail on deleted datasets ([`7c88541`](https://github.com/UCSD-E4E/e4e-data-management/commit/7c88541efd4e750d453852a62c9fe8dea3690b9c))

## v0.1.1 (2024-10-08)

### Documentation

* docs: Updates README ([`c0404ce`](https://github.com/UCSD-E4E/e4e-data-management/commit/c0404cec990c9ea5ca2b924dd5dca08040f74297))

### Fix

* fix: Updates prune to actually remove old data ([`b09cea7`](https://github.com/UCSD-E4E/e4e-data-management/commit/b09cea7ebdf03642c7f9a6043807bd313b94d577))

### Style

* style: Fixes style ([`fb500bd`](https://github.com/UCSD-E4E/e4e-data-management/commit/fb500bdcf8bbd9c569d950e0e3e53c8eda13e3eb))

## v0.1.0 (2024-09-23)

### Ci

* ci: Fixes validation on macos ([`872de04`](https://github.com/UCSD-E4E/e4e-data-management/commit/872de04c0fd6bd82ea848d3b6153c4bd9eb07c9e))

* ci: Switches to os ([`8d924d5`](https://github.com/UCSD-E4E/e4e-data-management/commit/8d924d5db1f303be7a81c095ef3346702ed13f69))

* ci: pytest only run under latest python ([`297789b`](https://github.com/UCSD-E4E/e4e-data-management/commit/297789bb032671c8bf80b4e56d4276a7da7e1c6e))

* ci: Upgrades workflows ([`1fd4b89`](https://github.com/UCSD-E4E/e4e-data-management/commit/1fd4b89352c7c5fd47443d1fbd1686182ac33ad9))

### Feature

* feat: Adds e4edm ls ([`8dbc1c3`](https://github.com/UCSD-E4E/e4e-data-management/commit/8dbc1c350d7b50589a238c782ce949fecff90a86))

### Fix

* fix: Makes time comparison logic neater ([`efd3e07`](https://github.com/UCSD-E4E/e4e-data-management/commit/efd3e075226149dbaa5b52bf2aa91f7c4f296f08))

### Unknown

* Merge branch &#39;workflow_upgrade&#39; ([`69060d3`](https://github.com/UCSD-E4E/e4e-data-management/commit/69060d3cfa0cb3cfac26451cb62f0acc87ccd371))

* Merge pull request #89 from UCSD-E4E/workflow_upgrade

ci: Upgrades workflows ([`5a3b1f9`](https://github.com/UCSD-E4E/e4e-data-management/commit/5a3b1f94acc01f581e23e7186c4c55b34e052978))

## v0.0.1 (2024-08-22)

### Chore

* chore: Removes old setup.py ([`07fa655`](https://github.com/UCSD-E4E/e4e-data-management/commit/07fa655bdf18ed5e480a84d8e78f6d956ba8c897))

* chore: Adds poetry support ([`d8141bd`](https://github.com/UCSD-E4E/e4e-data-management/commit/d8141bd68f6e6231c205f8ae6ae936fbfc7f7ad5))

### Ci

* ci: Switches back to releaser token ([`97c439e`](https://github.com/UCSD-E4E/e4e-data-management/commit/97c439ed89ec27f549121b36b8b32efaa68b58a4))

* ci: Switches to deploy key ([`7f4bb72`](https://github.com/UCSD-E4E/e4e-data-management/commit/7f4bb729bd5077d9b323884f6c3ddec48e34e941))

* ci: Adds -vv ([`b8dd838`](https://github.com/UCSD-E4E/e4e-data-management/commit/b8dd838798531124c3763277537c1184f21c49a1))

* ci: Fixes checkout ([`4501cf9`](https://github.com/UCSD-E4E/e4e-data-management/commit/4501cf9750435555550ee2123efae5c98906f5e1))

* ci: Fix persist-credentials ([`39fccf7`](https://github.com/UCSD-E4E/e4e-data-management/commit/39fccf783d83a3ca3d03de07f1b012ea62e52dfc))

* ci: Fixes checkout token ([`3dff30c`](https://github.com/UCSD-E4E/e4e-data-management/commit/3dff30c7d405ccf616b36e33642e9fe86ec4835f))

* ci: Fixes release token ([`e5b3181`](https://github.com/UCSD-E4E/e4e-data-management/commit/e5b3181ec58407f5c01a64076432abce1cb41402))

* ci: Fixes tests ([`2e19877`](https://github.com/UCSD-E4E/e4e-data-management/commit/2e198772bd6bbf2099912374e4120c7630bd8446))

* ci: Updates python versions ([`a549d33`](https://github.com/UCSD-E4E/e4e-data-management/commit/a549d3330ae742a327093e2abe43b74f05ee1f59))

### Fix

* fix: Raises error when commiting non-regular file ([`d26ad44`](https://github.com/UCSD-E4E/e4e-data-management/commit/d26ad4454c6378dd8f3a1839c284dbc993bbe3b2))

### Unknown

* Merge pull request #88 from UCSD-E4E/poetry

chore: Adds poetry support ([`62f0ae3`](https://github.com/UCSD-E4E/e4e-data-management/commit/62f0ae320810ccaf275c7e5aa899e99029ba80f4))

* Merge pull request #86 from UCSD-E4E/56-activate-save-state

Added self.save() call to dataset activation ([`9afcd74`](https://github.com/UCSD-E4E/e4e-data-management/commit/9afcd7410ec9cacc77e297c8da295bdd0125bf09))

* added save ([`9f12db8`](https://github.com/UCSD-E4E/e4e-data-management/commit/9f12db8e22a34a0ea76fbb10bd6990e70dbc2909))

* Update version ([`bd4c237`](https://github.com/UCSD-E4E/e4e-data-management/commit/bd4c2371c35002ae7b9ea1cf059969336c800d25))

* Merge remote-tracking branch &#39;origin/main&#39; into 42-implement-e4edm-validate ([`cfb4275`](https://github.com/UCSD-E4E/e4e-data-management/commit/cfb42756ec8317ce87ce759fb914fa2992fd0c22))

* Merge pull request #46 from UCSD-E4E/43-include-full-date-in-dataset

43 include full date in dataset ([`33e1998`](https://github.com/UCSD-E4E/e4e-data-management/commit/33e199837b9c1ccc6796b70e5ba04cde57d27740))

* Fixed linting - line too long ([`6a38881`](https://github.com/UCSD-E4E/e4e-data-management/commit/6a38881b0196ca34152c77e4ea63836c3965c8f1))

* Updated version ([`e1ae05d`](https://github.com/UCSD-E4E/e4e-data-management/commit/e1ae05da59eccc2673ba0f0896933390b7b8704b))

* Updated logic ([`a5f1c7f`](https://github.com/UCSD-E4E/e4e-data-management/commit/a5f1c7f3b4c61499e5c839337cacf9c6b2e4c964))

* Updated documentation ([`131ac51`](https://github.com/UCSD-E4E/e4e-data-management/commit/131ac51b3dc9f7d0140f52ee29bac84a7ccf2c55))

* Updated Tests ([`a408047`](https://github.com/UCSD-E4E/e4e-data-management/commit/a40804726e98e4b28d803cf2a26e3c0d82e8ca0a))

* Added remaining logic ([`131a461`](https://github.com/UCSD-E4E/e4e-data-management/commit/131a461926d265b46f8536ce39acfa4ecd3a795d))

* Adding command changes ([`c9e8619`](https://github.com/UCSD-E4E/e4e-data-management/commit/c9e86190f2b55d49affb86377813a3db68ef4012))

* Merge pull request #36 from UCSD-E4E/34-remove-dataset-after-pushing-to-server

34 remove dataset after pushing to server ([`69fadf7`](https://github.com/UCSD-E4E/e4e-data-management/commit/69fadf7d1f0f9c6b87b6470c8d30c921aa0a3e1e))

* Merge branch &#39;main&#39; into 34-remove-dataset-after-pushing-to-server ([`11a303a`](https://github.com/UCSD-E4E/e4e-data-management/commit/11a303a1e0f36f5f6cd7e94f20d5d29314353ca9))

* Merge pull request #32 from UCSD-E4E/31-logging

Added invocation logging ([`33e4f07`](https://github.com/UCSD-E4E/e4e-data-management/commit/33e4f07b66df81283eadc0e5918cfc5f2f9818ad))

* Fixed pylint ([`e3cce1d`](https://github.com/UCSD-E4E/e4e-data-management/commit/e3cce1d6d5d75cc2a514321a071e013feab419b7))

* Added stage and commit log messages ([`de5276a`](https://github.com/UCSD-E4E/e4e-data-management/commit/de5276a13eb97ff9a164da8d345d302290c68358))

* Adding version ([`17c5aa6`](https://github.com/UCSD-E4E/e4e-data-management/commit/17c5aa61ce3223608b312230fc0e15d9b2a81168))

* Added saving and upgrading log statements ([`f8f7d5c`](https://github.com/UCSD-E4E/e4e-data-management/commit/f8f7d5c711e66b13175ba809b63622837f8edfe7))

* Added invocation logging ([`72e0f8e`](https://github.com/UCSD-E4E/e4e-data-management/commit/72e0f8e0e5ab0979135fbbe0f3bfee7acec0287c))

* Organized imports ([`89eacd2`](https://github.com/UCSD-E4E/e4e-data-management/commit/89eacd2003cb78cea106beec88c8afa67fdc5dbf))

* Added push/prune logic ([`872f390`](https://github.com/UCSD-E4E/e4e-data-management/commit/872f390ec0183f071f1dd38bb8d1845323cc1d4c))

* Added readme ([`6ebc40a`](https://github.com/UCSD-E4E/e4e-data-management/commit/6ebc40a6c62a8a0927d7d83d8b8a75a362d864b8))

* Added push and prune logic ([`c216d12`](https://github.com/UCSD-E4E/e4e-data-management/commit/c216d127de04ccc3b5b7ae1677dfe5775299f17e))

* Added pushed flag ([`3dc8d24`](https://github.com/UCSD-E4E/e4e-data-management/commit/3dc8d2429ca22559a11feccfff01bef163de38bb))

* Added test ([`78279ee`](https://github.com/UCSD-E4E/e4e-data-management/commit/78279ee2ef65e795d6059877ca59931e37bb9933))

* Merge pull request #30 from UCSD-E4E/26-add-timezone-aware-timestamps

26 add timezone aware timestamps ([`132420a`](https://github.com/UCSD-E4E/e4e-data-management/commit/132420a957855dd1e6c4e5408dd39147798b219e))

* Added pragma justification ([`6ca6d75`](https://github.com/UCSD-E4E/e4e-data-management/commit/6ca6d75821fcaeefdfb2a73e4dbd1d21fd57f146))

* Merge branch &#39;main&#39; into 26-add-timezone-aware-timestamps ([`fc6b0cd`](https://github.com/UCSD-E4E/e4e-data-management/commit/fc6b0cd42b85e8ba668e1344a42f5697fa1ba707))

* Merge pull request #29 from UCSD-E4E/25-as-a-user-i-would-like-e4edm-push-to-include-the-dataset-directory-so-that-i-do-not-lose-the-dataset-context

25 as a user i would like e4edm push to include the dataset directory so that i do not lose the dataset context ([`b678578`](https://github.com/UCSD-E4E/e4e-data-management/commit/b678578122f7d9056a64c9e8754cde02ad275f8c))

* Merge remote-tracking branch &#39;origin/main&#39; into 25-as-a-user-i-would-like-e4edm-push-to-include-the-dataset-directory-so-that-i-do-not-lose-the-dataset-context ([`b4b7a3c`](https://github.com/UCSD-E4E/e4e-data-management/commit/b4b7a3c4bfb8a08d27042866dc1150d53252eb40))

* Merge pull request #24 from UCSD-E4E/23-e4edm-results-in-error-thrown

23 e4edm results in error thrown ([`3319f95`](https://github.com/UCSD-E4E/e4e-data-management/commit/3319f95f37b9b9f7a5722f9fad090699238ccc12))

* Merge remote-tracking branch &#39;origin/main&#39; into 23-e4edm-results-in-error-thrown ([`e6702ec`](https://github.com/UCSD-E4E/e4e-data-management/commit/e6702ecfc79f02b15e37d8ce3e6184e0cfadfa75))

* Merge pull request #28 from UCSD-E4E/22-readme-does-not-appear-in-staging-list-when-added-with-readme-flag

22 readme does not appear in staging list when added with readme flag ([`b4a8de8`](https://github.com/UCSD-E4E/e4e-data-management/commit/b4a8de84609ac9fcefd59ddff60171231b5ccca7))

* Resolving and escaping paths ([`a30354d`](https://github.com/UCSD-E4E/e4e-data-management/commit/a30354ddc2a7df6a2fc0862b0436558170629874))

* Added sort ([`4c366ed`](https://github.com/UCSD-E4E/e4e-data-management/commit/4c366ed0339383cc3acbc20795049d2010dbe6bb))

* Merge remote-tracking branch &#39;origin/main&#39; into 22-readme-does-not-appear-in-staging-list-when-added-with-readme-flag ([`876cfd2`](https://github.com/UCSD-E4E/e4e-data-management/commit/876cfd21ee80587323ac92d8ae99935e7f54a7a2))

* Added appropriate output logic ([`d52e040`](https://github.com/UCSD-E4E/e4e-data-management/commit/d52e0405b87c947a5dec7fecff9fa5fee33fa2fc))

* Added readme test ([`10dbc08`](https://github.com/UCSD-E4E/e4e-data-management/commit/10dbc083bc2310bd55c039043c6c8ead979ef927))

* Merge remote-tracking branch &#39;origin/main&#39; into 23-e4edm-results-in-error-thrown ([`71e8a05`](https://github.com/UCSD-E4E/e4e-data-management/commit/71e8a051973d709d71689b2c5fa29c9b157afc1b))

* Update build version ([`36e5596`](https://github.com/UCSD-E4E/e4e-data-management/commit/36e5596f544c28c4b9eb9d1efe5c49bc9e9f2a38))

* Updated parser for version and default action ([`5c221ab`](https://github.com/UCSD-E4E/e4e-data-management/commit/5c221abea6989d2157a253b0e77f83bef991bba6))

* Added test ([`bd83e1c`](https://github.com/UCSD-E4E/e4e-data-management/commit/bd83e1ca1edb52b5addcddbd529fa480d2e7e1ff))

* Merge remote-tracking branch &#39;origin/main&#39; into 25-as-a-user-i-would-like-e4edm-push-to-include-the-dataset-directory-so-that-i-do-not-lose-the-dataset-context ([`cd756cc`](https://github.com/UCSD-E4E/e4e-data-management/commit/cd756cce6417936c7c24c0cbe4441bdd5126dc05))

* Added push directory logic ([`881b624`](https://github.com/UCSD-E4E/e4e-data-management/commit/881b624e980375e6543b940e7b404c0b5dae49df))

* Adding check for directory name existence ([`d76d53c`](https://github.com/UCSD-E4E/e4e-data-management/commit/d76d53cad9540cefd4853bc965debaf62b586554))

* Added destination kwarg ([`97154a6`](https://github.com/UCSD-E4E/e4e-data-management/commit/97154a60b18d1fe4d106374e12fb67f39201dac2))

* Merge remote-tracking branch &#39;origin/main&#39; into 26-add-timezone-aware-timestamps ([`c3e2919`](https://github.com/UCSD-E4E/e4e-data-management/commit/c3e29199e70bbeb9af42077ae8890eabbd3c62aa))

* Merge pull request #27 from UCSD-E4E/21-staging-files-does-not-work-with-absolute-path

21 staging files does not work with absolute path ([`fbb6b3e`](https://github.com/UCSD-E4E/e4e-data-management/commit/fbb6b3e5867d4d304e2db4851cbbdd8e8b2d2b84))

* Fixed trailing whitespace ([`bf3be43`](https://github.com/UCSD-E4E/e4e-data-management/commit/bf3be43ae49023a26d224a47a7184389201fc1d0))

* Updated status output ([`24ced5b`](https://github.com/UCSD-E4E/e4e-data-management/commit/24ced5bee8dbff362796823cb07e9980655022d6))

* Updated version ([`05a5024`](https://github.com/UCSD-E4E/e4e-data-management/commit/05a50244b36b15f51700ed8194b4bddd71a74dc0))

* Corrected staging and commit behavior ([`fd70b1d`](https://github.com/UCSD-E4E/e4e-data-management/commit/fd70b1df8784638e3dc38690db13edcae107fb5c))

* Added test function ([`d31ba78`](https://github.com/UCSD-E4E/e4e-data-management/commit/d31ba788af8750443478797e6f42a14af773918a))

* Fixed filter behavior ([`b4e2c35`](https://github.com/UCSD-E4E/e4e-data-management/commit/b4e2c35477a9083643017d0b15d939cc60ae8a0c))

* Changed start time to local system based ([`36086df`](https://github.com/UCSD-E4E/e4e-data-management/commit/36086df6e25f8fbd62e33724eac6d4af8d26bb2d))

* Added timezone awareness ([`7ec26a0`](https://github.com/UCSD-E4E/e4e-data-management/commit/7ec26a001803067e3758caa2f4030f4d13fc11e9))

* Added timezone aware test for e4edm add ([`1fe90d8`](https://github.com/UCSD-E4E/e4e-data-management/commit/1fe90d89923445c2ad9970aa43000284a382dce1))

* Merge pull request #19 from UCSD-E4E/getting_started

Updated tutorial ([`219d3ab`](https://github.com/UCSD-E4E/e4e-data-management/commit/219d3ab6584c8c1a10ce2643f78ff70fb1b4695a))

* Updated tutorial ([`a0475cd`](https://github.com/UCSD-E4E/e4e-data-management/commit/a0475cdfd422afc7bf6a774558111093261a2946))

* Merge pull request #17 from UCSD-E4E/in-app-versioning

Added facility to get version at runtime ([`d6682a1`](https://github.com/UCSD-E4E/e4e-data-management/commit/d6682a1adabaf164de231a1aee863e0824efa0a5))

* Fixed command handling ([`17f5f8b`](https://github.com/UCSD-E4E/e4e-data-management/commit/17f5f8b50f06866b372ed0c2c97226267fbb187a))

* Updated version ([`84ab634`](https://github.com/UCSD-E4E/e4e-data-management/commit/84ab634606b25f93520751ae721a046e5fd9a977))

* Added facility to get version at runtime ([`1dcb260`](https://github.com/UCSD-E4E/e4e-data-management/commit/1dcb260fa53c5108b13b6804d5e556a0fe348264))

* Merge pull request #16 from UCSD-E4E/8-init_mission-help

Updates init_mission help text ([`577ce67`](https://github.com/UCSD-E4E/e4e-data-management/commit/577ce670d6f1ed293c8248d873564ee161e650ff))

* Updates init_mission help text ([`612f10b`](https://github.com/UCSD-E4E/e4e-data-management/commit/612f10b1a956dfe373dfa5dc2195570b33fcabd4))

* Merge pull request #15 from UCSD-E4E/init_dataset_default_dir

init_dataset default directory ([`6d850ee`](https://github.com/UCSD-E4E/e4e-data-management/commit/6d850ee2086cdc6293194883a577372c88b93641))

* Update build version ([`1ddd5d7`](https://github.com/UCSD-E4E/e4e-data-management/commit/1ddd5d7661ced817b8549425b42e15c6077af886))

* Refactored cli to OOP, added config ([`72c8f53`](https://github.com/UCSD-E4E/e4e-data-management/commit/72c8f53e6470969a8d107728c53eadbb15a0b4a1))

* Added tests for cli ([`722933b`](https://github.com/UCSD-E4E/e4e-data-management/commit/722933b23fa5af6ed9490c5d6579cc396ec9ba33))

* Added dataset dir value ([`33a4b36`](https://github.com/UCSD-E4E/e4e-data-management/commit/33a4b3659d0811608d8311d2ea32c534108a5007))

* Updated test to use mocks ([`4bdff07`](https://github.com/UCSD-E4E/e4e-data-management/commit/4bdff07e9a0b3d09a6897c22ae0c7abaaca74579))

* Merge pull request #14 from UCSD-E4E/init_dataset_today

Added `today` to `init_dataset` command ([`90fc5b5`](https://github.com/UCSD-E4E/e4e-data-management/commit/90fc5b59c49c7f8745e911e7488572f373ce0ede))

* Updated version ([`87f9df6`](https://github.com/UCSD-E4E/e4e-data-management/commit/87f9df667da6a9ecd2cec2b83f8af6251cf06efa))

* Fixed test ([`8a05446`](https://github.com/UCSD-E4E/e4e-data-management/commit/8a0544655d2cb2e304c88f9dd618c313e7723b64))

* Added date parser ([`104388a`](https://github.com/UCSD-E4E/e4e-data-management/commit/104388a4e85016ca601464e62be7d71f2e659483))

* Added test ([`49117c0`](https://github.com/UCSD-E4E/e4e-data-management/commit/49117c0c1f13232b98a717cd46799a7aaf5c5500))

* Updated version ([`a741907`](https://github.com/UCSD-E4E/e4e-data-management/commit/a741907dd836e55645120d3a33a3f4699963f80d))

* Merge pull request #13 from UCSD-E4E/cli_output_fix

Cli output fix ([`0532c19`](https://github.com/UCSD-E4E/e4e-data-management/commit/0532c197008be534358707216e836fd272b46952))

* Merge branch &#39;main&#39; into cli_output_fix ([`c223d37`](https://github.com/UCSD-E4E/e4e-data-management/commit/c223d37b1f013698cb63a4f90389499938e28eb0))

* Updated version ([`b227d29`](https://github.com/UCSD-E4E/e4e-data-management/commit/b227d29e8e3321d6bf8c8904e604d8e2797d5d1d))

* Merge pull request #12 from UCSD-E4E/add_date_range

Add date range, activate ([`49de6e8`](https://github.com/UCSD-E4E/e4e-data-management/commit/49de6e8b1bd81dc8da1bd926fdbc05b9e3d38ed6))

* Merge branch &#39;main&#39; into add_date_range ([`3bb8608`](https://github.com/UCSD-E4E/e4e-data-management/commit/3bb8608cd0dc65b086a98815243609937f86f485))

* Updated version ([`41dedb1`](https://github.com/UCSD-E4E/e4e-data-management/commit/41dedb151cb20d940ffc93f95a5d1ebb0460f8ed))

* Merge pull request #10 from UCSD-E4E/no_active_fix

Enables run with no active dataset ([`710c3ee`](https://github.com/UCSD-E4E/e4e-data-management/commit/710c3ee60f58a031765a73feaa7146f70b3b0b06))

* Fixed test ([`a049d37`](https://github.com/UCSD-E4E/e4e-data-management/commit/a049d3757f451d4b209e6eff91e18b51d2696c3c))

* Merge branch &#39;main&#39; into no_active_fix ([`df42e2b`](https://github.com/UCSD-E4E/e4e-data-management/commit/df42e2b0ef22dbe1c009b6a83d46d612ef0b3d4c))

* Update __init__.py ([`e9d7b22`](https://github.com/UCSD-E4E/e4e-data-management/commit/e9d7b22bbc6c1433bb6bf65e89d7b97c10ee9d4d))

* Merge pull request #11 from UCSD-E4E/config_versioning

Added versioning ([`4839c54`](https://github.com/UCSD-E4E/e4e-data-management/commit/4839c54c537e58c57e8bb31a27503b6332993a92))

* Added versioning ([`3fcf47f`](https://github.com/UCSD-E4E/e4e-data-management/commit/3fcf47f649b147ba25d82f70b88af0d10caaae08))

* Added test to validate exit on help in empty config ([`507f57d`](https://github.com/UCSD-E4E/e4e-data-management/commit/507f57d00bf51b5699d2605880feb9775fd61419))

* Fixes init mission for no active dataset ([`df19ad5`](https://github.com/UCSD-E4E/e4e-data-management/commit/df19ad551e9b6c1d120246d42e701f0cb2bff219))

* Updated project name ([`ea8d608`](https://github.com/UCSD-E4E/e4e-data-management/commit/ea8d608aba16cb0db985a5213569471dda2ce5df))

* Removed repeat code ([`e3f00c5`](https://github.com/UCSD-E4E/e4e-data-management/commit/e3f00c52c41ca2111538e607fd71b58d346a2f0e))

* Added activate command ([`6d35afa`](https://github.com/UCSD-E4E/e4e-data-management/commit/6d35afa848c1807c409a78b723f8f1090c51e8c8))

* Added bracketing datetime ([`910d8a9`](https://github.com/UCSD-E4E/e4e-data-management/commit/910d8a9c89b0acdf7bbb0bccf794586b71193add))

* Fixed typing ([`e087112`](https://github.com/UCSD-E4E/e4e-data-management/commit/e087112319f10f81f072ba6c2b62731fc556c414))

* Removing sort ([`209db95`](https://github.com/UCSD-E4E/e4e-data-management/commit/209db9595cf55c85dc982f403acae1f0aeb402bc))

* Adding separate timed file ([`3337f50`](https://github.com/UCSD-E4E/e4e-data-management/commit/3337f507e81db8bfda30a900f7e78a5db109943e))

* Added sorting for test ([`5c6ddb7`](https://github.com/UCSD-E4E/e4e-data-management/commit/5c6ddb74f64c2e896cfcbc8b4c5e3595c32a4642))

* Added number of staged files ([`5a9b821`](https://github.com/UCSD-E4E/e4e-data-management/commit/5a9b8218ca62f8aae328098e4c14fd6ad641b82b))

* Added date filter test ([`2d9687d`](https://github.com/UCSD-E4E/e4e-data-management/commit/2d9687df827a78873490b307daf1370fe3c56730))

* Added start/stop filtering on add ([`f66c9ad`](https://github.com/UCSD-E4E/e4e-data-management/commit/f66c9ad700f1c6d61d510aa5a3bff703ca14f83c))

* Fixed the status command output ([`613b7af`](https://github.com/UCSD-E4E/e4e-data-management/commit/613b7af688c7e156770ad429009a8c7735d05fe8))

* Clearing the active mission on new dataset ([`3f03716`](https://github.com/UCSD-E4E/e4e-data-management/commit/3f037163947f32e96b07cd1d1535745967a27785))

* Merge pull request #3 from UCSD-E4E/readme_commit

Readme Functionality ([`a94be4e`](https://github.com/UCSD-E4E/e4e-data-management/commit/a94be4e6791ef177cd6b4ed1247fc58d65dbf510))

* Remove odt, fixed dataset staging for push ([`88efa94`](https://github.com/UCSD-E4E/e4e-data-management/commit/88efa94d6496b8d37f62056e30bf4f29cfe1549f))

* Adding odt file to readme accept list ([`01f13d0`](https://github.com/UCSD-E4E/e4e-data-management/commit/01f13d0fecd83334ade69f00855355a329c5f9c9))

* making readme in DataManager.commit not kwarg ([`42ad050`](https://github.com/UCSD-E4E/e4e-data-management/commit/42ad050eb8fce14249a1d913940c2a6bdfb6cf6e))

* Removed trailing whitespace ([`42c1497`](https://github.com/UCSD-E4E/e4e-data-management/commit/42c1497f8e9b877b35e653be61ca6ac27d18ff10))

* Added regex for readme acceptance on *nix ([`20fe29d`](https://github.com/UCSD-E4E/e4e-data-management/commit/20fe29d0df008b5e7d3727dab48c7e2ac33f351b))

* Fixed push logic ([`d11922b`](https://github.com/UCSD-E4E/e4e-data-management/commit/d11922bb5936b1530f7f2309c0d21d7c18c83bdd))

* Fixed push readme acceptance ([`b80d7c5`](https://github.com/UCSD-E4E/e4e-data-management/commit/b80d7c550edcb1716807e16c4a9a10298f3c27be))

* Adding readme add and commit ([`9d89d0a`](https://github.com/UCSD-E4E/e4e-data-management/commit/9d89d0a0c33a4b3b59afa8413c2b32790c65aecf))

* Merge pull request #2 from UCSD-E4E/cli

Cli ([`fa3009b`](https://github.com/UCSD-E4E/e4e-data-management/commit/fa3009b93cc4241a20f8275f02209a3b222a42a4))

* Merge branch &#39;main&#39;

Conflicts:
	e4e_data_management/cli.py ([`bb7e845`](https://github.com/UCSD-E4E/e4e-data-management/commit/bb7e845df22457df795d7929eba2f6dced3acf3f))

* Update version ([`d65cbe3`](https://github.com/UCSD-E4E/e4e-data-management/commit/d65cbe317bcd32d7fc75ac6bfdc1b4837c683bf2))

* Merge pull request #1 from UCSD-E4E/fix_staging

Fixed staging ([`9df29e5`](https://github.com/UCSD-E4E/e4e-data-management/commit/9df29e55c330aa19896ee2efafae4d4d048d8caf))

* Fixed staging ([`35b56a0`](https://github.com/UCSD-E4E/e4e-data-management/commit/35b56a021a3a3cda878523f21eb90ab71f268c8b))

* Fixed default notes, added status, list ([`94613f3`](https://github.com/UCSD-E4E/e4e-data-management/commit/94613f3339d500147c18076f7320ed126f12b403))

* Switched to subparsers ([`22c8538`](https://github.com/UCSD-E4E/e4e-data-management/commit/22c853842ef46a5eb22b9cbcdc332b58293f436a))

* Simplifying tests ([`c583e70`](https://github.com/UCSD-E4E/e4e-data-management/commit/c583e700fa4a054365eb771b20040425b7b3ee66))

* Removing replicated code ([`3b737e4`](https://github.com/UCSD-E4E/e4e-data-management/commit/3b737e437fc5a56b696d6c835e4cfef94f458787))

* Combined mock_single_mission and single_mission ([`c8f3052`](https://github.com/UCSD-E4E/e4e-data-management/commit/c8f305220fb9c1ac9b763fc156c4c52263fcea8b))

* Fixed type hinting ([`08d02b8`](https://github.com/UCSD-E4E/e4e-data-management/commit/08d02b85805dde381b5f49a54636b4eca26e644c))

* Fixed mission data ([`8f46bdd`](https://github.com/UCSD-E4E/e4e-data-management/commit/8f46bdd16285a692b31fad6ab9daab49abe530f3))

* PEP8 ([`98f1c54`](https://github.com/UCSD-E4E/e4e-data-management/commit/98f1c54aa7761f42449ecadbde5abbe95b528a40))

* Merging test_app and test_mock_app ([`8c9bfb6`](https://github.com/UCSD-E4E/e4e-data-management/commit/8c9bfb67404bc3dae261ab7dc7abb89b0d9fb8bb))

* Updated version ([`539eaed`](https://github.com/UCSD-E4E/e4e-data-management/commit/539eaedf5d46d4875f8ff9eaee5ac583dcf6f3d8))

* Added push and duplicate ([`fcf695f`](https://github.com/UCSD-E4E/e4e-data-management/commit/fcf695f553c0b791dd36f1e45a6d71bb57d3f796))

* Updating readme ([`8d0f4d2`](https://github.com/UCSD-E4E/e4e-data-management/commit/8d0f4d2832d74d86198075f80f4745c2ae1ac00a))

* Removing old data_generator.ipynb ([`1702925`](https://github.com/UCSD-E4E/e4e-data-management/commit/1702925f9f2afe24fe5ff8c1fa7ec74b767b736f))

* Enabled branch coverage ([`14bdd5f`](https://github.com/UCSD-E4E/e4e-data-management/commit/14bdd5f1d0301732ddd97176b1f66c0316f6af49))

* Added bdist_wheel workflow ([`dd08bf5`](https://github.com/UCSD-E4E/e4e-data-management/commit/dd08bf524589e6b7f3294a6b652f5ce6a89d9c4b))

* Updated pylint notes ([`b7e0a78`](https://github.com/UCSD-E4E/e4e-data-management/commit/b7e0a78c89b53fdbdf790d782c244820ed70ba15))

* Added commit cli ([`514325d`](https://github.com/UCSD-E4E/e4e-data-management/commit/514325d4cd01b4a4bc95d0985f7b8ffd00bd0441))

* Pruning imports ([`cd488d5`](https://github.com/UCSD-E4E/e4e-data-management/commit/cd488d57ae0aa4b1142cfe6a7fee7e7f43ed19ec))

* Updated data generation ([`7f1ce27`](https://github.com/UCSD-E4E/e4e-data-management/commit/7f1ce270c3dcfcbe93aaa32479be1dbfc353e9c6))

* Added add_files test ([`25722c4`](https://github.com/UCSD-E4E/e4e-data-management/commit/25722c47a5e7ec1f9058c2a3bd1871ff93916c81))

* Updated imports ([`733a87d`](https://github.com/UCSD-E4E/e4e-data-management/commit/733a87d4f6c466b27137d9b4e7926d6a93cd6b0c))

* Updated to use fixture ([`af13f5f`](https://github.com/UCSD-E4E/e4e-data-management/commit/af13f5f54a301d63ef5ddb8f22c54235c17800ac))

* Added CLI tests ([`40cbf48`](https://github.com/UCSD-E4E/e4e-data-management/commit/40cbf48ae7b5f6cce39af04f5dda74398a5e723f))

* Fixed naming ([`0f4576a`](https://github.com/UCSD-E4E/e4e-data-management/commit/0f4576ae62bc7c46c86c2456be16ab50a5946eb1))

* Updated usage ([`6ccb453`](https://github.com/UCSD-E4E/e4e-data-management/commit/6ccb4531fb83e23944fc7dffcd7ddb57b535d589))

* Fixed load error handling ([`ed05af2`](https://github.com/UCSD-E4E/e4e-data-management/commit/ed05af2e85628149ff9782354d140e3c352e77dd))

* Fixed load ([`946ade0`](https://github.com/UCSD-E4E/e4e-data-management/commit/946ade0a270c1016762c9129f610d7a116faabf7))

* Implemented commit ([`3f31848`](https://github.com/UCSD-E4E/e4e-data-management/commit/3f3184875cb734b4b77fba4b3ffef02431a538ef))

* Removed old modules ([`3466be0`](https://github.com/UCSD-E4E/e4e-data-management/commit/3466be06399602b0ca902fd2c3101ff9667cfab3))

* Fixed final newline ([`58dbed6`](https://github.com/UCSD-E4E/e4e-data-management/commit/58dbed63892774c2e5657ed03486ecd53fa96e24))

* Merged app config into app ([`42a722c`](https://github.com/UCSD-E4E/e4e-data-management/commit/42a722c3ef76f93a614e2b36d5218fd28a6adbe4))

* Added initial staging logic ([`f6c370b`](https://github.com/UCSD-E4E/e4e-data-management/commit/f6c370b2d796065edecaaf32241981706206bf48))

* Checking that app state is updated ([`3207d98`](https://github.com/UCSD-E4E/e4e-data-management/commit/3207d98e3899e956154c4c5a9a366194de01df7e))

* Fixed state ([`84277f4`](https://github.com/UCSD-E4E/e4e-data-management/commit/84277f4841e15939cfa84d124f3a9c2739017fc7))

* Fixed config load error handling ([`602f9a4`](https://github.com/UCSD-E4E/e4e-data-management/commit/602f9a4181e4c588b61da33a4b1a011be6a99c66))

* Updated logic ([`1a2543c`](https://github.com/UCSD-E4E/e4e-data-management/commit/1a2543c66de7adae28c13737d86a5f213ecee966))

* Removed old executables ([`74702b6`](https://github.com/UCSD-E4E/e4e-data-management/commit/74702b6b57d40012fe0708fb78a68348641c02a1))

* Removing old files ([`88319b2`](https://github.com/UCSD-E4E/e4e-data-management/commit/88319b23e56da363a28c9e641b3e2addb6619423))

* Fixed error state ([`b9b5737`](https://github.com/UCSD-E4E/e4e-data-management/commit/b9b5737315b8d3c6694dd8662f213c7ba975e00a))

* Fixed error state ([`4b593da`](https://github.com/UCSD-E4E/e4e-data-management/commit/4b593dac29c51d0756cb0fda3c14ad7e108e3abf))

* Fixed error handling ([`8104f81`](https://github.com/UCSD-E4E/e4e-data-management/commit/8104f8162057c992257d92c30ebf8a0bbb05822a))

* Fixed list output ([`8a1f91d`](https://github.com/UCSD-E4E/e4e-data-management/commit/8a1f91d77c1d3bd23e9571bc52cae43736ab06e5))

* Fixed statefulness of config ([`08d0f91`](https://github.com/UCSD-E4E/e4e-data-management/commit/08d0f91d0e705c75d559400d21e5410bca1ba2e0))

* Fixed repeat init_dataset ([`316692c`](https://github.com/UCSD-E4E/e4e-data-management/commit/316692c3042c51b55f813fb77351359110f7c56c))

* Added convenience commands ([`1c10bbd`](https://github.com/UCSD-E4E/e4e-data-management/commit/1c10bbdf6da8b6e7108e3a56fc5685aabd896347))

* Adding initial folder structure design ([`3cbf342`](https://github.com/UCSD-E4E/e4e-data-management/commit/3cbf342d53855f6aed31fd6184ef31e7d3c1375e))

* Added init_dataset tests ([`66aca89`](https://github.com/UCSD-E4E/e4e-data-management/commit/66aca89013092a7365dbec9308e9c13635065fe6))

* Removed old interfaces, using status ([`763c234`](https://github.com/UCSD-E4E/e4e-data-management/commit/763c234d15b915656f23425037bc0e6b3c5b18f9))

* Added app config bypass for testing ([`daa481e`](https://github.com/UCSD-E4E/e4e-data-management/commit/daa481e0574047a865e11e31632cea53c655d591))

* Updated command line flags for init_dataset ([`a4b17be`](https://github.com/UCSD-E4E/e4e-data-management/commit/a4b17bed86d6f3821c8db5ccb7f615ad2a52e391))

* Removed read creation ([`5f57763`](https://github.com/UCSD-E4E/e4e-data-management/commit/5f57763078838faa48470fd29d918e5b4011a3bb))

* Fixed windows test ([`51d94c7`](https://github.com/UCSD-E4E/e4e-data-management/commit/51d94c7de492b3584ed031c3874901353d4a3cc0))

* Updated core logic ([`e31965b`](https://github.com/UCSD-E4E/e4e-data-management/commit/e31965b970f6fc27301529e556e418e86bcc7cce))

* Using activate instead of select ([`dd4a6bd`](https://github.com/UCSD-E4E/e4e-data-management/commit/dd4a6bd7fa9db65630de5b4ba344d688c98293a6))

* Renamed core to cli ([`1814a63`](https://github.com/UCSD-E4E/e4e-data-management/commit/1814a63446d2cc3473ec2e543a924db3bc64de49))

* Made interface more git-like ([`e6d4648`](https://github.com/UCSD-E4E/e4e-data-management/commit/e6d4648f9fc6b41ea2043743de1fb5c62ad8da90))

* Added e4edm interface ([`18de0bb`](https://github.com/UCSD-E4E/e4e-data-management/commit/18de0bbf812bb7be32d23d80d6b565d8c359e4e8))

* Updated pylint ([`9fd6b78`](https://github.com/UCSD-E4E/e4e-data-management/commit/9fd6b78907868123ef21df0bf1093dcd057b8c30))

* Added schema to install_requires ([`7d0330e`](https://github.com/UCSD-E4E/e4e-data-management/commit/7d0330ea49f992c5690a698e8817a39378dee7ca))

* Added pytest ([`b2a6f71`](https://github.com/UCSD-E4E/e4e-data-management/commit/b2a6f71eb573eb46572144229c507a64d9bd7a6c))

* Added commit tool structure ([`b55e8fc`](https://github.com/UCSD-E4E/e4e-data-management/commit/b55e8fc45260655fa60aa209e67e56f643ab1acc))

* Fixed to disallow creation of non-timezone aware metadatas ([`3fe96a0`](https://github.com/UCSD-E4E/e4e-data-management/commit/3fe96a00d9fc36229010f35847ad4a514b7ebe4e))

* Added completed dataset fixtures ([`18c110a`](https://github.com/UCSD-E4E/e4e-data-management/commit/18c110a96075bfa1b8843da274fce2175f3bbf3c))

* Added duplication structure ([`c7b14b7`](https://github.com/UCSD-E4E/e4e-data-management/commit/c7b14b733af92b57e9f158e59c472b394a698e9c))

* Added validation and test generator ([`95b3ce3`](https://github.com/UCSD-E4E/e4e-data-management/commit/95b3ce3f98f8bc9e2bc895ea7875b5d4bb996974))

* Added validators ([`b954ba6`](https://github.com/UCSD-E4E/e4e-data-management/commit/b954ba6a5cd74c93457348d1dda72d10eca22bf1))

* Added test dataset and generator ([`cec6ae7`](https://github.com/UCSD-E4E/e4e-data-management/commit/cec6ae71b238c27a81a500bf66b0bffeaef4f7c1))

* Fixed naming ([`f380bf7`](https://github.com/UCSD-E4E/e4e-data-management/commit/f380bf71f836fa8c9540f10f7944933047be983a))

* Added manifest logic ([`d729026`](https://github.com/UCSD-E4E/e4e-data-management/commit/d72902601351a1078231be0fb2e59c5753fb7de7))

* Removed unused jupyter notebook ([`9059199`](https://github.com/UCSD-E4E/e4e-data-management/commit/9059199dcd6944e14532e5302ff361925f02dabe))

* Updated README ([`5dae09b`](https://github.com/UCSD-E4E/e4e-data-management/commit/5dae09b61f13fe08b7f6f2e82801f727f02b9d48))

* Initial changes ([`be60b28`](https://github.com/UCSD-E4E/e4e-data-management/commit/be60b281a42d3d5c9040ae341525e8f87e7560f8))

* Initial commit ([`5ae3eb2`](https://github.com/UCSD-E4E/e4e-data-management/commit/5ae3eb296e5eea5f096abe58e02937627928bb8e))
