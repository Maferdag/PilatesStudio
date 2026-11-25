-- Plantilla para crear un administrador en Supabase.
-- Reemplaza ambos valores antes de ejecutar. Genera el hash con Werkzeug
-- usando el procedimiento indicado en la respuesta; no pongas aquí la clave
-- en texto plano ni subas este archivo con valores reales al repositorio.

INSERT INTO public.usuarios (
    correo,
    contrasena_hash,
    rol,
    estado_aprobacion
)
VALUES (
    'admin@pilates.com',
    'scrypt:32768:8:1$UYxqgur7IuxYXHm4$c3f86530877e6715ce7cd0243aa889e2a26f314261551a8d2bce8d41009eee1d42ff815f131c6e8fc23f4a91d49944e576c7b988def800efe2937fa8c871e752',
    'admin',
    'aprobado'
);
