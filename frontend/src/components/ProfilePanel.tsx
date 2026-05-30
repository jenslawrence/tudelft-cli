import {Box, Text} from 'ink';

import type {ResourceState} from '../hooks/useDashboardData.js';
import type {ProfileResponse} from '../types/contracts.js';

type Props = {
  profile: ResourceState<ProfileResponse>;
};

export function ProfilePanel({profile}: Props) {
  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text bold>Profile</Text>
      {profile.loading && <Text color="yellow">Loading profile...</Text>}
      {profile.error && (
        <>
          <Text color="red">Failed to load profile:</Text>
          <Text color="red">{profile.error}</Text>
        </>
      )}
      {!profile.loading && !profile.error && profile.data && (
        <>
          <Text>{value(profile.data.profile.name)}</Text>
          <Text>Student number: {value(profile.data.profile.student_number)}</Text>
          <Text dimColor>Email: {value(profile.data.profile.email)}</Text>
        </>
      )}
    </Box>
  );
}

function value(input: string | null): string {
  if (!input) {
    return '-';
  }

  return input;
}
