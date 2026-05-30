import {Box, Text} from 'ink';

import type {ResourceState} from '../hooks/useDashboardData.js';
import type {StatusResponse} from '../types/contracts.js';

type Props = {
  status: ResourceState<StatusResponse>;
};

export function StatusPanel({status}: Props) {
  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text bold>Auth Status</Text>
      {status.loading && <Text color="yellow">Loading status...</Text>}
      {status.error && (
        <>
          <Text color="red">Failed to load status:</Text>
          <Text color="red">{status.error}</Text>
        </>
      )}
      {!status.loading && !status.error && status.data && (
        <>
          <Text>{status.data.authenticated ? 'Logged in' : 'Not logged in'}</Text>
          <Text dimColor>Expires: {status.data.expires_at ?? '-'}</Text>
        </>
      )}
    </Box>
  );
}
