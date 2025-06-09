from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('biblioteca', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Funciones auxiliares
            CREATE OR REPLACE FUNCTION calc_overdue_fine(p_loan biblioteca_loan)
            RETURNS numeric AS $$
            DECLARE
            overdue_days integer := GREATEST((CURRENT_DATE - p_loan.due_date), 0);
            BEGIN
            RETURN overdue_days * 0.50;
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;

            CREATE OR REPLACE FUNCTION copy_available_count(p_book_id VARCHAR)
            RETURNS INT AS $$
                SELECT COUNT(*) FROM biblioteca_copy c
                WHERE c.book_id = p_book_id AND c.is_available;
            $$ LANGUAGE sql STABLE;

            -- Trigger: actualizar disponibilidad en loans
            CREATE OR REPLACE FUNCTION trg_update_copy_available() RETURNS trigger AS $$
            BEGIN
                IF TG_OP = 'INSERT' THEN
                    UPDATE biblioteca_copy SET is_available = FALSE WHERE id = NEW.copy_id;
                ELSIF TG_OP = 'UPDATE' AND NEW.returned_at IS NOT NULL THEN
                    UPDATE biblioteca_copy SET is_available = TRUE WHERE id = NEW.copy_id;
                END IF;
                RETURN NEW;
            END;$$ LANGUAGE plpgsql;

            CREATE TRIGGER trg_loan_copy
            AFTER INSERT OR UPDATE ON biblioteca_loan
            FOR EACH ROW EXECUTE FUNCTION trg_update_copy_available();

            -- Trigger: generar multa tras devolución
            CREATE OR REPLACE FUNCTION trg_generate_fine() RETURNS trigger AS $$
            BEGIN
                IF EXISTS (SELECT 1 FROM biblioteca_fine WHERE loan_id = NEW.id) 
                THEN RETURN NEW;
                END IF;
                IF NEW.returned_at IS NOT NULL AND NEW.returned_at::date > NEW.due_date THEN
                    INSERT INTO biblioteca_fine(loan_id, amount, created_at, paid)
                    VALUES(NEW.id, calc_overdue_fine(NEW), NOW(), FALSE);
                END IF;
                RETURN NEW;
            END;$$ LANGUAGE plpgsql;

            CREATE TRIGGER trg_fine_after_return
            AFTER UPDATE OF returned_at ON biblioteca_loan
            FOR EACH ROW WHEN (OLD.returned_at IS NULL AND NEW.returned_at IS NOT NULL)
            EXECUTE FUNCTION trg_generate_fine();

            -- Trigger: auditoría de libros
            CREATE OR REPLACE FUNCTION trg_book_audit() RETURNS trigger AS $$
            BEGIN
                INSERT INTO biblioteca_auditlog(table_name, record_id, op, changed_at, change_user)
                VALUES('books', COALESCE(NEW.isbn, OLD.isbn), TG_OP, NOW(), current_user);
                RETURN NEW;
            END;$$ LANGUAGE plpgsql;

            CREATE TRIGGER trg_books_audit
            AFTER INSERT OR UPDATE OR DELETE ON biblioteca_book
            FOR EACH ROW EXECUTE FUNCTION trg_book_audit();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS trg_books_audit ON biblioteca_book;
            DROP FUNCTION IF EXISTS trg_book_audit();
            DROP TRIGGER IF EXISTS trg_fine_after_return ON biblioteca_loan;
            DROP FUNCTION IF EXISTS trg_generate_fine();
            DROP TRIGGER IF EXISTS trg_loan_copy ON biblioteca_loan;
            DROP FUNCTION IF EXISTS trg_update_copy_available();
            DROP FUNCTION IF EXISTS copy_available_count(INT);
            DROP FUNCTION IF EXISTS calc_overdue_fine(biblioteca_loan);
            """,
        ),
    ]
