# Implementation Plan - Data Janitor CLI Enhancement

The goal is to transform the current simple CLI into a robust, AI-powered data cleaning and preparation tool.

## Proposed Changes

### Core Engine ([main.py](file:///e:/Antigravity/linkedin_projects/data_janitor_cli/main.py))

- **Modular Design**: Move logic into a `DataJanitor` class to manage state, file handles, and AI interactions.
- **Enhanced File Support**: Use `pandas` to read/write CSV, Excel, JSON, and Parquet.
- **Improved AI Logic**:
    - Use more descriptive system prompts.
    - Implement a "Code Review" step where the user can see and approve the generated code before execution.
    - Handle potential `exec()` errors more gracefully.
- **Data Profiling**: Before cleaning, perform a quick analysis of the data (missing values, types, basic stats) and present it to the user.

### UI/UX

- **Rich Integration**: Use `rich.table` for data previews and profiling results.
- **Interactive Prompts**: Use `typer.prompt` or `rich` features to ask the user for confirmation or further instructions.
- **Progress Indicators**: Show progress bars during long-running AI calls or data processing.

### New Commands

- `profile`: Strictly for data analysis without cleaning.
- `suggest`: AI suggests cleaning steps based on the profile.
- [clean](file:///e:/Antigravity/linkedin_projects/data_janitor_cli/main.py#35-97): The main cleaning command (enhanced).
- `history`: View previous cleaning steps (basic implementation).

## Verification Plan

### Automated Tests
- Create a test suite to verify file reading/writing for different formats.
- Mock the Gemini API call to test the code execution logic with known inputs.

### Manual Verification
- Run the `profile` command on [test.csv](file:///e:/Antigravity/linkedin_projects/data_janitor_cli/test.csv).
- Run the [clean](file:///e:/Antigravity/linkedin_projects/data_janitor_cli/main.py#35-97) command with various tasks and verify the output.
- Test the interactive mode by refining a cleaning task.
