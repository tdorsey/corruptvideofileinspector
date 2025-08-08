## Issue: Problem with Actions Workflow

### Description
The workflow for the repository is failing during the video processing step. The error message indicates that the video file cannot be processed due to an unknown format or corruption.

### Steps to Reproduce
1. Trigger the GitHub Actions workflow.
2. Observe the error during the video processing step.

### Possible Solutions
- Check the format of the video file being processed.
- Implement error handling for unsupported formats.
- Investigate if the video file is corrupt.

### Additional Context
- This issue was observed during the workflow run [#16820565861](https://github.com/tdorsey/corruptvideofileinspector/actions/runs/16820565861).
- Relevant logs can be found in the Actions tab of the repository.