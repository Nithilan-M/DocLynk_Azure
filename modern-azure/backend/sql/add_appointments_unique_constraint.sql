-- Ensure no duplicate rows exist for the same doctor/date/time_slot before adding the unique constraint.
WITH ranked AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY doctor_id, date, time_slot
            ORDER BY id
        ) AS row_num
    FROM appointments
)
DELETE FROM appointments
WHERE id IN (
    SELECT id
    FROM ranked
    WHERE row_num > 1
);

ALTER TABLE appointments
    ADD CONSTRAINT appointments_doctor_id_date_time_slot_key
    UNIQUE (doctor_id, date, time_slot);
