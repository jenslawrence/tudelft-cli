export type StatusResponse = {
  authenticated: boolean;
  expires_at: string | null;
  expired: boolean | null;
};

export type StudentProfile = {
  name: string;
  student_number: string | null;
  email: string | null;
};

export type ProfileResponse = {
  profile: StudentProfile;
};

export type EcProgressItem = {
  programme_name: string;
  faculty: string | null;
  exam_programme_name: string | null;
  phase_description: string;
  earned_ec: number | null;
  required_ec: number | null;
  percentage: number | null;
  completed: boolean | null;
  other_earned_ec: number | null;
};

export type EcResponse = {
  items: EcProgressItem[];
};

export type GradeItem = {
  course_code: string;
  course_name: string;
  component: string;
  value: string;
  passed: boolean | null;
  published_at: string | null;
};

export type GradesResponse = {
  items: GradeItem[];
};
