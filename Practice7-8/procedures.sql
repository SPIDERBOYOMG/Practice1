CREATE OR REPLACE PROCEDURE upsert_contact(p_username VARCHAR, p_phone VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM contacts WHERE username = p_username) THEN
        UPDATE contacts
        SET phone = p_phone
        WHERE username = p_username;
    ELSE
        INSERT INTO contacts(username, phone)
        VALUES (p_username, p_phone);
    END IF;
END;
$$;


CREATE OR REPLACE PROCEDURE insert_many_contacts(
    p_names TEXT[],
    p_phones TEXT[]
)
LANGUAGE plpgsql AS $$
DECLARE
    i INT;
BEGIN
    IF array_length(p_names, 1) IS NULL OR array_length(p_phones, 1) IS NULL THEN
        RAISE NOTICE 'Empty arrays';
        RETURN;
    END IF;

    IF array_length(p_names, 1) <> array_length(p_phones, 1) THEN
        RAISE EXCEPTION 'Arrays must have the same length';
    END IF;

    FOR i IN 1..array_length(p_names, 1)
    LOOP
        IF p_phones[i] ~ '^87[0-9]{9}$' THEN
            CALL upsert_contact(p_names[i], p_phones[i]);
        ELSE
            RAISE NOTICE 'Invalid phone: %, name: %', p_phones[i], p_names[i];
        END IF;
    END LOOP;
END;
$$;


CREATE OR REPLACE PROCEDURE delete_contact(p_value VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM contacts
    WHERE username = p_value OR phone = p_value;
END;
$$;
