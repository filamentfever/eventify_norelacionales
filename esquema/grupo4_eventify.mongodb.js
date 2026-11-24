
//PARTE 1: creación de colecciones con esquemas.
// 1. usuarios
use('eventify_db');
//borrar colección anterior. 
db.usuarios.drop();
// creación colección de usuarios con esquema.
db.createCollection("usuarios", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["rut", "nombre", "email", "telefono", "rol", "fecha_nacimiento", "activo"],
      properties: {
        rut: {
          bsonType: "string",
          pattern: "^[0-9]{7,8}-[0-9kK]$",
          description: "'rut' debe tener formato 12345678-9 (sin puntos, con guion)"
        },
        nombre: { bsonType: "string" },
        email: {
          bsonType: "string",
          pattern: "^[^@ ]+@[^@ ]+\\.[a-z]{2,}$",
          description: "'email' debe tener formato valido (nombre@dominio.cl)"
        },
        telefono: {
          bsonType: "string",
          pattern: "^[0-9]{9}$",
          description: "'telefono' debe tener exactamente 9 digitos"
        },
        rol: { enum: ["cliente", "administrador"] },
        fecha_nacimiento: { bsonType: "date" },
        activo: { bsonType: "bool" }
      }
    }
  },
});

// 2. eventos. 

use('eventify_db');

db.eventos.drop();

db.createCollection("eventos", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["codigo_lugar", "nombre", "categoria", "descripcion", "fecha_evento", "estado", "recinto", "tickets_disponibles"],
      properties: {
        codigo_lugar: { bsonType: "string" },
        nombre: { bsonType: "string" },
        categoria: { bsonType: "string" },
        descripcion: { bsonType: "string" },
        fecha_evento: { bsonType: "date" },
        estado: { enum: ["programado", "finalizado", "cancelado"] },

        // recinto embebido. 
        recinto: {
          bsonType: "object",
          description: "'recinto' debe ser un objeto",
          required: ["nombre", "direccion", "ciudad", "capacidad"],
          properties: {
            nombre: { bsonType: "string" },
            direccion: { bsonType: "string" },
            ciudad: { bsonType: "string" },
            capacidad: { bsonType: "number", minimum: 1 },
            coordenadas: {
              bsonType: "object",
              properties: {
                latitud: { bsonType: "number" },
                longitud: { bsonType: "number" }
              }
            }
          }
        },

        // tickets embebidos. 
        tickets_disponibles: {
          bsonType: "array",
          minItems: 1,
          description: "'tickets_disponibles' debe ser un arreglo de objetos",
          items: {
            bsonType: "object",
            required: ["tipo", "precio", "stock_inicial", "stock_disponible", "es_vip"],
            properties: {
              tipo: { bsonType: "string" },
              precio: { bsonType: "number", minimum: 0 },
              stock_inicial: { bsonType: "number", minimum: 0 },
              stock_disponible: { bsonType: "number", minimum: 0 },
              es_vip: { bsonType: "bool" }
            }
          }
        }
      }
    }
  },
});

// 3. ordenes_compra con referencia eventos y usuarios. 
use('eventify_db');

//borramos colección anterior. 
db.ordenes_compra.drop();

db.createCollection("ordenes_compra", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["usuario_id", "evento_id", "fecha_compra", "estado", "confirmado", "items", "total"],
      properties: {
        // REFERENCIAS (no se copian los datos, solo se guarda el _id)
        usuario_id: {
          bsonType: "objectId",
          description: "referencia al _id de usuarios"
        },
        evento_id: {
          bsonType: "objectId",
          description: "referencia al _id de eventos"
        },
        fecha_compra: { bsonType: "date" },
        estado: { enum: ["pagada", "pendiente", "anulada"] },
        confirmado: { bsonType: "bool" },
        items: {
          bsonType: "array",
          minItems: 1,
          description: "'items' debe ser un arreglo con al menos un elemento",
          items: {
            bsonType: "object",
            required: ["tipo_ticket", "cantidad", "precio_unitario"],
            properties: {
              tipo_ticket: { bsonType: "string" },
              cantidad: { bsonType: "number", minimum: 1 },
              precio_unitario: { bsonType: "number", minimum: 0 }
            }
          }
        },
        total: { bsonType: "number", minimum: 0 }
      }
    }
  },

});

