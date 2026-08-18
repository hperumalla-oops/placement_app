-- Enums
CREATE TYPE user_role AS ENUM
('STUDENT', 'SPC', 'ADMIN');
CREATE TYPE drive_type AS ENUM
('SUMMER_INTERNSHIP', 'FULL_TIME_ONLY', 'INTERNSHIP_PLUS_FULL_TIME');
CREATE TYPE conversion_type AS ENUM
('PBC', 'FTE', '6_MONTH_PBC', '6_MONTH_FTE', '6_MONTH_FTE/PBC', 'INTERNSHIP_ONLY');
CREATE TYPE application_status AS ENUM
('APPLIED', 'OA_SHORTLISTED', 'INTERVIEW_SHORTLISTED', 'SELECTED', 'REJECTED');
CREATE TYPE oa_mode AS ENUM
('VIRTUAL', 'IN_PERSON');
CREATE TYPE process_mode AS ENUM
('VIRTUAL', 'IN_PERSON', 'HYBRID');

-- users
CREATE TABLE users
(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    role user_role NOT NULL DEFAULT 'STUDENT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- students (NOTE: uses id as PK + usn as a unique column, matching the
-- code as delivered — NOT the spec's "usn as PK" description. See the
-- README "Known gaps" section.)
CREATE TABLE students
(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    usn TEXT UNIQUE NOT NULL,
    branch TEXT NOT NULL,
    date_of_birth DATE,
    graduation_year INTEGER NOT NULL,
    tenth_percentage NUMERIC(5,2),
    twelfth_percentage NUMERIC(5,2),
    cgpa NUMERIC(4,2),
    backlogs INTEGER NOT NULL DEFAULT 0,
    resume_url TEXT,
    profile_frozen BOOLEAN NOT NULL DEFAULT FALSE,
    cgpa_unlocked_until TIMESTAMPTZ,
    backlogs_unlocked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT students_tenth_percentage_check CHECK (tenth_percentage IS NULL OR (tenth_percentage >= 0 AND tenth_percentage <= 100)),
    CONSTRAINT students_twelfth_percentage_check CHECK (twelfth_percentage IS NULL OR (twelfth_percentage >= 0 AND twelfth_percentage <= 100)),
    CONSTRAINT students_cgpa_check CHECK (cgpa IS NULL OR (cgpa >= 0 AND cgpa <= 10)),
    CONSTRAINT students_backlogs_check CHECK (backlogs >= 0)
);

-- companies
CREATE TABLE companies
(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- drives
CREATE TABLE drives
(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    drive_type drive_type NOT NULL,
    conversion_type conversion_type,
    target_graduation_year INTEGER NOT NULL,
    stipend NUMERIC(10,2),
    ctc NUMERIC(12,2),
    location TEXT,
    ppt_datetime TIMESTAMPTZ,
    oa_datetime TIMESTAMPTZ,
    oa_deadline TIMESTAMPTZ NOT NULL,
    oa_mode oa_mode,
    process_mode process_mode,
    minimum_cgpa NUMERIC(4,2),
    maximum_backlogs INTEGER NOT NULL DEFAULT 0,
    type_placement_policy TEXT,
    job_description_url TEXT,
    additional_announcements TEXT,
    published BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT drives_minimum_cgpa_check CHECK (minimum_cgpa IS NULL OR (minimum_cgpa >= 0 AND minimum_cgpa <= 10)),
    CONSTRAINT drives_maximum_backlogs_check CHECK (maximum_backlogs >= 0),
    CONSTRAINT drives_stipend_check CHECK (stipend IS NULL OR stipend >= 0),
    CONSTRAINT drives_ctc_check CHECK (ctc IS NULL OR ctc >= 0)
);

-- drive_eligible_branches
CREATE TABLE drive_eligible_branches
(
    drive_id UUID NOT NULL REFERENCES drives(id) ON DELETE CASCADE,
    branch TEXT NOT NULL,
    PRIMARY KEY (drive_id, branch)
);

-- applications
CREATE TABLE applications
(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    drive_id UUID NOT NULL REFERENCES drives(id) ON DELETE CASCADE,
    status application_status NOT NULL DEFAULT 'APPLIED',
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT applications_student_id_drive_id_key UNIQUE (student_id, drive_id)
);

-- audit_logs
CREATE TABLE audit_logs
(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
