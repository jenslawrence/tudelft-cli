import {execFile} from 'node:child_process';

import type {
  EcResponse,
  GradesResponse,
  ProfileResponse,
  StatusResponse
} from '../types/contracts.js';

const DEFAULT_TIMEOUT_MS = 30_000;
const TUDELFT_BIN = process.env.TUDELFT_CLI_BIN ?? 'tudelft';

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
  const args = [command, '--output', 'json'];
  const displayCommand = `${TUDELFT_BIN} ${args.join(' ')}`;
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  const {stdout} = await execTudelft(args, displayCommand, timeoutMs);

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
  args: string[],
  displayCommand: string,
  timeoutMs: number
): Promise<{stdout: string; stderr: string}> {
  return new Promise((resolve, reject) => {
    execFile(
      TUDELFT_BIN,
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
