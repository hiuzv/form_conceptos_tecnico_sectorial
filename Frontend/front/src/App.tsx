import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Plus, Trash2, Download, ArrowLeft, PlusCircle, Search, RefreshCcw } from "lucide-react";

type ID = number;
interface Opcion { id: ID; nombre: string; codigo?: number | null; }
type EntidadFin = "DEPARTAMENTO" | "PROPIOS" | "SGP_LIBRE_INVERSION" | "SGP_LIBRE_DESTINACION" | "SGP_APSB" | "SGP_EDUCACION" | "SGP_ALIMENTACION_ESCOLAR" | "SGP_CULTURA" | "SGP_DEPORTE" | "SGP_SALUD" | "MUNICIPIO" | "NACION" | "OTROS";

const ENTIDADES: EntidadFin[] = ["DEPARTAMENTO", "PROPIOS", "SGP_LIBRE_INVERSION", "SGP_LIBRE_DESTINACION", "SGP_APSB", "SGP_EDUCACION", "SGP_ALIMENTACION_ESCOLAR", "SGP_CULTURA", "SGP_DEPORTE", "SGP_SALUD", "MUNICIPIO", "NACION", "OTROS"];
const API_BASE_DEFAULT = "http://localhost:8000";

/* ---------- Tipos de estado ---------- */
interface DatosBasicosDB {
  nombre_proyecto: string;
  cod_id_mga: number;
  id_dependencia: ID | null;
  id_linea_estrategica: ID | null;
  id_programa: ID | null;
  id_sector: ID | null;
  nombre_secretario: string;
  oficina_secretario: string;
  duracion_proyecto: number;
  cantidad_beneficiarios: number;
}

interface PoliticaFila {
  id_politica: ID | null;
  id_categoria: ID | null;
  id_subcategoria: ID | null;
  valor_destinado: number;
  opciones_categorias?: Opcion[];
  opciones_subcategorias?: Opcion[];
  valor_ui?: string;
}

interface EstadoFormulario {
  datos_basicos: DatosBasicosDB;
  politicas: PoliticaFila[];
  metas_sel: ID[];
  variables_sectorial_sel: ID[];
  variables_tecnico_sel: ID[];
  variables_sel?: ID[]; // compat
  anio_inicio?: number | null;
  estructura_financiera_ui: Record<string, string | undefined>;
}