// 4. resenas_evaluaciones con referencias a usuarios y eventos. 
use('eventify_db');

db.resenas_evaluaciones.drop();

db.createCollection("resenas_evaluaciones", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["usuario_id", "evento_id", "puntuacion", "fecha_resena"],
      properties: {
        usuario_id: { bsonType: "objectId" },
        evento_id: { bsonType: "objectId" },
        puntuacion: { bsonType: "number", minimum: 1, maximum: 5 },
        comentario: { bsonType: "string" },
        fecha_resena: { bsonType: "date" }
      }
    }
  },
});


// PARTE 2: CARGA AUTOMATIZADA DE DATOS 
// Se usan arreglos con datos base y un ciclo "for" que arma los
// documentos. 

// 2.1 USUARIOS (50 documentos)
use('eventify_db');

const nombres = ["Carlos", "Francisca", "Rodrigo", "Valentina", "Camila", "Diego", "Daniela", "Felipe", "Javiera", "Ignacio"];
const apellidos1 = ["Mendoza", "Silva", "Morales", "Castro", "Ortiz", "Reyes", "Fuentes", "Rojas", "Lagos", "Espinoza"];
const apellidos2 = ["Rivera", "Vega", "Soto", "Bravo", "Tapia", "Carrasco", "Guzman", "Flores", "Pavez", "Jara"];
const dominios = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com"];
const digitosRut = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "K"];

const listaUsuarios = [];

for (let i = 0; i < 50; i++) {
  const nombre = nombres[i % 10];
  const apellido1 = apellidos1[Math.floor(i / 5) % 10];
  const apellido2 = apellidos2[(i * 3) % 10];

  // Un usuario de cada 20 es administrador (3 en total), el resto son clientes
  let rol = "cliente";
  if (i % 20 === 0) {
    rol = "administrador";
  }

  listaUsuarios.push({
    rut: (10000000 + i * 377123) + "-" + digitosRut[i % 11],
    nombre: nombre + " " + apellido1 + " " + apellido2,
    email: nombre.toLowerCase() + "." + apellido1.toLowerCase() + (i + 1) + "@" + dominios[i % 4],
    telefono: "9" + (10000000 + i * 1731593),
    rol: rol,
    fecha_nacimiento: new Date(Date.UTC(1960 + (i * 7) % 45, i % 12, 1 + (i * 5) % 28)),
    activo: (i % 10 !== 7)   // 5 usuarios inactivos
  });
}

const resUsuarios = db.usuarios.insertMany(listaUsuarios);

const uIds = resUsuarios.insertedIds;



// 2.2 EVENTOS, 2.3 ORDENES y 2.4 RESENAS

use('eventify_db');

// Datos base de los recintos 
const recintos = [
  { codigo: "REC-STGO-01", nombre: "Movistar Arena", direccion: "Av. Tupper 1480", ciudad: "Santiago", capacidad: 17000, latitud: -33.4619, longitud: -70.6625 },
  { codigo: "REC-CONC-01", nombre: "Parque Bicentenario", direccion: "Costanera Poniente s/n", ciudad: "Concepción", capacidad: 50000, latitud: -36.8201, longitud: -73.0044 },
  { codigo: "REC-VALP-01", nombre: "Teatro Municipal de Valparaíso", direccion: "Uruguay 410", ciudad: "Valparaíso", capacidad: 1400, latitud: -33.0450, longitud: -71.6140 },
  { codigo: "REC-STGO-02", nombre: "Espacio Riesco", direccion: "Av. El Salto 5000", ciudad: "Santiago", capacidad: 12000, latitud: -33.3930, longitud: -70.6420 },
  { codigo: "REC-ANTO-01", nombre: "Enjoy Antofagasta", direccion: "Av. Angamos 1455", ciudad: "Antofagasta", capacidad: 1100, latitud: -23.6720, longitud: -70.4010 },
  { codigo: "REC-VINA-01", nombre: "Sporting Club", direccion: "Los Castaños 404", ciudad: "Viña del Mar", capacidad: 8000, latitud: -33.0300, longitud: -71.5500 },
  { codigo: "REC-PMON-01", nombre: "Arena Puerto Montt", direccion: "Egaña 1151", ciudad: "Puerto Montt", capacidad: 5000, latitud: -41.4690, longitud: -72.9420 },
  { codigo: "REC-STGO-03", nombre: "Centro Cultural Estación Mapocho", direccion: "Plaza Garín s/n", ciudad: "Santiago", capacidad: 7000, latitud: -33.4310, longitud: -70.6520 },
  { codigo: "REC-TEMU-01", nombre: "Teatro Municipal de Temuco", direccion: "Av. Pablo Neruda 01380", ciudad: "Temuco", capacidad: 1200, latitud: -38.7330, longitud: -72.6150 },
  { codigo: "REC-IQUI-01", nombre: "Teatro Municipal de Iquique", direccion: "Thompson 911", ciudad: "Iquique", capacidad: 900, latitud: -20.2133, longitud: -70.1527 }
];

