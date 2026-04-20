# Decision: Build automation artifacts and release tagging responsibilities

- Status: accepted
- Date: 2026-04-20
- Owner: Spec

## Context
The project needs GitHub-visible automation that can build the Decky plugin and package it as a zip artifact suitable for Decky Loader consumption. Patrick also wants the release flow to make clear that, once the relevant automation work is merged to `main`, the release manager should tag the result as part of the release process.

## Decision
1. **GitHub Actions should produce a Decky Loader friendly package artifact**
   - The automation path should build the plugin from repository state in GitHub Actions.
   - It should package a Decky Loader friendly zip artifact that is reviewable from GitHub-visible workflow outputs.

2. **Build/package automation and release tagging are separate responsibilities**
   - The Builder-facing automation slice should focus on producing verifiable build outputs and package artifacts.
   - Release-manager tagging should remain a separate release-coordination step after the relevant automation path is merged to `main`.

3. **Artifact contents must be explicit**
   - The packaging contract should state what files belong in the shipped plugin zip and what development-only files are excluded.
   - The artifact should be suitable for Decky Loader installation/testing without requiring repository-only scaffolding.

4. **GitHub-visible verification matters**
   - The automation result should be inspectable from GitHub through workflow runs and artifacts.
   - Release coordination may later decide whether the same package is also attached to GitHub Releases, but workflow artifacts are the minimum required visibility.

## Consequences
- The work should be split into at least one Builder-ready implementation issue for CI build/package automation and one separate release-tracking issue for tagging coordination.
- The automation issue should define the package boundary clearly enough for QA and release review.
- The release-tagging expectation is now durable project truth rather than a chat-only instruction.
