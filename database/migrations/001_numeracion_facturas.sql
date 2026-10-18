-- Ejecutar primero en la base de pruebas.
USE motonorte_test;

-- Cerrar todas las ventanas de Moto Norte antes de ejecutar.
-- Esta actualización no elimina ventas existentes.

CREATE TABLE IF NOT EXISTS numeracion_facturas (
    prefijo VARCHAR(10) NOT NULL,
    ultimo_numero BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (prefijo)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

START TRANSACTION;

-- Crear el contador si todavía no existe.
INSERT INTO numeracion_facturas (prefijo, ultimo_numero)
VALUES ('MN', 0)
ON DUPLICATE KEY UPDATE prefijo = 'MN';

-- Continuar desde la mayor factura existente.
-- Si se repite el script, el contador nunca disminuye.
UPDATE numeracion_facturas
SET ultimo_numero = GREATEST(
    ultimo_numero,
    (
        SELECT COALESCE(
            MAX(CAST(SUBSTRING(num_factura, 3) AS UNSIGNED)),
            0
        )
        FROM ventas
        WHERE num_factura REGEXP '^MN[0-9]+$'
    )
)
WHERE prefijo = 'MN';

COMMIT;

SELECT prefijo, ultimo_numero
FROM numeracion_facturas;