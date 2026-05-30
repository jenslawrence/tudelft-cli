import {Box, Text} from 'ink';

import type {ResourceState} from '../hooks/useDashboardData.js';
import type {GradesResponse} from '../types/contracts.js';

type Props = {
  grades: ResourceState<GradesResponse>;
};

export function GradesPanel({grades}: Props) {
  const items = grades.data?.items.slice(0, 5) ?? [];

  return (
    <Box flexDirection="column">
      <Text bold>Recent Grades</Text>
      {grades.loading && <Text color="yellow">Loading grades...</Text>}
      {grades.error && (
        <>
          <Text color="red">Failed to load grades:</Text>
          <Text color="red">{grades.error}</Text>
        </>
      )}
      {!grades.loading && !grades.error && items.length === 0 && (
        <Text>No grades available.</Text>
      )}
      {!grades.loading &&
        !grades.error &&
        items.map((grade) => (
          <Text key={`${grade.course_code}-${grade.component}-${grade.published_at ?? ''}`}>
            {grade.course_code} {grade.value} {grade.course_name} ({grade.component})
          </Text>
        ))}
    </Box>
  );
}