// Datos base de los eventos 
const nombresEventos = [
  "Rock Fest Chile",
  "Noche de Pop Latino",
  "Festival de Verano",
  "Electro Sunset",
  "Obra: La Vida es Sueño",
  "Teatro Clásico en Escena",
  "Cumbre de Tecnología e Innovación",
  "Congreso Nacional de Emprendimiento",
  "Stand-Up Comedy Tour",
  "Torneo Gamer Pro League"
];
const categorias = ["Concierto", "Concierto", "Festival", "Festival", "Teatro", "Teatro", "Conferencia", "Conferencia", "Comedia", "E-Sports"];
const descripciones = [
  "Festival de rock con bandas nacionales e internacionales.",
  "Gran noche de pop latino con artistas de la región.",
  "Música, gastronomía y actividades al aire libre.",
  "Festival de música electrónica con DJs internacionales.",
  "Montaje teatral de una obra clásica con elenco nacional.",
  "Ciclo de teatro clásico con compañías invitadas.",
  "Charlas y talleres sobre tecnología, startups e inteligencia artificial.",
  "Encuentro de emprendedores, inversionistas y mentores.",
  "Show humorístico con los mejores comediantes del país.",
  "Finales nacionales de videojuegos competitivos en vivo."
];

// Estados de evento
const estadosEvento = ["finalizado", "programado", "finalizado", "programado", "programado", "finalizado", "programado", "finalizado", "cancelado", "programado"];

// Datos base para ordenes y resenas
const estadosOrden = ["pagada", "pagada", "pendiente", "pagada", "anulada"];
const puntuaciones = [5, 4, 5, 3, 4, 5, 2, 4, 5, 1];
const comentarios = [
  "Excelente evento, volvería a ir sin dudarlo.",
  "Muy buena organización, aunque las filas de acceso fueron lentas.",
  "Increíble experiencia, el sonido y la producción fueron de primer nivel.",
  "Estuvo bien, pero la visibilidad desde mi ubicación no fue la mejor.",
  "Buen ambiente y buen show, el recinto es cómodo.",
  "Lo mejor del año, totalmente recomendable.",
  "Esperaba más, hubo retrasos en el inicio del evento.",
  "Muy entretenido y con buena relación precio calidad.",
  "Todo perfecto, personal amable y buena seguridad.",
  "Mala experiencia, problemas con el ingreso y poca información."
];



const hoy = Date.now(); 
const unDia = 24 * 60 * 60 * 1000;

const listaEventos = [];
const listaOrdenes = [];
const listaResenas = [];

for (let e = 0; e < 50; e++) {
  const bloque = Math.floor(e / 10);
  const recinto = recintos[(e + bloque) % 10];
  const estado = estadosEvento[(e + bloque * 3) % 10];

  let fechaEvento;
  if (estado === "finalizado") {
    fechaEvento = new Date(Date.UTC(2026, e % 9, 5 + (e % 20), 20, 0, 0));
  } else {
    fechaEvento = new Date(hoy + (10 + e * 4) * unDia + 20 * 60 * 60 * 1000);
  }

  // Precios y stock (cupo de entradas asignado a Eventify para la venta)
  const precioGeneral = 8000 + (e % 8) * 4000;
  const stockGeneral = 15 + (e % 6) * 5;
  const stockVip = 4 + (e % 4) * 2;

  listaEventos.push({
    _id: new ObjectId(),   // se crea aqui para poder usarlo como referencia en las ordenes
    codigo_lugar: recinto.codigo,
    nombre: nombresEventos[e % 10] + " Vol. " + (bloque + 1),
    categoria: categorias[e % 10],
    descripcion: descripciones[e % 10],
    fecha_evento: fechaEvento,
    estado: estado,
    recinto: {
      nombre: recinto.nombre,
      direccion: recinto.direccion,
      ciudad: recinto.ciudad,
      capacidad: recinto.capacidad,
      coordenadas: { latitud: recinto.latitud, longitud: recinto.longitud }
    },
    tickets_disponibles: [
      { tipo: "General", precio: precioGeneral, stock_inicial: stockGeneral, stock_disponible: stockGeneral, es_vip: false },
      { tipo: "VIP", precio: precioGeneral * 2, stock_inicial: stockVip, stock_disponible: stockVip, es_vip: true }
    ]
  });
}

