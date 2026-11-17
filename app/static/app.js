// Interfaz del MVP de VetVision AI (specs/004-mvp-web). HTML + JS simples, sin framework.
// Tres vistas en una sola pagina, con navegacion por hash: #nuevo, #estudio/CODIGO, #estudios.
"use strict";

const TIPOS_HALLAZGO_RESPALDO = [
  { id: "patron_alveolar", etiqueta: "Patrón alveolar" },
  { id: "patron_bronquial", etiqueta: "Patrón bronquial" },
  { id: "patron_vascular", etiqueta: "Patrón vascular" },
  { id: "patron_intersticial", etiqueta: "Patrón intersticial" },
  { id: "efusion_pleural", etiqueta: "Efusión pleural" },
  { id: "neumotorax", etiqueta: "Neumotórax" },
  { id: "cardiomegalia", etiqueta: "Cardiomegalia" },
  { id: "masa_nodulo", etiqueta: "Masa o nódulo" },
  { id: "sin_hallazgos", etiqueta: "Sin hallazgos" },
  { id: "otro", etiqueta: "Otro" },
];

const contenido = document.getElementById("contenido");
let tiposHallazgo = TIPOS_HALLAZGO_RESPALDO;

async function pedir(url, opciones) {
  const respuesta = await fetch(url, opciones);
  const cuerpo = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    const error = new Error(cuerpo.mensaje || "Ocurrió un error inesperado.");
    error.codigo = cuerpo.codigo;
    throw error;
  }
  return cuerpo;
}

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = texto == null ? "" : String(texto);
  return div.innerHTML;
}

function marcarNav(vista) {
  document.querySelectorAll(".vv-nav a").forEach((enlace) => {
    if (enlace.dataset.vista === vista) enlace.setAttribute("aria-current", "page");
    else enlace.removeAttribute("aria-current");
  });
}

async function enrutar() {
  const hash = location.hash.slice(1) || "nuevo";
  try {
    if (hash === "nuevo") {
      marcarNav("nuevo");
      await vistaNuevo();
    } else if (hash === "estudios") {
      marcarNav("estudios");
      await vistaListado();
    } else if (hash.startsWith("estudio/")) {
      marcarNav("estudios");
      await vistaDetalle(hash.slice("estudio/".length));
    } else {
      location.hash = "#nuevo";
    }
  } catch (error) {
    contenido.innerHTML = `<div class="vv-panel"><p class="vv-error" role="alert">${escapar(error.message)}</p></div>`;
  }
}

// ---------------------------------------------------------------- vista: nuevo estudio

async function vistaNuevo() {
  try {
    const salud = await pedir("/api/salud");
    tiposHallazgo = salud.tipos_hallazgo || TIPOS_HALLAZGO_RESPALDO;
  } catch (_error) {
    // Si /api/salud falla, seguimos con el catálogo de respaldo: la carga igual puede intentarse.
  }

  contenido.innerHTML = `
    <section class="vv-panel">
      <h1>Nuevo estudio</h1>
      <div class="vv-campo">
        <label for="vv-especie">Especie</label>
        <select id="vv-especie">
          <option value="canino" selected>Canino</option>
          <option value="felino">Felino</option>
        </select>
        <p id="vv-aviso-especie" class="vv-error" hidden>La especie felina queda fuera del alcance evaluado del modelo.</p>
      </div>
      <div class="vv-zona-carga" id="vv-zona-carga" tabindex="0" role="button"
           aria-describedby="vv-ayuda-carga">
        <p>Arrastrá una radiografía (JPG o PNG) o hacé clic para elegir un archivo.</p>
        <input type="file" id="vv-archivo" accept=".jpg,.jpeg,.png" class="vv-oculto"
               style="display:none" />
      </div>
      <p id="vv-ayuda-carga" class="vv-error" role="alert" aria-live="assertive"></p>
      <p id="vv-cargando" hidden>Procesando la radiografía…</p>
    </section>
  `;

  const selectEspecie = document.getElementById("vv-especie");
  const avisoEspecie = document.getElementById("vv-aviso-especie");
  selectEspecie.addEventListener("change", () => {
    avisoEspecie.hidden = selectEspecie.value !== "felino";
  });

  const zona = document.getElementById("vv-zona-carga");
  const archivo = document.getElementById("vv-archivo");
  const ayuda = document.getElementById("vv-ayuda-carga");
  const cargando = document.getElementById("vv-cargando");

  const abrirSelector = () => archivo.click();
  zona.addEventListener("click", abrirSelector);
  zona.addEventListener("keydown", (evento) => {
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      abrirSelector();
    }
  });
  ["dragenter", "dragover"].forEach((tipo) =>
    zona.addEventListener(tipo, (evento) => {
      evento.preventDefault();
      zona.classList.add("vv-arrastrando");
    })
  );
  ["dragleave", "drop"].forEach((tipo) =>
    zona.addEventListener(tipo, () => zona.classList.remove("vv-arrastrando"))
  );
  zona.addEventListener("drop", (evento) => {
    evento.preventDefault();
    const archivos = evento.dataTransfer && evento.dataTransfer.files;
    if (archivos && archivos.length) cargarArchivo(archivos[0]);
  });
  archivo.addEventListener("change", () => {
    if (archivo.files.length) cargarArchivo(archivo.files[0]);
  });

  async function cargarArchivo(file) {
    ayuda.textContent = "";
    cargando.hidden = false;
    const datos = new FormData();
    datos.append("imagen", file);
    datos.append("especie", selectEspecie.value);
    try {
      const estudio = await pedir("/api/estudios", { method: "POST", body: datos });
      location.hash = `#estudio/${estudio.codigo}`;
    } catch (error) {
      ayuda.textContent = error.message;
    } finally {
      cargando.hidden = true;
      archivo.value = "";
    }
  }
}

