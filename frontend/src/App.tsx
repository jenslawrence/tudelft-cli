import {Box, Text, useApp, useInput} from 'ink';

import {GradesPanel} from './components/GradesPanel.js';
import {ProfilePanel} from './components/ProfilePanel.js';
import {ProgressPanel} from './components/ProgressPanel.js';
import {StatusPanel} from './components/StatusPanel.js';
import {useDashboardData} from './hooks/useDashboardData.js';

export function App() {
  const {exit} = useApp();
  const dashboard = useDashboardData();

  useInput((input) => {
    if (input === 'q') {
      exit();
    }

    if (input === 'r') {
      dashboard.refresh();
    }
  });

  return (
    <Box flexDirection="column" borderStyle="single" borderColor="cyan" paddingX={1}>
      <Box marginBottom={1}>
        <Text bold>TU Delft Dashboard</Text>
        <Text dimColor>  q quit  r refresh</Text>
        {dashboard.refreshing && <Text color="yellow">  refreshing</Text>}
      </Box>
      <StatusPanel status={dashboard.status} />
      <ProfilePanel profile={dashboard.profile} />
      <ProgressPanel ec={dashboard.ec} />
      <GradesPanel grades={dashboard.grades} />
    </Box>
  );
}