// ----- Paso B: armar las ordenes (y las resenas) de cada evento -----
for (let e = 0; e < 50; e++) {
  const evento = listaEventos[e];
  const general = evento.tickets_disponibles[0];
  const vip = evento.tickets_disponibles[1];
  const cantidadOrdenes = 6 + (e % 5);   // entre 6 y 10 ordenes por evento

  for (let o = 0; o < cantidadOrdenes; o++) {
    // Tipo de compra: 0 = solo General, 1 = solo VIP, 2 = General + VIP
    const tipoCompra = o % 3;
    let cantGeneral = 0;
    let cantVip = 0;
    if (tipoCompra === 0 || tipoCompra === 2) {
      cantGeneral = 1 + (e + o) % 3;
    }
    if (tipoCompra === 1 || tipoCompra === 2) {
      cantVip = 1 + (e + o) % 2;
    }

    // Estado de la orden (las de eventos cancelados quedan anuladas)
    let estado = estadosOrden[o % 5];
    if (evento.estado === "cancelado") {
      estado = "anulada";
    }
    // Si ya no queda stock, la orden no se puede pagar: queda pendiente
    if (estado === "pagada" && (cantGeneral > general.stock_disponible || cantVip > vip.stock_disponible)) {
      estado = "pendiente";
    }
    // Solo las ordenes pagadas descuentan stock
    if (estado === "pagada") {
      general.stock_disponible = general.stock_disponible - cantGeneral;
      vip.stock_disponible = vip.stock_disponible - cantVip;
    }

    // Items comprados
    const items = [];
    if (cantGeneral > 0) {
      items.push({ tipo_ticket: "General", cantidad: cantGeneral, precio_unitario: general.precio });
    }
    if (cantVip > 0) {
      items.push({ tipo_ticket: "VIP", cantidad: cantVip, precio_unitario: vip.precio });
    }
    const total = cantGeneral * general.precio + cantVip * vip.precio;

    // Fecha de compra: siempre antes del evento y antes de "hoy"
    let fechaCompra;
    if (evento.estado === "finalizado") {
      fechaCompra = new Date(evento.fecha_evento.getTime() - (3 + (o * 5) % 40) * unDia);
    } else {
      fechaCompra = new Date(hoy - (1 + (o * 3 + e) % 60) * unDia + 15 * 60 * 60 * 1000);
    }

    // Usuario que compra (se reparten las compras entre los 50 usuarios)
    const idUsuario = uIds[(e + o * 7) % 50];

    listaOrdenes.push({
      usuario_id: idUsuario,
      evento_id: evento._id,
      fecha_compra: fechaCompra,
      estado: estado,
      confirmado: (estado === "pagada"),
      items: items,
      total: total
    });

    // Resena: solo si la orden esta pagada y el evento ya finalizo
    if (estado === "pagada" && evento.estado === "finalizado") {
      listaResenas.push({
        usuario_id: idUsuario,
        evento_id: evento._id,
        puntuacion: puntuaciones[(e + o * 3) % 10],
        comentario: comentarios[(e + o * 3) % 10],
        fecha_resena: new Date(evento.fecha_evento.getTime() + (1 + o % 5) * unDia)
      });
    }
  }
}

use('eventify_db');
db.eventos.insertMany(listaEventos);

use('eventify_db');
db.ordenes_compra.insertMany(listaOrdenes);

use('eventify_db');
db.resenas_evaluaciones.insertMany(listaResenas);


