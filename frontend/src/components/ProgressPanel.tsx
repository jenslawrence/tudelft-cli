import {Box, Text} from 'ink';

import type {ResourceState} from '../hooks/useDashboardData.js';
import type {EcResponse} from '../types/contracts.js';

type Props = {
  ec: ResourceState<EcResponse>;
};

export function ProgressPanel({ec}: Props) {
  const item = ec.data?.items[0];

  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text bold>EC Progress</Text>
      {ec.loading && <Text color="yellow">Loading EC progress...</Text>}
      {ec.error && (
        <>
          <Text color="red">Failed to load EC progress:</Text>
          <Text color="red">{ec.error}</Text>
        </>
      )}
      {!ec.loading && !ec.error && !item && <Text>No EC progress available.</Text>}
      {!ec.loading && !ec.error && item && (
        <>
          <Text>
            {value(item.earned_ec)} / {value(item.required_ec)} EC
            {item.percentage !== null ? ` (${item.percentage}%)` : ''}
          </Text>
          <Text dimColor>
            {item.programme_name} - {item.phase_description}
          </Text>
        </>
      )}
    </Box>
  );
}

function value(input: number | null): string {
  if (input === null) {
    return '-';
  }

  return String(input);
}
