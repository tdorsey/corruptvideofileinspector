# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0](https://github.com/tdorsey/corruptvideofileinspector/compare/corrupt-video-inspector-v0.1.0...corrupt-video-inspector-v1.0.0) (2025-08-17)


### ⚠ BREAKING CHANGES

* migrate trakt auth to config-based system, remove --token flags and access token requirement ([#104](https://github.com/tdorsey/corruptvideofileinspector/issues/104))

### ✨ Features

* add PR title validation workflow for conventional commits and issue references ([#78](https://github.com/tdorsey/corruptvideofileinspector/issues/78)) ([#79](https://github.com/tdorsey/corruptvideofileinspector/issues/79)) ([7c8ce01](https://github.com/tdorsey/corruptvideofileinspector/commit/7c8ce011538376c324e694759b88f68cac4b0640))
* add Trakt credential validation with user-friendly error messages ([#109](https://github.com/tdorsey/corruptvideofileinspector/issues/109)) ([b9fd0da](https://github.com/tdorsey/corruptvideofileinspector/commit/b9fd0da01c433fba1739b30568b106cd311d3b6b))
* birdvscat ([#57](https://github.com/tdorsey/corruptvideofileinspector/issues/57)) ([87e8735](https://github.com/tdorsey/corruptvideofileinspector/commit/87e8735cd71f9554435b28bc9079c3296153dc3c))
* enhance output handling in BaseHandler and update tests for output generation ([122a375](https://github.com/tdorsey/corruptvideofileinspector/commit/122a375a97e4d2c3ec5e0b0373c284813aa6148e))
* major refactor ([53ed5fb](https://github.com/tdorsey/corruptvideofileinspector/commit/53ed5fbc7d7bc82acf48d34982008f857c9a2ec5))
* many, many non atomic commits ([#71](https://github.com/tdorsey/corruptvideofileinspector/issues/71)) ([b1dd2b9](https://github.com/tdorsey/corruptvideofileinspector/commit/b1dd2b998d1baec56374405101c96662e475ca4f))
* migrate trakt auth to config-based system, remove --token flags and access token requirement ([#104](https://github.com/tdorsey/corruptvideofileinspector/issues/104)) ([9b761d0](https://github.com/tdorsey/corruptvideofileinspector/commit/9b761d02e269c00bb1fa76bd08a0488a1ff9ac6a))


### 🐛 Bug Fixes

* add optional file size formatting to trim trailing .0 from whole numbers ([#91](https://github.com/tdorsey/corruptvideofileinspector/issues/91)) ([#108](https://github.com/tdorsey/corruptvideofileinspector/issues/108)) ([a0a62bd](https://github.com/tdorsey/corruptvideofileinspector/commit/a0a62bd829abab83a09373953cdacbeffa60daf5))
* **makefile:** restore functionality, fix type checking errors, and resolve merge conflicts with main ([#114](https://github.com/tdorsey/corruptvideofileinspector/issues/114)) ([fc595f7](https://github.com/tdorsey/corruptvideofileinspector/commit/fc595f756894d4103eb5ba8d54a9fc72bd9c202c))
* runtime NameError exceptions in core modules ([#112](https://github.com/tdorsey/corruptvideofileinspector/issues/112)) ([5e96bc2](https://github.com/tdorsey/corruptvideofileinspector/commit/5e96bc27d216b27c185937de94bf1d758dbee732))
* **test:** resolve comprehensive test suite failures blocking CI pipeline ([#132](https://github.com/tdorsey/corruptvideofileinspector/issues/132)) ([b62e1f1](https://github.com/tdorsey/corruptvideofileinspector/commit/b62e1f1c4832021d95c81fc743a656f101ce6319))


### 📚 Documentation

* **copilot:** merge development standards with Copilot usage guidelines ([#148](https://github.com/tdorsey/corruptvideofileinspector/issues/148)) ([90de438](https://github.com/tdorsey/corruptvideofileinspector/commit/90de4385d41de161b5ec5150085722ef676eed68))


### ♻️ Code Refactoring

* decouple core modules from CLI interface for better reusability ([#160](https://github.com/tdorsey/corruptvideofileinspector/issues/160)) ([e8d7570](https://github.com/tdorsey/corruptvideofileinspector/commit/e8d7570b712274fc60c7b336c3935c35c4e80242))
* eliminate utility modules ([#73](https://github.com/tdorsey/corruptvideofileinspector/issues/73)) ([90ef9d8](https://github.com/tdorsey/corruptvideofileinspector/commit/90ef9d8cf500b8200a71c403772c87055161a736))


### 🔧 Miscellaneous Chores

* add automatic branch creation workflow for new issues ([#127](https://github.com/tdorsey/corruptvideofileinspector/issues/127)) ([639cdc8](https://github.com/tdorsey/corruptvideofileinspector/commit/639cdc8be16694789fffc9d1397c08dccef24820))
* add CODEOWNERS and issue templates for  security ([#151](https://github.com/tdorsey/corruptvideofileinspector/issues/151)) ([338e6a3](https://github.com/tdorsey/corruptvideofileinspector/commit/338e6a3b6fc89265e6de68f4c5f6c447179817b0))
* **ci:** add auto-assign issue workflow ([#100](https://github.com/tdorsey/corruptvideofileinspector/issues/100)) ([6b7c54a](https://github.com/tdorsey/corruptvideofileinspector/commit/6b7c54aea7b06ff6f69f0ad774ed458f22634fb3))
* configure agent setup to install network dependencies before firewall activation ([#164](https://github.com/tdorsey/corruptvideofileinspector/issues/164)) ([e52b108](https://github.com/tdorsey/corruptvideofileinspector/commit/e52b10884d24249d448c12a4897cbccc6a5b1217))
* configure repository settings via .github/settings.yaml and CODEOWNERS ([#128](https://github.com/tdorsey/corruptvideofileinspector/issues/128)) ([d6b030f](https://github.com/tdorsey/corruptvideofileinspector/commit/d6b030f87486b7094ff615d743b7497b9bc2e806))
* **deps:** bump urllib3 in the pip group across 1 directory ([#135](https://github.com/tdorsey/corruptvideofileinspector/issues/135)) ([6f3cd88](https://github.com/tdorsey/corruptvideofileinspector/commit/6f3cd8863effcc17a62eac33ecc232ede78a7d2d))
* disable code owner reviews and fix CI status check names ([#156](https://github.com/tdorsey/corruptvideofileinspector/issues/156)) ([412727d](https://github.com/tdorsey/corruptvideofileinspector/commit/412727d6be9a268284d65271b32e0c174a35dfac))
* ensure FFmpeg is installed as a development dependency, streamline repository settings, and integrate latest main branch updates via rebase ([#153](https://github.com/tdorsey/corruptvideofileinspector/issues/153)) ([bb8b702](https://github.com/tdorsey/corruptvideofileinspector/commit/bb8b702e9813b114d7534cdc7828f22b2d993015))
* **github-actions:** correct assignee format in auto-assign-issue workflow ([#124](https://github.com/tdorsey/corruptvideofileinspector/issues/124)) ([454cc27](https://github.com/tdorsey/corruptvideofileinspector/commit/454cc27faa8e2b3e050c565ce8e1f09277fe629c))
* **github:** enhance issue templates with title examples and automated labeling ([#147](https://github.com/tdorsey/corruptvideofileinspector/issues/147)) ([8b48028](https://github.com/tdorsey/corruptvideofileinspector/commit/8b48028544f82d896866b9d4824737dd1b9df44b))
* implement GitHub Actions workflow validation with actionlint  ([#130](https://github.com/tdorsey/corruptvideofileinspector/issues/130)) ([fe71ed1](https://github.com/tdorsey/corruptvideofileinspector/commit/fe71ed152ea6c7d189ff7f95333a24fa1a31c129))
* improve CI/CD workflow with conditional Docker build, enhanced PR validation, and resolved merge conflicts ([#141](https://github.com/tdorsey/corruptvideofileinspector/issues/141)) ([e1d3b58](https://github.com/tdorsey/corruptvideofileinspector/commit/e1d3b58e79478c98a8ab7a6463642b830adf5192))
* refactor PR title check workflow to use marketplace actions ([#116](https://github.com/tdorsey/corruptvideofileinspector/issues/116)) ([c6f12aa](https://github.com/tdorsey/corruptvideofileinspector/commit/c6f12aaaf37105b2f9ffa4233f052b56cdc18f43))
* remove code of conduct sections from issue templates ([#139](https://github.com/tdorsey/corruptvideofileinspector/issues/139)) ([b1157fa](https://github.com/tdorsey/corruptvideofileinspector/commit/b1157fa7d51a7cd2e608ed60cc178d541761eaea))
* remove piny package and its dependencies from poetry.lock ([#59](https://github.com/tdorsey/corruptvideofileinspector/issues/59)) ([ab9c114](https://github.com/tdorsey/corruptvideofileinspector/commit/ab9c11427f3960dedc6616c8a26756823446822f))
* replace custom labeler with marketplace action and improve GitHub Actions guidelines ([#95](https://github.com/tdorsey/corruptvideofileinspector/issues/95)) ([c03a535](https://github.com/tdorsey/corruptvideofileinspector/commit/c03a53553294f2591b141c8ec965fd8457aa402d))
* resolve merge conflicts and enhance copilot-instructions.md with instruction file links ([#99](https://github.com/tdorsey/corruptvideofileinspector/issues/99)) ([96e27dd](https://github.com/tdorsey/corruptvideofileinspector/commit/96e27dd0d4dae83fad539494b72dd42b9a842dc1))


### 👷 Continuous Integration

* add Dependabot configuration for Python dependencies ([#117](https://github.com/tdorsey/corruptvideofileinspector/issues/117)) ([#125](https://github.com/tdorsey/corruptvideofileinspector/issues/125)) ([b266365](https://github.com/tdorsey/corruptvideofileinspector/commit/b2663654ebea94de2437ee26e12d7b0770f0f249))
* disable PyPI publishing to prevent accidental releases ([#126](https://github.com/tdorsey/corruptvideofileinspector/issues/126)) ([481c680](https://github.com/tdorsey/corruptvideofileinspector/commit/481c680f7ad8f4eadddd560652cb7666c5df8db2))
* implement CODEOWNERS and branch protection for .github/settings.yml ([#152](https://github.com/tdorsey/corruptvideofileinspector/issues/152)) ([b1da187](https://github.com/tdorsey/corruptvideofileinspector/commit/b1da187f2d102e9f3ace20c645305b0f52c931f8))
* optimize pipeline to run security scan in parallel with formatting and linting ([#158](https://github.com/tdorsey/corruptvideofileinspector/issues/158)) ([8d395d3](https://github.com/tdorsey/corruptvideofileinspector/commit/8d395d3c67ff4f6c7b85d87331b09aa27b178497))
* refactor workflows for atomic tasks, complete Conventional Commit support, and remove pozil/auto-assign-issue ([#144](https://github.com/tdorsey/corruptvideofileinspector/issues/144)) ([9811c06](https://github.com/tdorsey/corruptvideofileinspector/commit/9811c06a6476c09e22af8280705cdf2f302b002e))
* resolve merge conflicts and maintain PR validation workflow functionality ([#134](https://github.com/tdorsey/corruptvideofileinspector/issues/134)) ([3c7095d](https://github.com/tdorsey/corruptvideofileinspector/commit/3c7095d218c1678d1dcb375c34c4790897d48475))
* **workflows:** improve release workflow with best practices and fix Docker credential references ([#154](https://github.com/tdorsey/corruptvideofileinspector/issues/154)) ([f5e3403](https://github.com/tdorsey/corruptvideofileinspector/commit/f5e3403bc4d5afb17979f07227c74ce65fb5e817))

## [Unreleased]

### Changed

#### ⚠️ **BREAKING CHANGE**: Trakt sync default behavior

- **Changed default `include_statuses` for Trakt sync from `[CORRUPT, SUSPICIOUS]` to `[HEALTHY]`**
  
  **Impact**: Trakt sync operations will now sync healthy video files by default instead of corrupt/suspicious files.
  
  **Rationale**: 
  - Users typically want to sync their working video files to Trakt watchlists
  - Syncing corrupt files to a watchlist provides limited value
  - Previous default was counterintuitive for most use cases
  
  **Migration**: To restore previous behavior, explicitly configure:
  ```yaml
  trakt:
    include_statuses: [CORRUPT, SUSPICIOUS]
  ```
  
  Or use CLI flag:
  ```bash
  corrupt-video-inspector trakt sync results.json --include-statuses CORRUPT SUSPICIOUS
  ```

### Fixed
- Updated test expectations to match new Trakt sync default behavior

### Documentation
- Updated CONFIG.md with Trakt configuration documentation
- Updated trakt.md to clarify new default sync behavior
- Added migration instructions for users requiring previous behavior
