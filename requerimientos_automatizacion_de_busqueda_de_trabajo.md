# Automatización de Búsqueda de Trabajo

## Descripción del Sistema

Este sistema tiene como objetivo la automatización de la búsqueda periódica de ofertas de trabajo en una lista de fuentes definidas y su puntuación para la evaluación de su compatibilidad con un perfil profesional definido. Con ayuda de un análisis de compatibilidad hecho por medio de IA el sistema debe ser capaz de elegir las propuestas que son más compatibles con el perfil (la puntuación supera un cierto umbral) y organizarlas en una estructura de datos que le permita al usuario final por medio de una interfaz web leer personalmente cada una de las ofertas de trabajo filtradas y decidir si las quiere eliminar o pasar a un proceso de postulación a esa empresa (marcando un campo en la estructura de datos elegida).

## Requerimientos del Sistema

1. El sistema debe tener un único punto de entrada para lanzar todo el proceso de búsqueda automática  
   1. El sistema se debe poder iniciar por medio de un cronjob para que se ejecute con la frecuencia requerida por el usuario  
   2. El sistema se debe poder iniciar enviando un comando desde la interfaz Web  
2. El sistema cuenta con una interfaz Web donde el usuario puede interactuar con el sistema  
   1. La interfaz Web provee una visualización estructurada de las ofertas de trabajo con información como:  
      1. Título del puesto (ej. "Embedded Systems Engineer")  
      2. Empresa  
      3. Ubicación (ciudad, país, remoto/híbrido/presencial)  
      4. Fecha de publicación  
      5. URL/fuente de la oferta  
      6. Departamento o equipo (ej. "Avionics Platform & Cockpit Systems")  
      7. Descripción general / resumen del puesto  
      8. Responsabilidades (lo que harás día a día)  
      9. Objetivos del rol (qué se espera lograr, a veces ligado a un proyecto específico)  
      10. Años de experiencia mínimos/preferidos  
      11. Nivel educativo (licenciatura, maestría, doctorado)  
      12. Habilidades técnicas obligatorias (lenguajes, frameworks, herramientas)  
      13. Habilidades técnicas deseables ("nice to have")  
      14. Idiomas requeridos y nivel  
      15. Tipo de contrato (CDI, CDD, stage, freelance, full-time, part-time)  
      16. Contacto de RRHH o reclutador (si está disponible)  
   2. La interfaz Web permite marcar ofertas para indicar que ya se empezó un proceso de postulación con ellas  
   3. La interfaz permite eliminar ofertas de trabajo manualmente que no sea interesantes para el usuario  
   4. La interfaz permite por medio de un link que el usuario pueda ir directamente a la página de la oferta de trabajo  
   5. La interfaz permite que el usuario ingrese un link directo donde se encuentra una oferta de trabajo pública para que el sistema la pueda procesar como lo haría con otras ofertas de trabajo  
3. El sistema debe contar con un método de identificación para cada oferta  
4. El sistema debe evitar análisis de textos de ofertas de trabajo que ya se hayan identificado antes (esto para evitar el posible uso de tokens de la IA innecesariamente)  
5. El sistema debe ser capaz de obtener las ofertas de trabajo desde diferentes fuentes como correos, sitios de búsqueda de ofertas de trabajo manejados por cada empresa  
   1. El sistema debe ser capaz de acceder al correo del usuario, identificar los correos de alertas de plataformas como LinkedIn o Indeed y seguir el link para obtener toda la información de la oferta de trabajo por medio de un navegador en el que el usuario ha hecho previamente login en estas plataformas para evitar bloqueos por acceso  
   2. El sistema debe ser capaz de ingresar a plataformas de búsqueda de trabajo de cada empresa para que por medio de un navegador pueda obtener la información y procesarla. Las fuentes de estas herramientas serán configuradas previamente como links http con los parámetros ya configurados para que la página liste únicamente las ofertas en las cuales el usuario está interesado