// ---------------------------------------------------------------- vista: detalle del estudio

function nivelClase(nivel) {
  return { alta: "vv-nivel-alta", media: "vv-nivel-media", baja: "vv-nivel-baja" }[nivel] || "";
}

function filaHallazgo(h) {
  const confianza = h.confianza != null ? `${Math.round(h.confianza * 100)} %` : "sin confianza (manual)";
  const nivel = h.nivel ? `<span class="vv-nivel ${nivelClase(h.nivel)}">${escapar(h.nivel)}</span>` : "";
  const deshabilitado = h.estado !== "pendiente" ? "disabled" : "";
  return `
    <article class="vv-hallazgo" data-estado="${escapar(h.estado)}" data-id="${h.id}">
      <p><strong>${escapar(h.tipo_etiqueta)}</strong> — ${confianza} ${nivel}</p>
      <p>Estado: ${escapar(h.estado)}${h.origen === "manual" ? " (agregado a mano)" : ""}</p>
      ${h.comentario ? `<p>Comentario: ${escapar(h.comentario)}</p>` : ""}
      <div class="vv-acciones-hallazgo">
        <button type="button" data-accion="validar" ${deshabilitado}>Validar</button>
        <button type="button" class="vv-secundario" data-accion="corregir" ${deshabilitado}>Corregir</button>
        <button type="button" class="vv-peligro" data-accion="descartar" ${deshabilitado}>Descartar</button>
      </div>
    </article>
  `;
}