use('eventify_db');
db.usuarios.findOne({rut : '10754246-2'});

// PARTE 3: consultas:3


// CONSULTA 1: Detalle de compras de un usuario ($lookup + $unwind)
// Une la orden con su evento, desglosa los items comprados y calcula
// el gasto total del usuario en los eventos de una ciudad.

use('eventify_db');

//datos que usaremos para ver 
const rutUsuario = "10754246-2";
const ciudadConsulta1 = "Temuco";

// buscar el _id del usuario por su rut.
const idUsuarioConsulta = db.usuarios.findOne({ rut: rutUsuario })._id;

// buscar por su rut y ordenes pagadas. 
use('eventify_db');
db.ordenes_compra.aggregate([
  { $match: { usuario_id: idUsuarioConsulta, estado: "pagada" } },
  {
    $lookup: { from: "eventos", 
      localField: "evento_id", 
      foreignField: "_id", 
      as: "evento" }
  },
  { $unwind: "$evento" },
  { $match: { "evento.recinto.ciudad": ciudadConsulta1 } },
  {
    $lookup: { from: "usuarios", 
      localField: "usuario_id", 
      foreignField: "_id", 
      as: "usuario" }
  },
  { $unwind: "$usuario" },
  { $unwind: "$items" },
  {
    $project: {
      _id: 0,
      rut: "$usuario.rut",
      nombre: "$usuario.nombre",
      fecha_compra: 1,
      evento: "$evento.nombre",
      ciudad: "$evento.recinto.ciudad",
      tipo_ticket: "$items.tipo_ticket",
      cantidad: "$items.cantidad",
      precio_unitario: "$items.precio_unitario"
    }
  }
]);

// 1B) Gasto total del usuario en esa ciudad
use('eventify_db');
db.ordenes_compra.aggregate([
  { $match: { usuario_id: idUsuarioConsulta, estado: "pagada" } },
  {
    $lookup: { from: "eventos",
      localField: "evento_id",
      foreignField: "_id",
      as: "evento" }
  },
  { $unwind: "$evento" },
  { $match: { "evento.recinto.ciudad": ciudadConsulta1 } },
  {
    $lookup: { from: "usuarios", localField: "usuario_id", foreignField: "_id", as: "usuario" }
  },
  { $unwind: "$usuario" },
  {
    $group: {
      _id: { rut: "$usuario.rut",
        nombre: "$usuario.nombre",
        ciudad: "$evento.recinto.ciudad" },
      gasto_total: { $sum: "$total" },
      ordenes_pagadas: { $sum: 1 }
    }
  },
  {
    $project: {
      _id: 0,
      rut: "$_id.rut",
      nombre: "$_id.nombre",
      ciudad: "$_id.ciudad",
      gasto_total: 1,
      ordenes_pagadas: 1
    }
  }
]);



// CONSULTA 2: Reporte de ventas por evento
// Total recaudado, tickets vendidos, % de venta respecto al stock
// inicial (embebido) y etiqueta "Exitoso" / "Por Mejorar".
// Regla: si se vendio el 40% o mas del stock inicial => "Exitoso"

use('eventify_db');
db.ordenes_compra.aggregate([
  // solo ordenes pagadas (aqui se filtra, sin necesidad de $cond)
  { $match: { estado: "pagada" } },

  // cantidad de tickets de cada orden (suma el arreglo items)
  { $project: { evento_id: 1, total: 1, tickets_orden: { $sum: "$items.cantidad" } } },

  // agrupar por evento
  {
    $group: {
      _id: "$evento_id",
      total_recaudado: { $sum: "$total" },
      tickets_vendidos: { $sum: "$tickets_orden" }
    }
  },

  // traer datos del evento
  {
    $lookup: { from: "eventos", localField: "_id", foreignField: "_id", as: "evento" }
  },
  { $unwind: "$evento" },

  // stock inicial de todos los tickets embebidos
  {
    $project: {
      _id: 0,
      evento: "$evento.nombre",
      ciudad: "$evento.recinto.ciudad",
      estado_evento: "$evento.estado",
      total_recaudado: 1,
      tickets_vendidos: 1,
      stock_inicial_total: { $sum: "$evento.tickets_disponibles.stock_inicial" }
    }
  },

  // porcentaje de venta
  {
    $project: {
      evento: 1, ciudad: 1, estado_evento: 1,
      total_recaudado: 1, tickets_vendidos: 1, stock_inicial_total: 1,
      porcentaje_venta: {
        $round: [{ $multiply: [{ $divide: ["$tickets_vendidos", "$stock_inicial_total"] }, 100] }, 1]
      }
    }
  },

  // etiqueta
  {
    $project: {
      evento: 1, ciudad: 1, estado_evento: 1,
      total_recaudado: 1, tickets_vendidos: 1, stock_inicial_total: 1, porcentaje_venta: 1,
      etiqueta: { $cond: [{ $gte: ["$porcentaje_venta", 40] }, "Exitoso", "Por Mejorar"] }
    }
  }
]);


