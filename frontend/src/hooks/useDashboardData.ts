import {useCallback, useEffect, useState} from 'react';

import {
  getEcProgress,
  getGrades,
  getProfile,
  getStatus
} from '../client/pythonCli.js';
import type {
  EcResponse,
  GradesResponse,
  ProfileResponse,
  StatusResponse
} from '../types/contracts.js';

export type ResourceState<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
};

export type DashboardData = {
  status: ResourceState<StatusResponse>;
  profile: ResourceState<ProfileResponse>;
  ec: ResourceState<EcResponse>;
  grades: ResourceState<GradesResponse>;
  refresh: () => void;
  refreshing: boolean;
};

const emptyResource = <T>(): ResourceState<T> => ({
  data: null,
  error: null,
  loading: true
});

export function useDashboardData(): DashboardData {
  const [refreshKey, setRefreshKey] = useState(0);
  const [status, setStatus] = useState<ResourceState<StatusResponse>>(emptyResource);
  const [profile, setProfile] = useState<ResourceState<ProfileResponse>>(emptyResource);
  const [ec, setEc] = useState<ResourceState<EcResponse>>(emptyResource);
  const [grades, setGrades] = useState<ResourceState<GradesResponse>>(emptyResource);

  const refresh = useCallback(() => {
    setRefreshKey((key) => key + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const load = <T>(
      request: () => Promise<T>,
      setResource: React.Dispatch<React.SetStateAction<ResourceState<T>>>
    ) => {
      setResource((current) => ({...current, error: null, loading: true}));

      request()
        .then((data) => {
          if (!cancelled) {
            setResource({data, error: null, loading: false});
          }
        })
        .catch((error: unknown) => {
          if (!cancelled) {
            setResource((current) => ({
              data: current.data,
              error: errorMessage(error),
              loading: false
            }));
          }
        });
    };

    load(getStatus, setStatus);
    load(getProfile, setProfile);
    load(getEcProgress, setEc);
    load(getGrades, setGrades);

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const refreshing = status.loading || profile.loading || ec.loading || grades.loading;

  return {
    status,
    profile,
    ec,
    grades,
    refresh,
    refreshing
  };
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return String(error);
}
