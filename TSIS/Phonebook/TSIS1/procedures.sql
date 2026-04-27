-- ============================================================
-- TSIS1 — New Stored Procedures & Functions
-- (Procedures from Practice 8 are NOT duplicated here)
-- ============================================================

-- 1. add_phone: add a phone number to an existing contact
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR   -- 'home', 'work', or 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE username = p_contact_name;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;

    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type "%". Must be home, work, or mobile', p_type;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);

    RAISE NOTICE 'Phone % (%) added to contact "%"', p_phone, p_type, p_contact_name;
END;
$$;


-- 2. move_to_group: assign a contact to a group, creating the group if needed
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id   INTEGER;
    v_contact_id INTEGER;
BEGIN
    -- Get or create group
    SELECT id INTO v_group_id
    FROM groups
    WHERE name = p_group_name;

    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group_name)
        RETURNING id INTO v_group_id;
        RAISE NOTICE 'Group "%" created', p_group_name;
    END IF;

    -- Find contact
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE username = p_contact_name;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;

    UPDATE contacts
    SET group_id = v_group_id
    WHERE id = v_contact_id;

    RAISE NOTICE 'Contact "%" moved to group "%"', p_contact_name, p_group_name;
END;
$$;


-- 3. search_contacts: full-field search (name, email, all phones)
--    Extends the Practice 8 get_contacts_by_pattern to cover the new schema.
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    contact_id  INTEGER,
    username    VARCHAR,
    email       VARCHAR,
    birthday    DATE,
    group_name  VARCHAR,
    phone       VARCHAR,
    phone_type  VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (c.id, ph.phone)
        c.id,
        c.username,
        c.email,
        c.birthday,
        g.name  AS group_name,
        ph.phone,
        ph.type AS phone_type
    FROM contacts c
    LEFT JOIN groups g  ON g.id  = c.group_id
    LEFT JOIN phones ph ON ph.contact_id = c.id
    WHERE
        c.username ILIKE '%' || p_query || '%'
        OR c.email  ILIKE '%' || p_query || '%'
        OR ph.phone ILIKE '%' || p_query || '%'
    ORDER BY c.id, ph.phone;
END;
$$ LANGUAGE plpgsql;