// CONSULTA 3: Eventos futuros en una ciudad con algun ticket barato
// disponible (filtrado de subdocumentos y fechas)

use('eventify_db');
const ciudadBuscada = "Santiago";
const precioMaximo = 20000;
db.eventos.aggregate([
  {
    $match: {
      "recinto.ciudad": ciudadBuscada,
      fecha_evento: { $gt: new Date() },
      estado: "programado"
    }
  },
  { $unwind: "$tickets_disponibles" },
  {
    $match: {
      "tickets_disponibles.precio": { $lt: precioMaximo },
      "tickets_disponibles.stock_disponible": { $gt: 0 }
    }
  },
  {
    $project: {
      _id: 0,
      evento: "$nombre",
      fecha_evento: 1,
      ciudad: "$recinto.ciudad",
      tipo_ticket: "$tickets_disponibles.tipo",
      precio: "$tickets_disponibles.precio",
      stock_disponible: "$tickets_disponibles.stock_disponible"
    }
  }
]);


// CONSULTA 4 (LIBRE): Nivel de satisfaccion de los eventos finalizados
//
// JUSTIFICACION DE NEGOCIO:
// Esta consulta busca descubrir que eventos finalizados dejaron una mejor
// experiencia en los asistentes, usando el promedio de puntuacion y la
// cantidad de resenas de cada evento. Es util para la gerencia porque
// permite decidir que eventos conviene repetir, que recintos o categorias
// priorizar y cuales revisar por problemas de calidad, basandose en la
// opinion real de los clientes y no solo en las ventas.
//
// CRITERIO DE VALORACION:
//  - Sin resenas              => "Sin resenas"
//  - Promedio >= 4.5          => "Excelente"
//  - Promedio >= 3.5          => "Bueno"
//  - Promedio menor a 3.5     => "Por mejorar"
//


use('eventify_db');
db.eventos.aggregate([
  { $match: { estado: "finalizado" } },
  {
    $lookup: {
      from: "resenas_evaluaciones",
      localField: "_id",
      foreignField: "evento_id",
      as: "resenas"
    }
  },

  // 1er project: cantidad y promedio (se conservan los campos que se usarán después)
  {
    $project: {
      nombre: 1,
      categoria: 1,
      recinto: 1,
      fecha_evento: 1,
      resenas: 1,
      total_resenas: { $size: "$resenas" },
      promedio_puntuacion: { $round: [{ $ifNull: [{ $avg: "$resenas.puntuacion" }, 0] }, 1] }
    }
  },

  // 2do project: etiqueta, fecha formateada y lista de opiniones
  {
    $project: {
      _id: 0,
      evento: "$nombre",
      ciudad: "$recinto.ciudad",
      categoria: 1,
      fecha: { $dateToString: { format: "%d-%m-%Y", date: "$fecha_evento" } },
      total_resenas: 1,
      promedio_puntuacion: 1,
      valoracion: {
        $switch: {
          branches: [
            { case: { $eq: ["$total_resenas", 0] }, then: "Sin reseñas" },
            { case: { $gte: ["$promedio_puntuacion", 4.5] }, then: "Excelente" },
            { case: { $gte: ["$promedio_puntuacion", 3.5] }, then: "Bueno" }
          ],
          default: "Por mejorar"
        }
      },
      opiniones: {
        $map: {
          input: "$resenas",
          as: "r",
          in: { puntuacion: "$$r.puntuacion", comentario: "$$r.comentario" }
        }
      }
    }
  }
]);