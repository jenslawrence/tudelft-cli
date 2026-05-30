import {execFile} from 'node:child_process';

import type {
  EcResponse,
  GradesResponse,
  ProfileResponse,
  StatusResponse
} from '../types/contracts.js';

const DEFAULT_TIMEOUT_MS = 30_000;
const DEFAULT_TUDELFT_CLI = 'tudelft';

export class PythonCliError extends Error {
  readonly command: string;
  readonly causeType: 'failed' | 'timeout' | 'invalid-json';
  readonly stderr: string;
  readonly stdout: string;
  readonly exitCode: number | null;

  constructor(
    message: string,
    options: {
      command: string;
      causeType: PythonCliError['causeType'];
      stderr?: string;
      stdout?: string;
      exitCode?: number | null;
    }
  ) {
    super(message);
    this.name = 'PythonCliError';
    this.command = options.command;
    this.causeType = options.causeType;
    this.stderr = options.stderr ?? '';
    this.stdout = options.stdout ?? '';
    this.exitCode = options.exitCode ?? null;
  }
}

type CommandName = 'status' | 'whoami' | 'ec' | 'grades';

export async function runCommand<T>(
  command: CommandName,
  options: {timeoutMs?: number} = {}
): Promise<T> {
  const cli = resolveCliCommand();
  const args = [...cli.args, command, '--output', 'json'];
  const displayCommand = [...cli.displayTokens, command, '--output', 'json'].join(' ');
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  const {stdout} = await execTudelft(cli.executable, args, displayCommand, timeoutMs);

  try {
    return JSON.parse(stdout) as T;
  } catch {
    throw new PythonCliError(
      `Invalid JSON returned by ${displayCommand}.`,
      {
        command: displayCommand,
        causeType: 'invalid-json',
        stdout
      }
    );
  }
}

export function getStatus(): Promise<StatusResponse> {
  return runCommand<StatusResponse>('status');
}

export function getProfile(): Promise<ProfileResponse> {
  return runCommand<ProfileResponse>('whoami');
}

export function getEcProgress(): Promise<EcResponse> {
  return runCommand<EcResponse>('ec');
}

export function getGrades(): Promise<GradesResponse> {
  return runCommand<GradesResponse>('grades');
}

function execTudelft(
  executable: string,
  args: string[],
  displayCommand: string,
  timeoutMs: number
): Promise<{stdout: string; stderr: string}> {
  return new Promise((resolve, reject) => {
    execFile(
      executable,
      args,
      {
        encoding: 'utf8',
        timeout: timeoutMs,
        windowsHide: true,
        maxBuffer: 1024 * 1024
      },
      (error, stdout, stderr) => {
        if (!error) {
          resolve({stdout, stderr});
          return;
        }

        const nodeError = error as NodeJS.ErrnoException & {
          code?: string | number | null;
          killed?: boolean;
          signal?: NodeJS.Signals | null;
        };
        const timedOut = nodeError.killed === true || nodeError.signal === 'SIGTERM';
        const trimmedStderr = stderr.trim();
        const trimmedStdout = stdout.trim();

        reject(
          new PythonCliError(
            timedOut
              ? `${displayCommand} timed out after ${timeoutMs}ms.`
              : commandFailureMessage(
                  displayCommand,
                  trimmedStderr,
                  trimmedStdout,
                  nodeError.message
                ),
            {
              command: displayCommand,
              causeType: timedOut ? 'timeout' : 'failed',
              stderr,
              stdout,
              exitCode: typeof nodeError.code === 'number' ? nodeError.code : null
            }
          )
        );
      }
    );
  });
}

function resolveCliCommand(): {
  executable: string;
  args: string[];
  displayTokens: string[];
} {
  const configuredCommand = process.env.TUDELFT_CLI?.trim() || DEFAULT_TUDELFT_CLI;
  const tokens = parseCommand(configuredCommand);

  if (tokens.length === 0) {
    return {
      executable: DEFAULT_TUDELFT_CLI,
      args: [],
      displayTokens: [DEFAULT_TUDELFT_CLI]
    };
  }

  const [executable, ...args] = tokens;
  return {
    executable,
    args,
    displayTokens: tokens
  };
}

function parseCommand(command: string): string[] {
  const tokens: string[] = [];
  let token = '';
  let quote: '"' | "'" | null = null;
  let escaping = false;

  for (const character of command) {
    if (escaping) {
      token += character;
      escaping = false;
      continue;
    }

    if (character === '\\') {
      escaping = true;
      continue;
    }

    if (quote) {
      if (character === quote) {
        quote = null;
      } else {
        token += character;
      }
      continue;
    }

    if (character === '"' || character === "'") {
      quote = character;
      continue;
    }

    if (/\s/.test(character)) {
      if (token.length > 0) {
        tokens.push(token);
        token = '';
      }
      continue;
    }

    token += character;
  }

  if (escaping) {
    token += '\\';
  }

  if (token.length > 0) {
    tokens.push(token);
  }

  return tokens;
}

function commandFailureMessage(
  displayCommand: string,
  stderr: string,
  stdout: string,
  errorMessage: string
): string {
  const details = stderr || stdout || errorMessage;
  if (!details) {
    return `${displayCommand} failed.`;
  }

  return `${displayCommand} failed: ${details}`;
}
