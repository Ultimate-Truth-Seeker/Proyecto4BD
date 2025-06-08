from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('biblioteca', '0002_create_functions_triggers'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
CREATE OR REPLACE VIEW vista_catalogo_libros AS
                SELECT 
                    b.isbn,
                    b.title,
                    CONCAT(a.first_name, ' ', a.last_name) as autor_principal,
                    b.published_year,
                    b.condition,
                    b.page_count,
                    STRING_AGG(DISTINCT g.name, ', ') as generos,
                    STRING_AGG(DISTINCT CONCAT(oa.first_name, ' ', oa.last_name), ', ') as otros_autores,
                    COUNT(DISTINCT c.id) as total_copias,
                    COUNT(DISTINCT CASE WHEN c.is_available = true THEN c.id END) as copias_disponibles,
                    COUNT(DISTINCT r.id) as total_reviews,
                    ROUND(AVG(
                        CASE r.rating 
                            WHEN 'poor' THEN 1
                            WHEN 'average' THEN 2
                            WHEN 'good' THEN 3
                            WHEN 'excellent' THEN 4
                        END
                    ), 2) as rating_promedio,
                    b.created_at,
                    CASE 
                        WHEN COUNT(DISTINCT CASE WHEN c.is_available = true THEN c.id END) > 0 
                        THEN 'Disponible'
                        ELSE 'No disponible'
                    END as estado_disponibilidad
                FROM biblioteca_book b
                LEFT JOIN biblioteca_author a ON b.main_author_id = a.id
                LEFT JOIN biblioteca_bookauthor ba ON b.isbn = ba.book_id
                LEFT JOIN biblioteca_author oa ON ba.author_id = oa.id AND oa.id != b.main_author_id
                LEFT JOIN biblioteca_bookgenre bg ON b.isbn = bg.book_id
                LEFT JOIN biblioteca_genre g ON bg.genre_id = g.id
                LEFT JOIN biblioteca_copy c ON b.isbn = c.book_id
                LEFT JOIN biblioteca_review r ON b.isbn = r.book_id
                GROUP BY 
                    b.isbn, b.title, a.first_name, a.last_name, 
                    b.published_year, b.condition, b.page_count, b.created_at
                ORDER BY b.title;
            """,
            reverse_sql="""
            DROP VIEW IF EXISTS vista_catalogo_libros;
            """,
        ),
        migrations.RunSQL(
            sql="""
CREATE OR REPLACE VIEW vista_prestamos_usuarios AS
                SELECT 
                    u.id as usuario_id,
                    u.username,
                    CONCAT(u.first_name, ' ', u.last_name) as nombre_completo,
                    u.email,
                    u.status as estado_usuario,
                    COUNT(DISTINCT l.id) as total_prestamos,
                    COUNT(DISTINCT CASE WHEN l.returned_at IS NULL THEN l.id END) as prestamos_activos,
                    COUNT(DISTINCT CASE WHEN l.returned_at IS NOT NULL THEN l.id END) as prestamos_devueltos,
                    COUNT(DISTINCT CASE WHEN l.returned_at IS NULL AND l.due_date < CURRENT_DATE THEN l.id END) as prestamos_vencidos,
                    COUNT(DISTINCT f.id) as total_multas,
                    COUNT(DISTINCT CASE WHEN f.paid = false THEN f.id END) as multas_pendientes,
                    COALESCE(SUM(CASE WHEN f.paid = false THEN f.amount ELSE 0 END), 0) as monto_multas_pendientes,
                    COUNT(DISTINCT r.id) as total_reservas,
                    COUNT(DISTINCT CASE WHEN r.expires_at > CURRENT_TIMESTAMP THEN r.id END) as reservas_activas,
                    COUNT(DISTINCT rev.id) as total_reviews,
                    u.date_joined,
                    CASE 
                        WHEN COUNT(DISTINCT CASE WHEN l.returned_at IS NULL AND l.due_date < CURRENT_DATE THEN l.id END) > 0 
                        THEN 'Con retrasos'
                        WHEN COUNT(DISTINCT CASE WHEN f.paid = false THEN f.id END) > 0 
                        THEN 'Con multas'
                        WHEN COUNT(DISTINCT CASE WHEN l.returned_at IS NULL THEN l.id END) > 0 
                        THEN 'Con préstamos'
                        ELSE 'Sin actividad'
                    END as estado_prestamos
                FROM library_users u
                LEFT JOIN biblioteca_loan l ON u.id = l.user_id
                LEFT JOIN biblioteca_fine f ON l.id = f.loan_id
                LEFT JOIN biblioteca_reservation r ON u.id = r.user_id
                LEFT JOIN biblioteca_review rev ON u.id = rev.user_id
                WHERE u.status = 'active'
                GROUP BY 
                    u.id, u.username, u.first_name, u.last_name, 
                    u.email, u.status, u.date_joined
                ORDER BY u.username;
            """,
            reverse_sql="""
            DROP VIEW IF EXISTS vista_prestamos_usuarios;
            """,
        ),
        migrations.RunSQL(
            sql="""
CREATE OR REPLACE VIEW vista_actividad_sucursales AS
                SELECT 
                    br.id as sucursal_id,
                    br.name as nombre_sucursal,
                    br.address,
                    br.phone,
                    COUNT(DISTINCT s.id) as total_estantes,
                    COUNT(DISTINCT c.id) as total_copias,
                    COUNT(DISTINCT CASE WHEN c.is_available = true THEN c.id END) as copias_disponibles,
                    COUNT(DISTINCT CASE WHEN c.is_available = false THEN c.id END) as copias_prestadas,
                    COUNT(DISTINCT l.id) as total_prestamos_historicos,
                    COUNT(DISTINCT CASE WHEN l.returned_at IS NULL THEN l.id END) as prestamos_activos,
                    COUNT(DISTINCT CASE WHEN l.returned_at IS NULL AND l.due_date < CURRENT_DATE THEN l.id END) as prestamos_vencidos,
                    COUNT(DISTINCT e.id) as total_eventos,
                    COUNT(DISTINCT CASE WHEN e.ends_at > CURRENT_TIMESTAMP THEN e.id END) as eventos_futuros,
                    COUNT(DISTINCT ea.id) as total_asistencias_eventos,
                    ROUND(
                        CASE 
                            WHEN COUNT(DISTINCT c.id) > 0 
                            THEN (COUNT(DISTINCT CASE WHEN c.is_available = false THEN c.id END) * 100.0 / COUNT(DISTINCT c.id))
                            ELSE 0 
                        END, 2
                    ) as porcentaje_ocupacion,
                    ROUND(
                        CASE 
                            WHEN COUNT(DISTINCT e.id) > 0 
                            THEN (COUNT(DISTINCT ea.id) * 1.0 / COUNT(DISTINCT e.id))
                            ELSE 0 
                        END, 2
                    ) as promedio_asistencia_eventos,
                    br.created_at,
                    CASE 
                        WHEN COUNT(DISTINCT CASE WHEN c.is_available = false THEN c.id END) * 100.0 / NULLIF(COUNT(DISTINCT c.id), 0) >= 80 
                        THEN 'Alta ocupación'
                        WHEN COUNT(DISTINCT CASE WHEN c.is_available = false THEN c.id END) * 100.0 / NULLIF(COUNT(DISTINCT c.id), 0) >= 50 
                        THEN 'Ocupación media'
                        WHEN COUNT(DISTINCT c.id) > 0 
                        THEN 'Baja ocupación'
                        ELSE 'Sin actividad'
                    END as nivel_actividad
                FROM biblioteca_branch br
                LEFT JOIN biblioteca_shelf s ON br.id = s.branch_id
                LEFT JOIN biblioteca_copy c ON s.id = c.shelf_id
                LEFT JOIN biblioteca_loan l ON c.id = l.copy_id
                LEFT JOIN biblioteca_event e ON br.id = e.branch_id
                LEFT JOIN biblioteca_eventattendance ea ON e.id = ea.event_id
                GROUP BY 
                    br.id, br.name, br.address, br.phone, br.created_at
                ORDER BY br.name;
            """,
            reverse_sql="""
            DROP VIEW IF EXISTS vista_actividad_sucursales;
            """,
        ),
    ]

