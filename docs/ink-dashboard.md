# Ink dashboard

This milestone adds a minimal read-only TypeScript Ink dashboard in
`frontend/`. The Python backend remains the source of truth for authentication,
session storage, portal requests, parsing, and business rules.

## Architecture

```text
Ink dashboard
  |
  | execFile("tudelft", ["status", "--output", "json"])
  | execFile("tudelft", ["whoami", "--output", "json"])
  | execFile("tudelft", ["ec", "--output", "json"])
  | execFile("tudelft", ["grades", "--output", "json"])
  v
Existing Python CLI
  |
  v
Existing Python services, auth, portal, and formatters
```

The TypeScript frontend does not call MyTU Delft directly, inspect session
files, or duplicate portal logic. It only consumes the public JSON contracts
exposed by the Python CLI.

## Subprocess communication

`frontend/src/client/pythonCli.ts` is the only module that spawns the Python
CLI. It resolves the command from `TUDELFT_CLI` and falls back to `tudelft`.

Each dashboard command is executed with `child_process.execFile`, explicit
argument arrays, and `--output json`. `TUDELFT_CLI` may contain a simple
executable or a quoted multi-token command; the frontend parses it into an
executable plus arguments and does not run it through a shell. The client owns
timeout handling, non-zero exit handling, and JSON parse errors. UI components
receive normalized error messages and render them next to the affected panel.

Commands used by the first dashboard:

- `tudelft status --output json`
- `tudelft whoami --output json`
- `tudelft ec --output json`
- `tudelft grades --output json`

## Keyboard shortcuts

- `q`: quit the dashboard
- `r`: refresh all dashboard data

## Development

From `frontend/`:

```bash
npm install
npm run build
npm run dev
```

`npm run start` runs the compiled `dist/index.js`, so run `npm run build` first
after TypeScript changes.

By default, the dashboard expects `tudelft` to be available on `PATH`:

```bash
npm run dev
```

If the Python CLI is available through `uv`, point the dashboard at that command:

```bash
TUDELFT_CLI="uv run tudelft" npm run dev
```

For direct module execution, run from `frontend/` and expose the Python source
tree if the package is not installed in the active environment:

```bash
PYTHONPATH=../src TUDELFT_CLI="python -m tudelft_cli.main" npm run dev
```

If the package is installed editable or otherwise importable, `PYTHONPATH` is
not required:

```bash
TUDELFT_CLI="python -m tudelft_cli.main" npm run dev
```

## Future roadmap

- Add tests for the subprocess client with mocked `execFile` behavior.
- Add dashboard data tests with representative JSON fixtures.
- Add read-only enrollments once the first dashboard layout has settled.
- Consider a hidden Python batch/RPC command only if subprocess refresh latency
  becomes a measured problem.
- Keep enrollment mutations out of the dashboard until the backend exposes
  explicit dry-run, confirmation, and result contracts for TUI use.
