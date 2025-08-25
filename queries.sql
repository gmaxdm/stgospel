-- Readings and users:
SELECT g.name, au.first_name, au.last_name, au.email, u.role, u.joined, u.deleted, au.last_login
FROM gospel_agreementgroupuser u INNER JOIN gospel_agreementgroup g ON u.group_id = g.id INNER JOIN authuser_user au ON au.id = u.user_id;
