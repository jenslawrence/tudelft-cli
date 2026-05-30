# TypeScript TUI frontend direction

This note proposes a low-risk path for adding a TypeScript terminal UI to
`tudelft-cli` without rewriting the Python portal, authentication, session, or
Typer/Rich command surface.

## Recommendation

Use Ink for the first implementation.

Ink is the better fit for this repository because the first TUI should be a
thin, read-only frontend over the existing Python CLI contracts. The project
does not currently need a native terminal rendering engine, custom text
rasterization, or a high-frequency UI loop. It needs predictable React-style
composition, keyboard handling, snapshot-friendly testing, and simple packaging.

OpenTUI is worth revisiting later if the app grows into a dense, full-screen
workspace with heavier rendering requirements. For the first dashboard/search
milestone, it adds more packaging and native-build risk than benefit.

## Current Backend Shape

The Python application already has a useful separation:

- `src/tudelft_cli/main.py` keeps the public `tudelft` Typer entrypoint.
- `src/tudelft_cli/cli/context.py` wires `SessionStore`,
  `BrowserAuthProvider`, and `MyTUDelftPortal`.
- `src/tudelft_cli/app/services/` contains use-case services such as profile,
  grades, EC progress, enrollments, suggestions, and enrollment actions.
- `src/tudelft_cli/domain/` defines the domain models and interfaces.
- `src/tudelft_cli/infra/` contains Playwright/auth/session/portal integration.

The TUI should not bypass that boundary. Python remains the source of truth for
MyTU Delft auth, sessions, portal requests, portal parsing, and enrollment
mutations.

## Ink vs OpenTUI

| Area | Ink | OpenTUI |
| --- | --- | --- |
| Maturity | Mature React renderer for CLIs with many production users. The official README positions it as React for command-line apps and lists major CLI users. | Newer and moving quickly. The official README describes a native Zig terminal UI core with TypeScript bindings and production use in OpenCode. |
| Ecosystem | React, npm, existing Ink components, `ink-testing-library`, React DevTools support, and familiar hooks. | Smaller but promising ecosystem. Provides core TypeScript bindings plus React and Solid reconcilers. |
| React mental model | Direct fit. Components are React components, layout uses Flexbox through Yoga, and keyboard handling uses Ink hooks. | Possible through `@opentui/react`, but OpenTUI's core model is broader than React and closer to a terminal rendering engine. |
| Performance | Enough for dashboard, lists, search, forms, and status panels. Potentially less ideal for very dense or high-frequency cell updates. | Stronger performance story: native Zig core, screen buffer, and renderer focus. Better candidate for very rich full-screen UIs. |
| Packaging | Plain Node/npm package is viable. No native core decision in the first MR. | Native Zig core means more build/distribution complexity. The README notes Zig is required to build packages. |
| Keyboard interactions | Built-in `useInput`, focus hooks, alternate screen support, and common CLI interaction patterns. | Capable, but the app would need to own more renderer/runtime choices early. |
| Testing | `ink-testing-library` supports component render assertions and last-frame checks. This fits a read-only dashboard milestone well. | Testing story is less established for this repo's needs and likely requires more harness work. |
| Risk | Lower. Fits the desired thin frontend and makes it easy to throw away or reshape. | Higher for a first step because it couples the MR to a newer native renderer and packaging decisions. |
| Dashboard/search/enrollment flows | Good fit for dashboard, search results, detail panes, confirmation screens, and read-only data exploration. | Also capable, and may become attractive for a more ambitious full-screen app after the backend contract stabilizes. |

References checked while making this comparison:

