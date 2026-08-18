INSERT INTO users
    (id, email, role)
VALUES
    ('11111111-1111-1111-1111-111111111111', 'spc@test.local', 'SPC'),
    ('22222222-2222-2222-2222-222222222222', 'student@test.local', 'STUDENT');

INSERT INTO students
    (user_id, name, usn, branch, graduation_year, cgpa, backlogs)
VALUES
    ('22222222-2222-2222-2222-222222222222', 'Test Student', '1XX20CS001', 'CSE', 2027, 8.5, 0);