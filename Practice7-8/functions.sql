CREATE OR REPLACE FUNCTION get_contacts_by_pattern(p text)
RETURNS TABLE(username VARCHAR, phone VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT c.username, c.phone
    FROM contacts c
    WHERE c.username ILIKE '%' || p || '%' 
    OR c.phone ILIKE '%' || p || '%';
END;
$$ LANGUAGE plpgsql;
CREATE OR REPLACE FUNCTION get_contacts_paginated(p_limit INT, p_offset INT)
RETURNS TABLE(id INT, username VARCHAR, phone VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.username, c.phone
    FROM contacts c
    ORDER BY c.id
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;