- [Ink GitHub README](https://github.com/vadimdemedes/ink)
- [OpenTUI GitHub README](https://github.com/anomalyco/opentui)

## Architecture

Keep the initial TUI as a separate TypeScript frontend process that shells out
to the Python CLI and consumes JSON.

```text
User
  |
  | runs tudelft-tui
  v
TypeScript Ink app
  |
  | child_process.execFile("tudelft", ["grades", "--output", "json"])
  | child_process.execFile("tudelft", ["ec", "--output", "json"])
  | child_process.execFile("tudelft", ["whoami", "--output", "json"])
  v
Existing Python Typer CLI
  |
  v
app/services use cases
  |
  v
domain interfaces and models
  |
  v
infra/auth + infra/portal
  |
  v
MyTU Delft
```

The important constraint is that TypeScript never talks to MyTU Delft directly.
It only talks to stable Python JSON contracts.

## Backend/Frontend Boundary Options

### 1. TypeScript invokes `tudelft ... --output json`

This is the recommended first boundary.

Pros:

- Reuses the installed Python package exactly as users already run it.
- Keeps Typer/Rich commands working.
- Requires only small additions to missing JSON output modes.
- Easy to test from both sides: Python contract tests plus TypeScript client
  tests with mocked subprocess output.
- No daemon lifecycle, port allocation, CORS, auth token exposure, or local
  server cleanup.

Cons:

- Startup overhead per command.
- The frontend must handle process failures, stderr, non-JSON output, and
  authentication errors carefully.
- Public command output becomes an API, so JSON contracts need tests and
  versioning discipline.

### 2. Python exposes a hidden JSON/RPC command surface

Example: `tudelft _rpc dashboard` or `tudelft _json grades`.

Pros:

- Cleaner machine contract than retrofitting public human commands.
- Can batch dashboard data and reduce subprocess calls.
- Keeps Python as the backend source of truth.

Cons:

- Adds a second command layer before the frontend has proven itself.
- More contract design up front.
- Still has subprocess startup cost unless it becomes a long-lived process.

This is a good second step if the dashboard needs one batched call or if public
command JSON starts to constrain human CLI design.

### 3. Python exposes a local HTTP server

Pros:

- Natural request/response model for a frontend.
- Can support incremental loading, caching, and long-running sessions.

Cons:

- Too much lifecycle and security surface for the first MR.
- Requires port management, server startup, shutdown, error handling, and local
  auth considerations.
- Easy to overbuild before the product shape is clear.

Do not choose this first.

### 4. Full backend rewrite in TypeScript

Pros:

- One language for frontend and backend eventually.

Cons:

- Duplicates MyTU Delft portal behavior.
- Reimplements Playwright/auth/session handling.
- Creates high regression risk around the most sensitive code.
- Violates the current architecture and migration constraints.

Do not choose this.

## First Boundary Recommendation

Use subprocess JSON contracts first:

- Add missing `--output json` modes to public read-only commands.
- Treat those JSON payloads as stable API contracts.
- Add Python contract tests for every JSON command used by the TUI.
- In TypeScript, create one narrow `pythonCli.ts` client that owns command
  execution, JSON parsing, timeout behavior, and error normalization.

This is intentionally boring. It keeps the TUI frontend thin and lets the repo
learn what screens and data shapes are actually useful before introducing RPC,
HTTP, or a backend rewrite.

## Proposed Repository Structure

```text
frontend/
  package.json
  tsconfig.json
  src/
    cli.tsx
    App.tsx
    client/
      pythonCli.ts
      contracts.ts
    screens/
      DashboardScreen.tsx
      GradesScreen.tsx
      EnrollmentsScreen.tsx
      SearchScreen.tsx
    components/
      AppFrame.tsx
      StatusBar.tsx
      LoadingState.tsx
      ErrorState.tsx
      DataTable.tsx
      ProgressBar.tsx
    test/
      pythonCli.test.ts
      DashboardScreen.test.tsx
```

Keep this out of the Python package initially. The Python package remains
installable as `tudelft`; the TypeScript package can expose `tudelft-tui`.

## Packaging Direction

First implementation:

- Keep `[project.scripts] tudelft = "tudelft_cli.main:main"` unchanged.
- Add `frontend/` as an optional Node workspace, not as a Python dependency.
- Expose a Node bin named `tudelft-tui`.
- Document that `tudelft-tui` requires `tudelft` to be available on `PATH`.

Later:

- Add `tudelft tui` as a Python wrapper that execs `tudelft-tui` when available.
- Consider bundling the TypeScript frontend into a single executable with a
  tool such as `pkg`, `nexe`, or a platform-specific packaging flow only after
  the TUI is useful.
- Consider an npm package if the frontend becomes independently installable.

Avoid making the first MR solve Python packaging plus Node packaging plus binary
distribution at once.

## First Minimal TUI Milestone

Build a read-only Ink dashboard:

- Full-screen dashboard in alternate screen mode.
- Auth status panel.
- Profile panel when logged in.
- EC progress summary.
- Recent grades list.
- Current course/exam enrollments if JSON is available.
- Refresh key, quit key, and basic error state.
- No enrollment mutations.
- No direct portal calls from TypeScript.

Suggested keys:

- `r`: refresh visible data.
- `g`: focus grades.
- `e`: focus enrollments.
- `/`: search/filter visible rows locally.
- `q` or `Esc`: quit.

The first milestone should be read-only because enrollment actions are
high-consequence and currently rely on Python confirmation flows. Mutation
screens can come later after the TUI has its own confirmation design and the
backend contract can express dry-run, confirmation, and result states.

## Dashboard JSON Contracts

Already present or mostly present:

- `tudelft grades --output json`
- `tudelft grades --final-only --output json`
- `tudelft ec --output json`
- `tudelft course COURSE_CODE --output json`
- `tudelft suggest-courses --output json`
- `tudelft suggest-exams --output json`

Available for the dashboard milestone:

- `tudelft whoami --output json`
- `tudelft enrollments --output json`
- `tudelft enrollments --courses --output json`
- `tudelft enrollments --exams --output json`
- `tudelft status --output json`

Recommended response shapes:

```json
{
  "profile": {
    "name": "Ada Lovelace",
    "student_number": "1234567",
    "email": "ada.lovelace@example.test"
  }
}
```

```json
{
  "course_enrollments": [],
  "exam_enrollments": []
}
```

```json
{
  "authenticated": true,
  "expires_at": "2026-06-01T12:00:00+00:00",
  "expired": false
}
```

For errors, keep the first contract simple:

```json
{
  "error": {
    "code": "not_authenticated",
    "message": "Not logged in. Run 'tudelft login' first."
  }
}
```

The CLI can still print human errors by default. JSON mode should emit JSON on
stdout and reserve stderr for diagnostics that are not part of the contract.

## TypeScript Client Contract

`frontend/src/client/pythonCli.ts` should be the only module allowed to spawn
Python commands.

Responsibilities:

- Resolve the command from `TUDELFT_CLI_BIN` or default to `tudelft`.
- Use `execFile`, not shell string execution.
- Pass explicit argument arrays.
- Set a reasonable timeout per command.
- Parse stdout as JSON.
- Convert non-zero exits into typed frontend errors.
- Detect non-JSON stdout and report a contract error.
- Never inspect session files or portal tokens directly.

Example API shape:

```ts
export interface PythonCliClient {
  authStatus(): Promise<AuthStatus>;
  whoami(): Promise<StudentProfile>;
  ec(): Promise<EcProgress>;
  grades(options?: { finalOnly?: boolean }): Promise<GradesResult>;
  enrollments(options?: { courses?: boolean; exams?: boolean }): Promise<EnrollmentsResult>;
}
```

## Risks

- JSON output drift: public commands may change shape unless contract tests pin
  the payloads.
- Subprocess latency: dashboard refresh may feel slow if it spawns several
  commands. Mitigate with concurrent calls first; add hidden batched RPC only if
  measured latency is poor.
- Authentication UX: `tudelft login` opens a browser and should stay in Python.
  The TUI can show "not logged in" and offer to run login later, but should not
  implement auth itself.
- Error normalization: current Typer commands print human errors. JSON mode must
  become machine-readable for the TUI.
- Packaging: Python and Node install flows can confuse users if introduced all
  at once. Keep `tudelft-tui` optional until useful.
- Enrollment safety: mutation flows need explicit confirmations, dry-run/result
  contracts, and careful tests before becoming interactive TUI actions.

## Implementation Checklist

First backend contract MR:

- Add `--output json` to `whoami`. Done.
- Add `--output json` to `enrollments`. Done.
- Add read-only auth status command with `--output json`. Done as `tudelft status`.
- Add JSON error helper for machine-readable error responses in JSON mode.
- Add contract tests for all JSON payloads consumed by the TUI.
- Keep existing Typer/Rich human output unchanged.

First frontend scaffold MR:

- Add `frontend/package.json`, TypeScript config, and Ink dependencies.
- Add `frontend/src/client/pythonCli.ts`.
- Add contract TypeScript interfaces matching the documented JSON shapes.
- Add a minimal `DashboardScreen` that renders mocked data in tests.
- Add a development script that runs `tudelft-tui` locally.

First usable TUI MR:

- Load auth status, profile, EC progress, grades, and enrollments through
  `pythonCli.ts`.
- Render read-only dashboard.
- Add refresh and quit keys.
- Add loading, empty, unauthenticated, and error states.
- Add TypeScript tests for the subprocess client and dashboard rendering.
- Update README with optional TUI development instructions.

Decision points after milestone one:

- If subprocess startup is acceptable, continue with public JSON contracts.
- If dashboard refresh is slow, add a hidden Python `tudelft _rpc dashboard`
  command that batches read-only data.
- If rendering complexity grows beyond Ink's comfort zone, re-evaluate OpenTUI
  with measured UI requirements.
