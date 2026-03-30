CREATE TYPE doclynk_user_role AS ENUM ('doctor', 'patient');
CREATE TYPE doclynk_appointment_status AS ENUM ('pending', 'approved', 'rejected', 'cancelled');

CREATE TABLE IF NOT EXISTS doclynk_users (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role doclynk_user_role NOT NULL,
    specialization VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_doclynk_users_email ON doclynk_users(email);

CREATE TABLE IF NOT EXISTS doclynk_appointments (
    id BIGSERIAL PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES doclynk_users(id) ON DELETE CASCADE,
    doctor_id BIGINT NOT NULL REFERENCES doclynk_users(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMPTZ NOT NULL,
    reason TEXT,
    status doclynk_appointment_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_doclynk_appointments_doctor_id ON doclynk_appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_doclynk_appointments_patient_id ON doclynk_appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_doclynk_appointments_scheduled_at ON doclynk_appointments(scheduled_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_doctor_active_slot
    ON doclynk_appointments(doctor_id, scheduled_at)
    WHERE status IN ('pending', 'approved');
