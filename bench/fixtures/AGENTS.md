# example-app

## Setup
Run `pnpm install` before working on this repo.

## Build
Run `pnpm build` to produce a production bundle in `dist/`.

## Test
Run `pnpm test` before opening a PR. All tests must pass.

## Code Style
- 2-space indentation
- Single quotes for strings
- Trailing commas in multi-line literals

## Pull Requests
- Title format: Conventional Commits (`feat:`, `fix:`, `chore:`, etc.)
- One logical change per PR
- Link the related issue in the description

## Security
- Never commit `.env` files
- Run `pnpm audit` before publishing