async function vistaDetalle(codigo) {
  const estudio = await pedir(`/api/estudios/${encodeURIComponent(codigo)}`);
  const opcionesTipo = tiposHallazgo
    .map((t) => `<option value="${escapar(t.id)}">${escapar(t.etiqueta)}</option>`)
    .join("");

  contenido.innerHTML = `
    <section class="vv-panel">
      <h1>Estudio ${escapar(estudio.codigo)}</h1>
      <p>Especie: ${escapar(estudio.especie)} · Estado: ${escapar(estudio.estado)}</p>
      ${estudio.avisos.map((a) => `<p class="vv-aviso" role="alert">${escapar(a.mensaje)}</p>`).join("")}
    </section>
    <div class="vv-estudio-detalle">
      <img class="vv-imagen-radiografia" src="/api/estudios/${encodeURIComponent(estudio.codigo)}/imagen"
           alt="Radiografía cargada del estudio ${escapar(estudio.codigo)}" />
      <div class="vv-hallazgos">
        <h2>Hallazgos</h2>
        <div id="vv-lista-hallazgos">
          ${estudio.hallazgos.length ? estudio.hallazgos.map(filaHallazgo).join("") : "<p>Sin hallazgos todavía.</p>"}
        </div>
        <form id="vv-form-manual" class="vv-panel">
          <h3>Agregar hallazgo</h3>
          <div class="vv-campo">
            <label for="vv-tipo-manual">Tipo</label>
            <select id="vv-tipo-manual">${opcionesTipo}</select>
          </div>
          <div class="vv-campo">
            <label for="vv-comentario-manual">Comentario (opcional)</label>
            <textarea id="vv-comentario-manual" rows="2"></textarea>
          </div>
          <button type="submit">Agregar hallazgo</button>
        </form>
        <button type="button" id="vv-cerrar" ${estudio.puede_cerrarse ? "" : "disabled"}>
          Cerrar informe
        </button>
        <p id="vv-motivo-cierre" class="vv-error" role="alert"></p>
      </div>
    </div>
    <footer class="vv-descargo" role="note" style="margin-top:16px">${escapar(estudio.descargo)}</footer>
  `;

  document.getElementById("vv-lista-hallazgos").addEventListener("click", async (evento) => {
    const boton = evento.target.closest("button[data-accion]");
    if (!boton) return;
    const articulo = boton.closest(".vv-hallazgo");
    const idHallazgo = articulo.dataset.id;
    const accion = boton.dataset.accion;
    let tipo, comentario;
    if (accion === "corregir") {
      tipo = prompt("Nuevo tipo de hallazgo (dejar vacío para no cambiarlo):") || null;
      comentario = prompt("Comentario:") || null;
      if (!tipo && !comentario) return;
    }
    try {
      await pedir(`/api/estudios/${encodeURIComponent(codigo)}/hallazgos/${idHallazgo}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accion, tipo, comentario }),
      });
      vistaDetalle(codigo);
    } catch (error) {
      alert(error.message);
    }
  });

  document.getElementById("vv-form-manual").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const tipo = document.getElementById("vv-tipo-manual").value;
    const comentario = document.getElementById("vv-comentario-manual").value;
    try {
      await pedir(`/api/estudios/${encodeURIComponent(codigo)}/hallazgos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tipo, comentario }),
      });
      vistaDetalle(codigo);
    } catch (error) {
      alert(error.message);
    }
  });

  document.getElementById("vv-cerrar").addEventListener("click", async () => {
    try {
      await pedir(`/api/estudios/${encodeURIComponent(codigo)}/cerrar`, { method: "POST" });
      vistaDetalle(codigo);
    } catch (error) {
      document.getElementById("vv-motivo-cierre").textContent = error.message;
    }
  });
}

// ---------------------------------------------------------------- vista: listado

async function vistaListado(estadoFiltro) {
  const parametros = estadoFiltro ? `?estado=${encodeURIComponent(estadoFiltro)}` : "";
  const listado = await pedir(`/api/estudios${parametros}`);
  const filas = listado.estudios
    .map(
      (e) => `
      <tr>
        <td><a href="#estudio/${escapar(e.codigo)}">${escapar(e.codigo)}</a></td>
        <td>${escapar(e.fecha_carga ? e.fecha_carga.slice(0, 19).replace("T", " ") : "")}</td>
        <td>${escapar(e.region.etiqueta || "—")}</td>
        <td>${e.cantidad_hallazgos} (${e.pendientes} pendientes)</td>
        <td>${escapar(e.estado)}</td>
      </tr>`
    )
    .join("");

  contenido.innerHTML = `
    <section class="vv-panel">
      <h1>Estudios procesados</h1>
      <div class="vv-filtros" role="group" aria-label="Filtrar por estado">
        <button type="button" data-estado="">Todos</button>
        <button type="button" data-estado="borrador">Borrador</button>
        <button type="button" data-estado="validado">Validado</button>
      </div>
      <table class="vv-tabla">
        <thead>
          <tr><th>Código</th><th>Fecha</th><th>Región</th><th>Hallazgos</th><th>Estado</th></tr>
        </thead>
        <tbody>${filas || '<tr><td colspan="5">Todavía no hay estudios cargados.</td></tr>'}</tbody>
      </table>
    </section>
  `;

  contenido.querySelectorAll("[data-estado]").forEach((boton) => {
    boton.addEventListener("click", () => vistaListado(boton.dataset.estado || null));
  });
}

window.addEventListener("hashchange", enrutar);
enrutar();