/* ---------- Utils ---------- */
function cx(...xs: Array<string | false | null | undefined>) { return xs.filter(Boolean).join(" "); }
function toMoney(n?: number) {
  const v = Number(n ?? 0);
  return v.toLocaleString("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
async function fetchJson(path: string) {
  const res = await fetch(`${API_BASE_DEFAULT.replace(/\/$/,"")}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}
function normalizaFlex(arr: any[], posiblesNombres: string[], campoCodigo?: string): Opcion[] {
  if (!Array.isArray(arr)) return [];
  return arr.map((x) => {
    const nombreKey = posiblesNombres.find(k => x[k] != null) ?? posiblesNombres[0];
    return {
      id: Number(x.id ?? x.id_dependencia ?? x.codigo ?? x.cod_id_mga ?? 0),
      nombre: String(x[nombreKey] ?? x.nombre ?? x.dependencia ?? ""),
      codigo: campoCodigo ? (x[campoCodigo] ?? null) : null,
    };
  });
}
function sortById(arr: Opcion[]): Opcion[] { return [...arr].sort((a, b) => a.id - b.id); }
function sortOptions(arr: Opcion[]): Opcion[] {
  return [...arr].sort((a, b) => {
    const aHas = a.codigo != null;
    const bHas = b.codigo != null;
    if (aHas && bHas && a.codigo !== b.codigo) return Number(a.codigo) - Number(b.codigo);
    const byNombre = a.nombre.localeCompare(b.nombre, "es", { numeric: true, sensitivity: "base" });
    if (byNombre !== 0) return byNombre;
    return a.id - b.id;
  });
}
function round2(n: number) { return Math.round(n * 100) / 100; }
function parseDecimal2(raw: string): number | null {
  const t = (raw ?? "").trim().replace(/\s+/g, "").replace(",", ".");
  if (t === "") return 0;
  if (!/^\d*(?:\.\d{0,2})?$/.test(t)) return null;
  const num = Number(t);
  return Number.isFinite(num) ? round2(num) : null;
}
function numbersEqual(a: number, b: number) { return Math.abs(a - b) < 0.005; }
function keyFin(anio: number, entidad: EntidadFin) { return `${anio}|${entidad}`; }
function getYears(anio_inicio?: number | null): number[] {
  if (!anio_inicio || anio_inicio < 1900 || anio_inicio > 3000) return [];
  return [anio_inicio, anio_inicio + 1, anio_inicio + 2, anio_inicio + 3];
}

/* ---------- Lista ---------- */
type ProyectoListaItemFlex = Record<string, any> & { nombre?: string; nombre_proyecto?: string; cod_id_mga?: number; id_dependencia?: number; dependencia_id?: number };

/* Extrae id si existe con distintos nombres */
function getRowId(p: ProyectoListaItemFlex): number | null {
  const candidate =
    p.id ??
    p.form_id ??
    p.formulario_id ??
    p.id_formulario ??
    p.proyecto_id ??
    p.id_proyecto ??
    p.id_form ??
    p.pk ??
    null;
  if (candidate == null) return null;
  const n = Number(candidate);
  return Number.isFinite(n) ? n : null;
}

/* ========== Componente principal ========== */
export default function App() {
  const [vista, setVista] = useState<"lista" | "form">("lista");

  // LISTA
  const [deps, setDeps] = useState<Opcion[]>([]);
  const [fNombre, setFNombre] = useState("");
  const [fCodMga, setFCodMga] = useState<string>("");
  const [fDependencia, setFDependencia] = useState<ID | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState<number | null>(null);
  const [lista, setLista] = useState<ProyectoListaItemFlex[]>([]);
  const [loadingLista, setLoadingLista] = useState(false);
  const [viabilidadList, setViabilidadList] = useState<Opcion[]>([]);
  const [tiposViabilidad, setTiposViabilidad] = useState<Opcion[]>([]);
  const [viabilidadesSel, setViabilidadesSel] = useState<ID[]>([]);
  const [funcionariosViab, setFuncionariosViab] = useState<Record<number, {nombre:string; cargo:string}>>({});
  const firstFiltersRun = React.useRef(true);

  const queryLista = async (resetPage=false) => {
    try {
      setLoadingLista(true);
      const p = resetPage ? 1 : page;
      const params = new URLSearchParams();
      if (fNombre.trim()) params.set("nombre", fNombre.trim());
      if (fCodMga.trim()) params.set("cod_id_mga", fCodMga.trim());
      if (fDependencia != null) params.set("id_dependencia", String(fDependencia));
      params.set("page", String(p));
      params.set("page_size", String(pageSize));
      const data = await fetchJson(`/proyecto/lista?${params.toString()}`);
      const items: ProyectoListaItemFlex[] = Array.isArray(data) ? (data as any) : (data.items ?? data.data ?? data.results ?? []);
      const tot = (data.total ?? data.count ?? (Array.isArray(data) ? null : null)) as number | null;
      setLista(items);
      setTotal(tot);
      if (resetPage) setPage(1);
    } catch (e) {
      console.error(e);
      setLista([]);
    } finally {
      setLoadingLista(false);
    }
  };

  useEffect(() => { (async () => {
    try {
      const depsR = await fetchJson("/proyecto/dependencias");
      setDeps(sortOptions(normalizaFlex(depsR, ["nombre_dependencia", "nombre"])));
    } catch (e) { console.error(e); }
  })(); }, []);
  useEffect(() => { queryLista(true); }, []);

  const lastPage = useMemo(
    () => (total != null ? Math.max(1, Math.ceil(total / pageSize)) : null),
    [total, pageSize]
  );
  const canPrev = page > 1;
  const canNext = lastPage != null ? page < lastPage : (lista.length === pageSize && lista.length > 0);

  useEffect(() => {
    if (vista !== "lista") return;
    if (firstFiltersRun.current) {
      firstFiltersRun.current = false;
      return;
    }
    const t = setTimeout(() => {
      queryLista(true);
    }, 400);
    return () => clearTimeout(t);
  }, [vista, fNombre, fCodMga, fDependencia]);

  React.useEffect(() => {
    if (firstFiltersRun.current) {
      firstFiltersRun.current = false;
      return;
    }
    const t = setTimeout(() => {
      queryLista(true);
    }, 400);

    return () => clearTimeout(t);
  }, [fNombre, fCodMga, fDependencia]);

  // FORM
  const [lineas, setLineas] = useState<Opcion[]>([]);
  const [sectores, setSectores] = useState<Opcion[]>([]);
  const [programas, setProgramas] = useState<Opcion[]>([]);
  const [metas, setMetas] = useState<Opcion[]>([]);
  const [variablesSectorial, setVariablesSectorial] = useState<Opcion[]>([]);
  const [variablesTecnico, setVariablesTecnico] = useState<Opcion[]>([]);
  const [politicas, setPoliticas] = useState<Opcion[]>([]);

  const [step, setStep] = useState(1);
  const [sending, setSending] = useState(false);

  const [datos, setDatos] = useState<EstadoFormulario>({
    datos_basicos: {
      nombre_proyecto: "",
      cod_id_mga: 0,
      id_dependencia: null,
      id_linea_estrategica: null,
      id_programa: null,
      id_sector: null,
      nombre_secretario: "",
      oficina_secretario: "",
      duracion_proyecto: 0,
      cantidad_beneficiarios: 0,
    },
    politicas: [{ id_politica: null, id_categoria: null, id_subcategoria: null, valor_destinado: 0 }],
    metas_sel: [],
    variables_sectorial_sel: [],
    variables_tecnico_sel: [],
    variables_sel: [],
    anio_inicio: undefined,
    estructura_financiera_ui: {},
  });

  const [formId, setFormId] = useState<ID | null>(null);

  // Totales UI
  const totalPoliticas = useMemo(() => round2(datos.politicas.reduce((a, b) => a + (Number(b.valor_destinado) || 0), 0)), [datos.politicas]);
  const years = useMemo(() => getYears(datos.anio_inicio), [datos.anio_inicio]);
  const totalesAnio = useMemo(() => {
    const out: Record<number, number> = {};
    years.forEach(anio => {
      let s = 0;
      ENTIDADES.forEach(ent => {
        const v = parseDecimal2(datos.estructura_financiera_ui[keyFin(anio, ent)] ?? "");
        s += v ?? 0;
      });
      out[anio] = round2(s);
    });
    return out;
  }, [datos.estructura_financiera_ui, years]);
  const totalProyecto = useMemo(() => round2(years.reduce((acc, anio) => acc + (totalesAnio[anio] ?? 0), 0)), [years, totalesAnio]);
  const difProyectoPoliticas = useMemo(() => round2(totalProyecto - totalPoliticas), [totalProyecto, totalPoliticas]);
  const igualesProyectoPoliticas = numbersEqual(totalProyecto, totalPoliticas);

  useEffect(() => {
    if (vista !== "form") return;
      (async () => {
        try {
          const [lineasR, varsSecR, varsTecR, politR, viaR, tiposVR] = await Promise.all([
            fetchJson("/proyecto/lineas"),
            fetchJson("/proyecto/variables_sectorial"),
            fetchJson("/proyecto/variables_tecnico"),
            fetchJson("/proyecto/politicas"),
            fetchJson("/proyecto/viabilidad"),
            fetchJson("/proyecto/tipos_viabilidad"),
          ]);
          setLineas(sortOptions(normalizaFlex(lineasR, ["nombre", "nombre_linea_estrategica"])));
          setVariablesSectorial(sortById(normalizaFlex(varsSecR, ["nombre_variable", "nombre"])));
          setVariablesTecnico(sortById(normalizaFlex(varsTecR, ["nombre_variable", "nombre"])));
          setPoliticas(sortOptions(normalizaFlex(politR, ["nombre_politica", "nombre"])));
          setViabilidadList(sortOptions(normalizaFlex(viaR, ["nombre"])));
          setTiposViabilidad(sortById(normalizaFlex(tiposVR, ["nombre"])));
        } catch (e) { console.error(e); }
      })();
  }, [vista]);


  // Sectores por línea
  useEffect(() => {
    const idLinea = datos.datos_basicos.id_linea_estrategica;
    if (!idLinea) { setSectores([]); return; }
    (async () => {
      try {
        const r = await fetchJson(`/proyecto/sectores?linea_id=${idLinea}`);
        setSectores(sortOptions(normalizaFlex(r, ["nombre_sector", "nombre"], "codigo_sector")));
      } catch (e) { console.error(e); setSectores([]); }
    })();
  }, [datos.datos_basicos.id_linea_estrategica]);

  // Programas por sector
  useEffect(() => {
    const idSector = datos.datos_basicos.id_sector;
    if (!idSector) { setProgramas([]); return; }
    (async () => {
      try {
        const r = await fetchJson(`/proyecto/programas?sector_id=${idSector}`);
        setProgramas(sortOptions(normalizaFlex(r, ["nombre_programa", "nombre"], "codigo_programa")));
      } catch (e) { console.error(e); setProgramas([]); }
    })();
  }, [datos.datos_basicos.id_sector]);

  // Metas por programa
  useEffect(() => {
    const idPrograma = datos.datos_basicos.id_programa;
    if (!idPrograma) {
      setMetas([]);
      setDatos(p => ({ ...p, metas_sel: [] }));
      return;
    }
    (async () => {
      try {
        const r = await fetchJson(`/proyecto/metas?programa_id=${idPrograma}`);
        const ops = sortOptions(normalizaFlex(r, ["nombre_meta", "nombre"]));
        setMetas(ops);
        setDatos(p => {
          const valid = new Set(ops.map(o => o.id));
          const kept = p.metas_sel.filter(id => valid.has(id));
          return { ...p, metas_sel: kept };
        });
      } catch (e) {
        console.error(e);
        setMetas([]);
        setDatos(p => ({ ...p, metas_sel: [] }));
      }
    })();
  }, [datos.datos_basicos.id_programa]);

  /* ---------- Build payload ---------- */
  function buildBackendPayload(state: EstadoFormulario) {
    const db = state.datos_basicos;
    const politicas_ids: ID[] = [];
    const valores_politicas: number[] = [];
    const categorias_ids: ID[] = [];
    const subcategorias_ids: ID[] = [];
    state.politicas.forEach(p => {
      if (p.id_politica != null) {
        politicas_ids.push(Number(p.id_politica));
        valores_politicas.push(Number(p.valor_destinado || 0));
        if (p.id_categoria != null) categorias_ids.push(Number(p.id_categoria));
        if (p.id_subcategoria != null) subcategorias_ids.push(Number(p.id_subcategoria));
      }
    });

    const variables_union = Array.from(new Set([
      ...(state.variables_sectorial_sel || []),
      ...(state.variables_tecnico_sel || []),
      ...(state.variables_sel || []),
    ]));

    const estructura_financiera: Array<{anio:number; entidad:EntidadFin; valor:number}> = [];
    const ys = getYears(state.anio_inicio);
    ys.forEach(anio => {
      ENTIDADES.forEach(ent => {
        const raw = state.estructura_financiera_ui[keyFin(anio, ent)] ?? "";
        const num = parseDecimal2(raw);
        estructura_financiera.push({ anio, entidad: ent, valor: num ?? 0 });
      });
    });

    return {
      nombre_proyecto: db.nombre_proyecto,
      cod_id_mga: Number(db.cod_id_mga || 0),
      id_dependencia: db.id_dependencia,
      id_linea_estrategica: db.id_linea_estrategica,
      id_programa: db.id_programa,
      id_sector: db.id_sector,
      metas: state.metas_sel,
      variables_sectorial: state.variables_sectorial_sel,
      variables_tecnico: state.variables_tecnico_sel,
      variables: variables_union,
      politicas: politicas_ids,
      valores_politicas,
      categorias: categorias_ids,
      subcategorias: subcategorias_ids,
      estructura_financiera,
    };
  }

  /* ---------- Guardado ---------- */
  async function ensureFormId(): Promise<number> {
    if (formId) return formId;
    const db = datos.datos_basicos;
    if (!db?.nombre_proyecto?.trim() || !db?.cod_id_mga || !db?.id_dependencia) {
      throw new Error("Faltan mínimos: Nombre, Cod. MGA y Dependencia");
    }
    const r = await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/minimo`, {
      method: "POST",
      headers: { "Content-Type":"application/json" },
      body: JSON.stringify({
        nombre_proyecto: db.nombre_proyecto.trim(),
        cod_id_mga: Number(db.cod_id_mga),
        id_dependencia: Number(db.id_dependencia),
      }),
    });
    if (!r.ok) throw new Error("Error creando/obteniendo proyecto mínimo");
    const j = await r.json();
    const id = Number(j.id);
    setFormId(id);
    return id;
  }

  async function saveStep(which:number) {
    const id = await ensureFormId();
    const payload = buildBackendPayload(datos);

    if (which === 1) {
      const b: any = {
        nombre_proyecto: datos.datos_basicos.nombre_proyecto?.trim() ?? "",
        cod_id_mga: Number(datos.datos_basicos.cod_id_mga || 0),
        id_dependencia: datos.datos_basicos.id_dependencia,
        nombre_secretario: datos.datos_basicos.nombre_secretario ?? "",
        oficina_secretario: datos.datos_basicos.oficina_secretario ?? "",
        duracion_proyecto: Number(datos.datos_basicos.duracion_proyecto || 0),
        cantidad_beneficiarios: Number(datos.datos_basicos.cantidad_beneficiarios || 0),
      };
      if (Number.isFinite(datos.datos_basicos.id_linea_estrategica) && Number(datos.datos_basicos.id_linea_estrategica) > 0) b.id_linea_estrategica = Number(datos.datos_basicos.id_linea_estrategica);
      if (Number.isFinite(datos.datos_basicos.id_sector)            && Number(datos.datos_basicos.id_sector)            > 0) b.id_sector            = Number(datos.datos_basicos.id_sector);
      if (Number.isFinite(datos.datos_basicos.id_programa)          && Number(datos.datos_basicos.id_programa)          > 0) b.id_programa          = Number(datos.datos_basicos.id_programa);

      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/basicos`, {
        method: "PATCH",
        headers: { "Content-Type":"application/json" },
        body: JSON.stringify(b),
      });
    }
    if (which === 2) {
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/metas`, {
        method:"PUT", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ ids: payload.metas }),
      });
    }
    if (which === 3) {
      const ys = getYears(datos.anio_inicio);
      const filas: Array<{anio:number; entidad:EntidadFin; valor:number}> = [];
      ys.forEach(anio => ENTIDADES.forEach(ent => {
        const raw = datos.estructura_financiera_ui[keyFin(anio, ent)] ?? "";
        const num = parseDecimal2(raw) ?? 0;
        filas.push({ anio, entidad: ent, valor: num });
      }));
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/estructura-financiera`, {
        method:"PUT", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ filas }),
      });
    }
    if (which === 4) {
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/variables-sectorial`, {
        method:"PUT", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ ids: payload.variables_sectorial }),
      });
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/variables-tecnico`, {
        method:"PUT", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ ids: payload.variables_tecnico }),
      });
    }
    if (which === 5) {
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/politicas`, {
        method:"PUT", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ politicas: payload.politicas, valores_politicas: payload.valores_politicas }),
      });
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/categorias`, {
        method:"PUT", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ ids: payload.categorias }),
      });
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/subcategorias`, {
        method:"PUT", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ ids: payload.subcategorias }),
      });
    }
    if (which === 6) {
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/viabilidades`, {
        method:"PUT", headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ ids: viabilidadesSel }),
      });

      const funcionarios = tiposViabilidad.map(t => ({
        id_tipo_viabilidad: t.id,
        nombre: funcionariosViab[t.id]?.nombre || "",
        cargo:  funcionariosViab[t.id]?.cargo  || "",
      })).filter(f => f.nombre || f.cargo);

      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/funcionarios-viabilidad`, {
        method:"PUT", headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ funcionarios }),
      });
    }
  }


  async function saveAll() { for (const w of [1,2,3,4,5]) { await saveStep(w); } }

  /* ---------- Abrir fila: SIN /resolve y SIN crear automáticamente ---------- */
  async function openFromRow(p: ProyectoListaItemFlex) {
    // Usa id si viene en la lista
    const rid = getRowId(p);
    if (rid != null) {
      setFormId(rid);
      setVista("form");
      await loadForm(rid);
      return;
    }

    // Si NO viene id, pregunto antes de crear
    const nombre = String(p.nombre ?? p.nombre_proyecto ?? "").trim();
    const cod = Number(p.cod_id_mga ?? p.cod_mga ?? p.codigo_mga ?? NaN);
    const dep = Number(p.id_dependencia ?? p.dependencia_id ?? NaN);

    if (!Number.isFinite(cod) || !Number.isFinite(dep)) {
      alert("No se puede abrir: la fila no trae ID ni (cod_id_mga + id_dependencia).");
      return;
    }
    
    // Crear mínimo (esperando que tu back lo haga idempotente)
    const r = await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/minimo`, {
      method: "POST",
      headers: { "Content-Type":"application/json" },
      body: JSON.stringify({
        nombre_proyecto: nombre || `Proyecto ${cod}`,
        cod_id_mga: Number(cod),
        id_dependencia: Number(dep),
      }),
    });
    if (!r.ok) { alert("No fue posible crear/obtener un ID mínimo."); return; }
    const j = await r.json();
    const nid = Number(j.id);
    if (!Number.isFinite(nid)) { alert("El backend no devolvió un ID válido."); return; }

    setFormId(nid);
    setVista("form");
    await loadForm(nid);
  }

  /* ---------- Carga de un formulario existente ---------- */
  async function loadForm(id: number) {
    try {
      const r = await fetchJson(`/proyecto/formulario/${id}`);
      const nombre_proyecto = r.nombre_proyecto ?? r.nombre ?? "";
      const cod_id_mga = Number(r.cod_id_mga ?? r.cod_mga ?? r.codigo_mga ?? 0);
     
      // Estructura financiera
      const efUI: Record<string, string> = {};
      let minAnio: number | null = null;
      (r.estructura_financiera || []).forEach((row: any) => {
        const anio = row.anio ?? null;
        const ent = (row.entidad ?? row.fuente) as EntidadFin;
        const val = Number(row.valor ?? row.monto ?? 0);
        if (anio != null && ent) {
          const k = `${anio}|${ent}`;
          efUI[k] = val ? val.toFixed(2) : "";
          if (minAnio == null || anio < minAnio) minAnio = anio;
        }
      });

      // Mapear metas / variables
      const metasSel = (r.metas || []).map((m: any) => Number(m.id ?? m.id_meta ?? m.meta_id ?? m.codigo)).filter(Number.isFinite);
      const varsSecSel = (r.variables_sectorial || r.variables_sectoriales || []).map((v: any) => Number(v.id ?? v.id_variable ?? v.variable_id)).filter(Number.isFinite);
      const varsTecSel = (r.variables_tecnico || r.variables_tecnicas || []).map((v: any) => Number(v.id ?? v.id_variable ?? v.variable_id)).filter(Number.isFinite);
      const viaSel = (r.viabilidades || []).map((v:any)=> Number(v.id ?? v.id_viabilidad ?? v.viabilidad_id)).filter(Number.isFinite);
      const funcs = Object.fromEntries((r.funcionarios_viabilidad || []).map((f:any) => [Number(f.id_tipo_viabilidad), { nombre: String(f.nombre||""), cargo: String(f.cargo||"") }]));

      setViabilidadesSel(viaSel);
      setFuncionariosViab(funcs);
      setDatos(prev => ({
        ...prev,
        datos_basicos: {
          ...prev.datos_basicos,
          nombre_proyecto,
          cod_id_mga,
          id_dependencia: r.id_dependencia ?? prev.datos_basicos.id_dependencia ?? null,
          id_linea_estrategica: r.id_linea_estrategica ?? prev.datos_basicos.id_linea_estrategica ?? null,
          id_sector:            r.id_sector            ?? prev.datos_basicos.id_sector            ?? null,
          id_programa:          r.id_programa          ?? prev.datos_basicos.id_programa          ?? null,
          nombre_secretario: r.nombre_secretario ?? prev.datos_basicos.nombre_secretario ?? "",
          oficina_secretario: r.oficina_secretario ?? prev.datos_basicos.oficina_secretario ?? "",
          duracion_proyecto:  r.duracion_proyecto  ?? prev.datos_basicos.duracion_proyecto  ?? 0,
          cantidad_beneficiarios: r.cantidad_beneficiarios ?? prev.datos_basicos.cantidad_beneficiarios ?? 0,
        },
        metas_sel: metasSel,
        variables_sectorial_sel: varsSecSel,
        variables_tecnico_sel: varsTecSel,
        variables_sel: Array.from(new Set([...varsSecSel, ...varsTecSel])),
        anio_inicio: minAnio,
        estructura_financiera_ui: efUI,
      }));

      setStep(1);
    } catch (e) {
      console.error("No se pudo cargar el formulario", e);
      alert("No se pudo cargar el formulario seleccionado.");
    }
  }

  function sanitizeFileName(s: string) {
    return (s || "Formulario").trim().replace(/\s+/g, "_").replace(/[^\w\-\.]+/g, "");
  }

  async function descargarExcelDirecto() {
    try {
      setSending(true);
      await saveAll();
      const id = await ensureFormId();
      const down = await fetch(`${API_BASE_DEFAULT.replace(/\/$/,"")}/descarga/formulario/${id}/excel`);
      if (!down.ok) {
        const txt = await down.text().catch(()=> "");
        throw new Error(`GET /descarga/formulario/${id}/excel → ${down.status} ${txt || down.statusText}`);
      }
      const blob = await down.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      const dep = deps.find(d => d.id === datos.datos_basicos.id_dependencia);
      const depName = dep ? dep.nombre : "Dependencia";
      const base = `${datos.datos_basicos.cod_id_mga}_${sanitizeFileName(depName)}`;
      a.download = `${base}_3_y_4_Concepto_tecnico_y_sectorial_2025.xlsx`;
      a.click();
      URL.revokeObjectURL(a.href);
      alert("Archivo descargado.");
    } catch (e: any) {
      alert(e.message || "Error al descargar el formulario");
    } finally {
      setSending(false);
    }
  }

  const limpiarFormulario = () => {
    setDatos({
      datos_basicos: {
        nombre_proyecto: "",
        cod_id_mga: 0,
        id_dependencia: null,
        id_linea_estrategica: null,
        id_programa: null,
        id_sector: null,
        nombre_secretario: "",
        oficina_secretario: "",
        duracion_proyecto: 0,
        cantidad_beneficiarios: 0,
      },
      politicas: [{ id_politica: null, id_categoria: null, id_subcategoria: null, valor_destinado: 0 }],
      metas_sel: [],
      variables_sectorial_sel: [],
      variables_tecnico_sel: [],
      variables_sel: [],
      anio_inicio: undefined,
      estructura_financiera_ui: {},
    });
    setViabilidadesSel([]);
    setFuncionariosViab({});
    setStep(1);
  };

  /* ---------- RENDER ---------- */
  if (vista === "lista") {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white p-4 md:p-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Proyectos</h1>
            <Button className="gap-2" onClick={() => { limpiarFormulario(); setFormId(null); setVista("form"); }}>
              <PlusCircle className="h-4 w-4"/> Nuevo proyecto
            </Button>
          </div>

          {/* Filtros */}
          <Card className="shadow-sm">
            <CardContent className="p-4 grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <Label>Nombre</Label>
                <Input
                  value={fNombre}
                  onChange={(e) => setFNombre(e.target.value)}
                  placeholder="Buscar por nombre…"
                />
              </div>
              <div>
                <Label>Código ID MGA</Label>
                <Input
                  value={fCodMga}
                  onChange={(e) => setFCodMga(e.target.value)}
                  placeholder="Ej. 12345"
                />
              </div>
              <div>
                <Label>Dependencia</Label>
                <SelectNative
                  opciones={deps}
                  value={fDependencia}
                  onChange={setFDependencia}
                  placeholder="Todas"
                />
              </div>
            </CardContent>
          </Card>

          {/* Tabla */}
          <div className="overflow-auto rounded-xl border">
            <table className="min-w-[760px] w-full text-sm table-fixed">
              <thead className="bg-slate-100">
                <tr>
                  <th className="px-3 py-2 text-left w-1/2">Nombre</th>
                  <th className="px-3 py-2 text-left w-28">Cod. MGA</th>
                  <th className="px-3 py-2 text-left w-1/4">Dependencia</th>
                  <th className="px-3 py-2 text-right w-24">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {loadingLista ? (
                  <tr><td colSpan={4} className="px-3 py-10 text-center text-slate-500">Cargando…</td></tr>
                ) : lista.length === 0 ? (
                  <tr><td colSpan={4} className="px-3 py-10 text-center text-slate-500">Sin resultados</td></tr>
                ) : (
                  lista.map((p, idx) => {
                    const rowId = getRowId(p);
                    const nombreFila = p.nombre ?? p.nombre_proyecto ?? "(sin nombre)";
                    const codFila = p.cod_id_mga ?? p.cod_mga ?? p.codigo_mga ?? "";
                    const depFila = p.id_dependencia ?? p.dependencia_id;
                    return (
                      <tr key={rowId ?? `${codFila || "sinCod"}-${idx}`} className="border-t align-top">
                        <td className="px-3 py-2 break-words whitespace-pre-wrap">{nombreFila}</td>
                        <td className="px-3 py-2">{codFila}</td>
                        <td className="px-3 py-2 break-words whitespace-pre-wrap">{(() => {
                          const d = deps.find(x => x.id === depFila);
                          return d ? d.nombre : depFila ?? "";
                        })()}</td>
                        <td className="px-3 py-2 text-right">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => openFromRow(p)}
                          >Abrir</Button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Paginación */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-slate-600">{total != null ? `Total: ${total} registros` : ""}</div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={()=> setPage(p => Math.max(1, p - 1))}
                disabled={!canPrev}
              >
                Anterior
              </Button>
              <div className="text-sm">Página {page}{lastPage ? ` de ${lastPage}` : ""}</div>
              <Button
                variant="outline"
                onClick={()=> setPage(p => p + 1)}
                disabled={!canNext}
              >
                Siguiente
              </Button>
              <select
                className="h-9 rounded-md border px-2 text-sm"
                value={pageSize}
                onChange={(e)=>{
                  setPageSize(Number(e.target.value));
                  setPage(1);
                }}
              >
                {[10,20,50].map(n=> <option key={n} value={n}>{n}/página</option>)}
              </select>
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* ---------- FORM ---------- */
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white p-4 md:p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Documentación Proyectos de Inversión</h1>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge variant="secondary">Total Proyecto: {toMoney(totalProyecto)}</Badge>
            </div>
          </div>
          <Button
            variant="outline"
            className="gap-2"
            onClick={async ()=>{
              try { await saveAll(); } catch(e:any){ alert(e.message||"Completa Nombre, Cod. MGA y Dependencia para guardar."); }
              setVista("lista");
              setFormId(null);
              queryLista(true);
            }}
          >
            <ArrowLeft className="h-4 w-4"/> Volver a lista
          </Button>
        </div>

        {/* Stepper */}
        <div className="flex flex-wrap gap-2 text-sm">
          {[
            [1, "Datos básicos"],
            [2, "Metas"],
            [3, "Estructura financiera"],
            [4, "Variables analizadas"],
            [5, "Políticas"],
            [6, "Viabilidad"],
            [7, "Descargas"],
          ].map(([idx, label]) => (
            <button
              key={idx as number}
              onClick={async ()=>{
                try { await saveStep(step); } catch (e:any) { alert(e.message || "No se pudo guardar el paso actual"); }
                setStep(Number(idx));
              }}
              className={cx("px-3 py-1.5 rounded-full border", step===idx ? "bg-black text-white" : "bg-white hover:bg-slate-50")}
            >{label}</button>
          ))}
        </div>

        {/* Paso 1 */}
        {step===1 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label="Nombre del proyecto">
                <Textarea
                  rows={3}
                  value={datos.datos_basicos.nombre_proyecto}
                  onChange={(e) => setDatos(p => ({ ...p, datos_basicos: { ...p.datos_basicos, nombre_proyecto: e.target.value } }))}
                  placeholder="Escribe el nombre completo del proyecto…"
                  className="resize-y"
                />
              </Field>

              <Field label="Código ID MGA">
                <Input type="number" value={datos.datos_basicos.cod_id_mga}
                  onChange={e=> setDatos(p=>({ ...p, datos_basicos: { ...p.datos_basicos, cod_id_mga: Number(e.target.value || 0) } }))} />
              </Field>

              <Field label="Dependencia">
                <SelectNative
                  opciones={deps}
                  value={datos.datos_basicos.id_dependencia}
                  onChange={(id)=> setDatos(p=> ({ ...p, datos_basicos: { ...p.datos_basicos, id_dependencia: id } }))}
                  placeholder="Selecciona dependencia"
                />
              </Field>

              <Field label="Línea estratégica">
                <SelectNative
                  opciones={lineas}
                  value={datos.datos_basicos.id_linea_estrategica}
                  onChange={(id)=> setDatos(p=> ({ ...p, datos_basicos: { ...p.datos_basicos, id_linea_estrategica: id, id_sector: null, id_programa: null } }))}
                  placeholder="Selecciona línea"
                />
              </Field>

              <Field label="Sector (según línea)">
                <SelectNative
                  opciones={sectores}
                  value={datos.datos_basicos.id_sector}
                  onChange={(id)=> setDatos(p=> ({ ...p, datos_basicos: { ...p.datos_basicos, id_sector: id, id_programa: null } }))}
                  placeholder={datos.datos_basicos.id_linea_estrategica ? "Selecciona sector" : "Primero elige una línea"}
                />
              </Field>

              <Field label="Programa (según sector)">
                <SelectNative
                  opciones={programas}
                  value={datos.datos_basicos.id_programa}
                  onChange={(id)=> setDatos(p=> ({ ...p, datos_basicos: { ...p.datos_basicos, id_programa: id } }))}
                  placeholder={datos.datos_basicos.id_sector ? "Selecciona programa" : "Primero elige un sector"}
                />
              </Field>

              <Field label="Nombre Secretario">
                <Input type="text" value={datos.datos_basicos.nombre_secretario}
                  onChange={(e) => setDatos(p => ({ ...p, datos_basicos: { ...p.datos_basicos, nombre_secretario: e.target.value } }))} />
              </Field>

              <Field label="Oficina Secretaría">
                <Input type="text" value={datos.datos_basicos.oficina_secretario}
                  onChange={(e) => setDatos(p => ({ ...p, datos_basicos: { ...p.datos_basicos, oficina_secretario: e.target.value } }))} />
              </Field>

              <Field label="Duración del proyecto (meses)">
                <Input type="number" value={datos.datos_basicos.duracion_proyecto}
                  onChange={e=> setDatos(p=>({ ...p, datos_basicos: { ...p.datos_basicos, duracion_proyecto: Number(e.target.value || 0) } }))} />
              </Field>

              <Field label="Cantidad de beneficiarios">
                <Input type="number" value={datos.datos_basicos.cantidad_beneficiarios} 
                onChange={(e) => setDatos(p => ({ ...p, datos_basicos: { ...p.datos_basicos, cantidad_beneficiarios: Number(e.target.value || 0) } }))} />
              </Field>
            </CardContent>
          </Card>
        )}

        {/* Paso 2 */}
        {step===2 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 space-y-2">
              <h3 className="font-semibold">Metas — depende del Programa</h3>
              <div className="border rounded-xl p-3 max-h-72 overflow-auto space-y-1">
                {metas.map(o => (
                  <CheckItem
                    key={`m-${o.id}`}
                    label={`${o.id} — ${o.nombre}`}
                    checked={datos.metas_sel.includes(o.id)}
                    onChange={(v)=> setDatos(prev => {
                      const set = new Set<number>(prev.metas_sel);
                      if (v) set.add(o.id); else set.delete(o.id);
                      return { ...prev, metas_sel: Array.from(set) };
                    })}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Paso 3 */}
        {step===3 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 space-y-4">
              <div className="grid gap-2 md:max-w-xs">
                <Label>Año de inicio</Label>
                <Input
                  type="number"
                  placeholder="Ej. 2025"
                  value={datos.anio_inicio ?? ""}
                  onChange={(e)=>{ const y = Number(e.target.value || ""); setDatos(p=>({ ...p, anio_inicio: Number.isFinite(y) ? y : null })); }}
                />
              </div>

              {years.length === 4 ? (
                <div className="overflow-auto rounded-xl border">
                  <table className="min-w-[720px] w-full text-sm">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="px-3 py-2 text-left">Entidad</th>
                        {years.map(y => (<th key={`y-${y}`} className="px-3 py-2 text-right">{y}</th>))}
                        <th className="px-3 py-2 text-right">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ENTIDADES.map(ent => (
                        <tr key={ent} className="border-t">
                          <td className="px-3 py-2 font-medium">{ent === "NACION" ? "Nación" : ent.charAt(0) + ent.slice(1).toLowerCase()}</td>
                          {years.map(y => {
                            const k = keyFin(y, ent);
                            const raw = datos.estructura_financiera_ui[k] ?? "";
                            return (
                              <td key={k} className="px-2 py-1">
                                <input
                                  type="text"
                                  inputMode="decimal"
                                  placeholder="0,00"
                                  className="w-full rounded-md border px-2 py-1 text-right"
                                  value={raw}
                                  onChange={(e)=> setDatos(p=> ({ ...p, estructura_financiera_ui: { ...p.estructura_financiera_ui, [k]: e.target.value } }))}
                                  onBlur={(e)=> {
                                    const n = parseDecimal2(e.target.value);
                                    setDatos(p=> ({
                                      ...p,
                                      estructura_financiera_ui: {
                                        ...p.estructura_financiera_ui,
                                        [k]: n === null ? (e.target.value ?? "") : (n === 0 ? "" : n.toFixed(2))
                                      }
                                    }));
                                  }}
                                />
                              </td>
                            );
                          })}
                          <td className="px-3 py-2 text-right font-semibold">
                            {toMoney(years.reduce((s,y)=> s + (parseDecimal2(datos.estructura_financiera_ui[keyFin(y, ent)] ?? "") ?? 0), 0))}
                          </td>
                        </tr>
                      ))}
                      <tr className="border-t bg-slate-50">
                        <td className="px-3 py-2 font-bold">Total</td>
                        {years.map(y=> (<td key={`tot-${y}`} className="px-3 py-2 text-right font-bold">{toMoney(totalesAnio[y] ?? 0)}</td>))}
                        <td className="px-3 py-2 text-right font-extrabold">{toMoney(totalProyecto)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-sm text-slate-600">Ingresa un año válido para construir la tabla.</div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Paso 4 */}
        {step===4 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 space-y-6">
              <div className="space-y-2">
                <h3 className="font-semibold">Variables concepto sectorial</h3>
                <div className="border rounded-xl p-3 max-h-72 overflow-auto space-y-1">
                  {variablesSectorial.map(o => (
                    <CheckItem
                      key={`vs-${o.id}`}
                      label={`${o.id} — ${o.nombre}`}
                      checked={datos.variables_sectorial_sel.includes(o.id)}
                      onChange={(v)=> setDatos(prev => {
                        const set = new Set<number>(prev.variables_sectorial_sel);
                        if (v) set.add(o.id); else set.delete(o.id);
                        const unionCompat = new Set<number>([ ...Array.from(set), ...prev.variables_tecnico_sel ]);
                        return { ...prev, variables_sectorial_sel: Array.from(set), variables_sel: Array.from(unionCompat) };
                      })}
                    />
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="font-semibold">Variables concepto técnico</h3>
                <div className="border rounded-xl p-3 max-h-72 overflow-auto space-y-1">
                  {variablesTecnico.map(o => (
                    <CheckItem
                      key={`vt-${o.id}`}
                      label={`${o.id} — ${o.nombre}`}
                      checked={datos.variables_tecnico_sel.includes(o.id)}
                      onChange={(v)=> setDatos(prev => {
                        const set = new Set<number>(prev.variables_tecnico_sel);
                        if (v) set.add(o.id); else set.delete(o.id);
                        const unionCompat = new Set<number>([ ...prev.variables_sectorial_sel, ...Array.from(set) ]);
                        return { ...prev, variables_tecnico_sel: Array.from(set), variables_sel: Array.from(unionCompat) };
                      })}
                    />
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Paso 5 */}
        {step===5 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Políticas (máximo 2)</h3>
                <Button size="sm" className="gap-2" disabled={datos.politicas.length >= 2}
                  onClick={()=> setDatos(p=> ({ ...p, politicas: [...p.politicas, { id_politica: null, id_categoria: null, id_subcategoria: null, valor_destinado: 0 }] }))}>
                  <Plus className="h-4 w-4"/> Añadir fila
                </Button>
              </div>

              {datos.politicas.map((row, idx) => (
                <div key={idx} className="grid md:grid-cols-4 gap-3 border rounded-2xl p-3">
                  <div>
                    <Label>Política</Label>
                    <SelectNative
                      value={row.id_politica}
                      onChange={async (id)=> {
                        let opciones_categorias: Opcion[] = [];
                        let opciones_subcategorias: Opcion[] = [];
                        let id_categoria: ID | null = null;
                        let id_subcategoria: ID | null = null;
                        if (id!=null) {
                          try {
                            const r = await fetchJson(`/proyecto/categorias?politica_id=${id}`);
                            opciones_categorias = sortOptions(normalizaFlex(r, ["nombre_categoria", "nombre"]));
                          } catch (e) { console.error(e); }
                        }
                        setDatos(p=>{
                          const arr = [...p.politicas];
                          arr[idx] = { ...arr[idx], id_politica: id, id_categoria, id_subcategoria, opciones_categorias, opciones_subcategorias };
                          return { ...p, politicas: arr };
                        });
                      }}
                      opciones={politicas}
                      placeholder="Selecciona política"
                    />
                  </div>

                  <div>
                    <Label>Categoría</Label>
                    <SelectNative
                      value={row.id_categoria}
                      onChange={async (idCat)=> {
                        let opciones_subcategorias: Opcion[] = [];
                        let id_subcategoria: ID | null = null;
                        if (idCat!=null) {
                          try {
                            const r = await fetchJson(`/proyecto/subcategorias?categoria_id=${idCat}`);
                            opciones_subcategorias = sortOptions(normalizaFlex(r, ["nombre_subcategoria", "nombre"]));
                          } catch (e) { console.error(e); }
                        }
                        setDatos(p=>{
                          const arr = [...p.politicas];
                          arr[idx] = { ...arr[idx], id_categoria: idCat, id_subcategoria, opciones_subcategorias };
                          return { ...p, politicas: arr };
                        });
                      }}
                      opciones={sortOptions(row.opciones_categorias ?? [])}
                      placeholder={row.id_politica ? "Selecciona categoría" : "Primero selecciona política"}
                    />
                  </div>

                  <div>
                    <Label>Subcategoría</Label>
                    <SelectNative
                      value={row.id_subcategoria}
                      onChange={(id)=> setDatos(p=>{ const arr = [...p.politicas]; arr[idx] = { ...arr[idx], id_subcategoria: id }; return { ...p, politicas: arr }; })}
                      opciones={sortOptions(row.opciones_subcategorias ?? [])}
                      placeholder={row.id_categoria ? "Selecciona subcategoría" : "Primero selecciona categoría"}
                    />
                  </div>

                  <div>
                    <Label>Valor destinado</Label>
                    <Input
                      type="text"
                      inputMode="decimal"
                      placeholder="0,00"
                      value={row.valor_ui ?? (row.valor_destinado ? row.valor_destinado.toFixed(2) : "")}
                      onChange={(e) => setDatos((p) => { const arr = [...p.politicas]; arr[idx] = { ...arr[idx], valor_ui: e.target.value }; return { ...p, politicas: arr }; })}
                      onBlur={(e) => {
                        const num = parseDecimal2(e.target.value);
                        setDatos((p) => {
                          const arr = [...p.politicas];
                          if (num !== null) arr[idx] = { ...arr[idx], valor_destinado: num, valor_ui: undefined };
                          else arr[idx] = { ...arr[idx], valor_ui: e.target.value };
                          return { ...p, politicas: arr };
                        });
                      }}
                    />
                    <div className="text-[11px] text-slate-500 mt-1">
                      {toMoney(row.valor_ui !== undefined ? (parseDecimal2(row.valor_ui) ?? row.valor_destinado) : row.valor_destinado)}
                    </div>
                  </div>

                  <div className="md:col-span-4 text-right">
                    <Button size="icon" variant="ghost" onClick={()=> setDatos(p=> ({ ...p, politicas: p.politicas.filter((_,i)=> i!==idx) }))}>
                      <Trash2 className="h-4 w-4"/>
                    </Button>
                  </div>
                </div>
              ))}

              <div className="text-right text-sm text-slate-600">
                Total: <span className="font-semibold">{toMoney(totalPoliticas)}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {step===6 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 space-y-6">
              <div className="space-y-2">
                <h3 className="font-semibold">Viabilidad</h3>
                <div className="border rounded-xl p-3 max-h-72 overflow-auto space-y-1">
                  {viabilidadList.map(o => (
                    <CheckItem
                      key={`via-${o.id}`}
                      label={`${o.id} — ${o.nombre}`}
                      checked={viabilidadesSel.includes(o.id)}
                      onChange={(v)=> setViabilidadesSel(prev=>{
                        const s = new Set(prev);
                        if (v) s.add(o.id); else s.delete(o.id);
                        return Array.from(s);
                      })}
                    />
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <h3 className="font-semibold">Funcionarios por tipo de viabilidad</h3>
                <div className="grid gap-3 md:grid-cols-3">
                  {tiposViabilidad.map(t => {
                    const val = funcionariosViab[t.id] || { nombre:"", cargo:"" };
                    return (
                      <div key={t.id} className="border rounded-xl p-3 space-y-2">
                        <div className="font-medium">{t.nombre}</div>
                        <div className="grid gap-2">
                          <Label>Nombre</Label>
                          <Input
                            value={val.nombre}
                            onChange={(e)=> setFuncionariosViab(p=>({ ...p, [t.id]: { ...p[t.id], nombre:e.target.value } }))}
                            placeholder="Nombre del funcionario"
                          />
                        </div>
                        <div className="grid gap-2">
                          <Label>Cargo</Label>
                          <Input
                            value={val.cargo}
                            onChange={(e)=> setFuncionariosViab(p=>({ ...p, [t.id]: { ...p[t.id], cargo:e.target.value } }))}
                            placeholder="Cargo del funcionario"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Paso 7 */}
          {step === 7 && (
            <div className="w-full">
              <h2 className="text-2xl font-bold mb-6">Descargas</h2>

              {typeof formId === "number" ? (
                <DownloadList
                  formId={formId}
                  baseUrl={import.meta.env.VITE_API_URL ?? ""}
                />
              ) : (
                <div className="text-sm text-gray-600">
                  Guarda el formulario para habilitar las descargas.
                </div>
              )}
            </div>
          )}

        {/* Navegación inferior */}
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={async ()=>{
              if (step>1) { try { await saveStep(step); } catch {} }
              setStep(s=> Math.max(1, s-1));
            }}
          >
            Atrás
          </Button>
            <div className="flex items-center gap-2">
              {step < 7 && (
                <Button
                  onClick={async ()=>{
                    try { await saveStep(step); } catch(e:any){ return alert(e.message || "Error guardando"); }
                    setStep(s=> Math.min(7, s+1));
                  }}
                >
                  Siguiente
                </Button>
              )}
            </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Helpers UI ---------- */
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}
function SelectNative({
  opciones, value, onChange, placeholder,
}: { opciones: Opcion[]; value: ID | null; onChange: (id: ID | null) => void; placeholder?: string; }) {
  return (
    <select className="h-10 w-full rounded-md border px-3 text-sm"
      value={value ?? ""} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}>
      <option value="">{placeholder || "Selecciona"}</option>
      {opciones.map((o) => (<option key={o.id} value={o.id}>{o.nombre}</option>))}
    </select>
  );
}
function CheckItem({ label, checked, onChange }:{ label:string; checked:boolean; onChange:(v:boolean)=>void }) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <input type="checkbox" className="h-4 w-4" checked={checked} onChange={e=>onChange(e.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

type Item = {
  id: string;
  title: string;
  endpoint: string;
  filename: string;
  kind: "word" | "excel";
};

function DownloadList({ formId, baseUrl }: { formId: number | string; baseUrl: string }) {
  const [downloading, setDownloading] = React.useState<string | null>(null);

  const items: Item[] = [
    {
      id: "carta",
      title: "2. Modelo de carta de presentación",
      endpoint: `/descarga/word/carta/${formId}`,
      filename: "2_Carta_de_presentacion.docx",
      kind: "word",
    },
    {
      id: "concepto",
      title: "3. Concepto técnico general y concepto sectorial",
      endpoint: `/descarga/excel/concepto-tecnico-sectorial/${formId}`,
      filename: "3_y_4_Concepto_tecnico_y_sectorial_2025.xlsx",
      kind: "excel",
    },
    {
      id: "cert-precios",
      title: "4. Modelo de certificación de precios",
      endpoint: `/descarga/word/cert-precios/${formId}`,
      filename: "4_Certificacion_de_precios.docx",
      kind: "word",
    },
    {
      id: "no-cofin",
      title: "5. No doble cofinanciación",
      endpoint: `/descarga/word/no-doble-cofin/${formId}`,
      filename: "5_No_doble_cofinanciacion.docx",
      kind: "word",
    },
    {
      id: "cadena",
      title: "6. Cadena de valor",
      endpoint: `/descarga/excel/cadena-valor/${formId}`,
      filename: "6_Cadena_de_valor.xlsx",
      kind: "excel",
    },
    {
      id: "viabilidad",
      title: "7. Viabilidad dependencias",
      endpoint: `/descarga/excel/viabilidad-dependencias/${formId}`,
      filename: "7_Viabilidad_dependencias.xlsx",
      kind: "excel",
    },
  ];

  const handleDownload = async (item: Item) => {
    try {
      setDownloading(item.id);
      const res = await fetch(baseUrl + item.endpoint, { method: "GET" });
      if (!res.ok) throw new Error("Error al descargar");
      const blob = await res.blob();

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = item.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      alert("No fue posible descargar el archivo.");
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-6">
      {items.map((item) => (
        <div
          key={item.id}
          className="flex items-center justify-between gap-4 border-b pb-4"
        >
          {/* Izquierda: icono + título*/}
          <div className="flex-1">
            <div className="flex items-start gap-3">
              <div className="shrink-0 mt-1">
                {item.kind === "word" ? <WordIcon /> : <ExcelIcon />}
              </div>
              <div>
                <div className="text-[15px] text-green-700 hover:underline font-medium">
                  {item.title}
                </div>
              </div>
            </div>
          </div>

          {/* Derecha: botón Descarga*/}
          <div className="shrink-0">
            <button
              onClick={() => handleDownload(item)}
              disabled={downloading === item.id}
              className="px-4 h-10 rounded-md bg-green-700 text-white font-semibold hover:bg-green-800 disabled:opacity-60"
            >
              {downloading === item.id ? "Descargando..." : "Descarga"}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function WordIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" className="text-blue-700">
      <rect x="3" y="2" width="14" height="20" rx="2" fill="#e9f2ff" />
      <rect x="7" y="6" width="10" height="2" fill="#1d4ed8" />
      <rect x="7" y="10" width="10" height="2" fill="#1d4ed8" />
      <rect x="7" y="14" width="7" height="2" fill="#1d4ed8" />
    </svg>
  );
}

function ExcelIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" className="text-green-700">
      <rect x="3" y="2" width="14" height="20" rx="2" fill="#ecfdf5" />
      <rect x="7" y="6" width="10" height="2" fill="#047857" />
      <rect x="7" y="10" width="10" height="2" fill="#047857" />
      <rect x="7" y="14" width="10" height="2" fill="#047857" />
    </svg>
  );
}
