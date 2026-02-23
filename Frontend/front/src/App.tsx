import React, { useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Loader2, Plus, Trash2, Download, ArrowLeft, PlusCircle, Search, RefreshCcw } from "lucide-react";

type ID = number;
interface Opcion { id: ID; nombre: string; codigo?: number | null; }
type EntidadFin = "DEPARTAMENTO" | "PROPIOS" | "SGP_LIBRE_INVERSION" | "SGP_LIBRE_DESTINACION" | "SGP_APSB" | "SGP_EDUCACION" | "SGP_ALIMENTACION_ESCOLAR" | "SGP_CULTURA" | "SGP_DEPORTE" | "SGP_SALUD" | "MUNICIPIO" | "NACION" | "OTROS";

const isSGP = (e: EntidadFin) => e.startsWith("SGP_");

function uiNumber(raw: string | undefined) {
  const n = parseDecimal2(raw ?? "");
  return n ?? 0;
}

function calcDepartamentoForYear(efUI: Record<string,string|undefined>, y:number) {
  const propios = uiNumber(efUI[keyFin(y, "PROPIOS")]);
  const sgps = [
    "SGP_LIBRE_INVERSION","SGP_LIBRE_DESTINACION","SGP_APSB",
    "SGP_EDUCACION","SGP_ALIMENTACION_ESCOLAR","SGP_CULTURA",
    "SGP_DEPORTE","SGP_SALUD",
  ] as EntidadFin[];
  const sumSgps = sgps.reduce((a, ent) => a + uiNumber(efUI[keyFin(y, ent)]), 0);
  return round2(propios + sumSgps);
}

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
  cargo_responsable: string;
  nombre_secretario: string;
  fuentes: string;
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
    let codigo: number | null = null;
    if (campoCodigo) {
      const c = Number(x[campoCodigo as keyof typeof x]);
      codigo = Number.isFinite(c) ? c : null;
    }
    return {
      id: Number(x.id ?? x.id_dependencia ?? x.codigo ?? x.cod_id_mga ?? 0),
      nombre: String(x[nombreKey] ?? x.nombre ?? x.dependencia ?? ""),
      codigo,
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
  const t0 = (raw ?? "").trim();
  if (t0 === "") return 0;
  const t = t0.replace(/\s+/g, "").replace(/\./g, "").replace(",", ".");
  if (!/^\d*(?:\.\d{0,2})?$/.test(t)) return null;
  const num = Number(t);
  return Number.isFinite(num) ? round2(num) : null;
}
function sanitizeMoneyInput(raw: string): string {
  if (!raw) return "";
  let t = raw.replace(/\s+/g, "");
  const hadTrailingComma = t.endsWith(",");
  const parts = t.split(",");
  if (parts.length > 2) {
    t = parts[0] + "," + parts.slice(1).join("").replace(/,/g, "");
  }
  t = t.replace(/\./g, "");
  const [intPart, decPart = ""] = t.split(",");
  let dec = decPart;
  if (dec.length > 2) dec = dec.slice(0, 2);
  if (hadTrailingComma && dec === "") {
    return intPart + ",";
  }
  return dec ? `${intPart},${dec}` : intPart;
}
function formatMiles(value?: string | number) {
  if (value == null || value === "") return "";
  let num: number | null = null;
  if (typeof value === "number") {
    num = value;
  } else {
    num = parseDecimal2(value);
  }
  if (num == null) return "";
  const hasDecimals = !Number.isInteger(num);
  return num.toLocaleString("es-CO", {
    minimumFractionDigits: hasDecimals ? 2 : 0,
    maximumFractionDigits: 2,
  });
}
function formatInputMiles(value: string): string {
  if (!value) return "";
  const hasComma = value.includes(",");
  let [intPart, decPart] = value.split(",");
  intPart = intPart.replace(/\./g, "");
  intPart = Number(intPart).toLocaleString("es-CO");
  if (hasComma) {
    return decPart !== undefined ? `${intPart},${decPart}` : `${intPart},`;
  }

  return intPart;
}
function normalizeMoney(value: string): string {
  if (!value) return "";
  value = value.replace(/\./g, "");
  value = value.replace(",", ".");
  const num = Number(value);
  if (isNaN(num)) return "";
  return num.toLocaleString("es-CO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function numbersEqual(a: number, b: number) { return Math.abs(a - b) < 0.005; }
function keyFin(anio: number, entidad: EntidadFin) { return `${anio}|${entidad}`; }
function getYears(anio_inicio?: number | null): number[] {
  if (!anio_inicio || anio_inicio < 1900 || anio_inicio > 3000) return [];
  return [anio_inicio, anio_inicio + 1, anio_inicio + 2, anio_inicio + 3];
}

/* ---------- Lista ---------- */
type ProyectoListaItemFlex = Record<string, any> & { nombre?: string; nombre_proyecto?: string; cod_id_mga?: number; id_dependencia?: number; dependencia_id?: number };
type RolApp = "dependencia" | "radicador" | "evaluador";
type DocEvaluador = "observaciones" | "viabilidad" | "viabilidad_ajustada";

interface ProyectoEvaluador {
  id: number | null;
  nombre: string;
  codMGA: string;
  dependencia: string;
}

interface ObservacionEvaluacionItem {
  id: number;
  id_formulario: number;
  tipo_documento: "OBSERVACIONES" | "VIABILIDAD" | "VIABILIDAD_AJUSTADA";
  contenido_html: string;
  nombre_evaluador: string;
  cargo_evaluador?: string | null;
  indicadores_objetivo?: IndicadorObjetivoItem[];
  concepto_tecnico_favorable_dep?: "SI" | "NO" | null;
  concepto_sectorial_favorable_dep?: "SI" | "NO" | null;
  proyecto_viable_dep?: "SI" | "NO" | null;
  created_at: string;
}

interface IndicadorObjetivoItem {
  indicador_objetivo_general: string;
  unidad_medida: string;
  meta_resultado: string;
}

interface MetaPddEvaluadorItem {
  id: number;
  numero_meta: number | string;
  nombre_meta: string;
}

interface MedicionAjustadaItem {
  descripcion: string;
  unidad_medida: string;
  meta_programada: string;
  meta_alcanzada: string;
}

type SiNo = "" | "SI" | "NO";

interface RadicacionState {
  numero_radicacion: string;
  fecha_radicacion: string;
  bpin: string;
  soportes_folios: number;
  soportes_planos: number;
  soportes_cds: number;
  soportes_otros: number;
}

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

function sanitizeSearchTerm(raw: string): string {
  return (raw || "")
    .replace(/data:image\/[a-zA-Z]+;base64,[A-Za-z0-9+/=]+/g, " ")
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .slice(0, 180);
}

function todayISODate(): string {
  return new Date().toISOString().slice(0, 10);
}

/* ========== Componente principal ========== */
export default function App() {
  const [vista, setVista] = useState<"home" | "lista" | "form" | "evaluador_doc">("home");
  const [rol, setRol] = useState<RolApp | null>(null);
  const [docEvaluador, setDocEvaluador] = useState<DocEvaluador | null>(null);
  const [proyectoEvaluador, setProyectoEvaluador] = useState<ProyectoEvaluador | null>(null);
  const [contenidoEvaluador, setContenidoEvaluador] = useState("");
  const [nombreEvaluador, setNombreEvaluador] = useState("");
  const [cargoEvaluador, setCargoEvaluador] = useState("");
  const [fechaEvaluador, setFechaEvaluador] = useState(todayISODate());
  const [conceptoTecnicoDep, setConceptoTecnicoDep] = useState<SiNo>("");
  const [conceptoSectorialDep, setConceptoSectorialDep] = useState<SiNo>("");
  const [proyectoViableDep, setProyectoViableDep] = useState<SiNo>("");
  const [indicadoresObjetivo, setIndicadoresObjetivo] = useState<IndicadorObjetivoItem[]>([
    { indicador_objetivo_general: "", unidad_medida: "", meta_resultado: "" },
  ]);
  const [productosAjustados, setProductosAjustados] = useState<MedicionAjustadaItem[]>([
    { descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" },
  ]);
  const [resultadosAjustados, setResultadosAjustados] = useState<MedicionAjustadaItem[]>([
    { descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" },
  ]);
  const [metasProyectoById, setMetasProyectoById] = useState<Record<number, string>>({});
  const [metasPddEvaluador, setMetasPddEvaluador] = useState<MetaPddEvaluadorItem[]>([]);
  const [editorFontSizePx, setEditorFontSizePx] = useState("14");
  const editorRef = useRef<HTMLDivElement | null>(null);
  const imageInputRef = useRef<HTMLInputElement | null>(null);
  const selectedImageRef = useRef<HTMLImageElement | null>(null);
  const [openRadicacion, setOpenRadicacion] = useState(false);
  const [radicacionLoading, setRadicacionLoading] = useState(false);
  const [radicacionSaving, setRadicacionSaving] = useState(false);
  const [radicacionFormId, setRadicacionFormId] = useState<number | null>(null);
  const [radicacionProyecto, setRadicacionProyecto] = useState<string>("");
  const [radicacionState, setRadicacionState] = useState<RadicacionState>({
    numero_radicacion: "",
    fecha_radicacion: todayISODate(),
    bpin: "",
    soportes_folios: 0,
    soportes_planos: 0,
    soportes_cds: 0,
    soportes_otros: 0,
  });

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
  const [varsSectorialResp, setVarsSectorialResp] = useState<VarResp[]>([]);
  const [varsTecnicoResp, setVarsTecnicoResp]   = useState<VarResp[]>([]);
  const [viabResp, setViabResp]                 = useState<VarResp[]>([]);

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

  type Respuesta = "SI" | "NO" | "N/A" | "";
  type VarResp = { id:number; nombre:string; no_aplica:boolean; respuesta?:Respuesta };
  
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
      cargo_responsable: "",
      nombre_secretario: "",
      fuentes: "",
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
      const sum =
        calcDepartamentoForYear(datos.estructura_financiera_ui, anio) +
        uiNumber(datos.estructura_financiera_ui[keyFin(anio, "MUNICIPIO")]) +
        uiNumber(datos.estructura_financiera_ui[keyFin(anio, "NACION")]) +
        uiNumber(datos.estructura_financiera_ui[keyFin(anio, "OTROS")] );
      out[anio] = round2(sum);
    });
    return out;
  }, [datos.estructura_financiera_ui, years]);
  const totalProyecto = useMemo(() => round2(years.reduce((acc, anio) => acc + (totalesAnio[anio] ?? 0), 0)), [years, totalesAnio]);
  const difProyectoPoliticas = useMemo(() => round2(totalProyecto - totalPoliticas), [totalProyecto, totalPoliticas]);
  const igualesProyectoPoliticas = numbersEqual(totalProyecto, totalPoliticas);
  const varsSectorialRespSorted = useMemo(() => [...varsSectorialResp].sort((a,b) => a.id - b.id), [varsSectorialResp]);
  const varsTecnicoRespSorted = useMemo(() => [...varsTecnicoResp].sort((a,b) => a.id - b.id), [varsTecnicoResp]);
  const viabRespSorted = useMemo(() => [...viabResp].sort((a,b) => a.id - b.id), [viabResp]);
  const tiposViabilidadSorted = useMemo(() => [...tiposViabilidad].sort((a,b) => a.id - b.id), [tiposViabilidad]);


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
  
  // Variables (sectorial / técnico)
  useEffect(() => {
    if (vista !== "form" || step !== 4) return;

    (async () => {
      try {
        const id = formId ?? (await ensureFormId().catch(() => null));
        if (!id) return;

        const [vsr, vtr] = await Promise.all([
          fetchJson(`/proyecto/formulario/${id}/variables-sectorial-respuestas`),
          fetchJson(`/proyecto/formulario/${id}/variables-tecnico-respuestas`),
        ]);

        setVarsSectorialResp(vsr);
        setVarsTecnicoResp(vtr);
      } catch (e) {
        console.error("Error cargando respuestas de variables", e);
      }
    })();
  }, [vista, step, formId]);

  // Viabilidades
  useEffect(() => {
    if (vista !== "form" || step !== 6) return;

    (async () => {
      try {
        const id = formId ?? (await ensureFormId().catch(() => null));
        if (!id) return;

        const vbr = await fetchJson(`/proyecto/formulario/${id}/viabilidades-respuestas`);
        setViabResp(vbr);
      } catch (e) {
        console.error("Error cargando respuestas de viabilidad", e);
      }
    })();
  }, [vista, step, formId]);

  // Sectores por línea
  useEffect(() => {
    const idLinea = datos.datos_basicos.id_linea_estrategica;
    if (!idLinea) { setSectores([]); return; }
    (async () => {
      try {
        const r = await fetchJson(`/proyecto/sectores?linea_id=${idLinea}`);
        const raw = normalizaFlex(r, ["nombre_sector", "nombre"], "codigo_sector");
        setSectores(sortOptions(raw).map(o => ({...o, nombre: (o.codigo != null ? `${o.codigo} - ${o.nombre}` : o.nombre)})));
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
        const raw = normalizaFlex(r, ["nombre_programa", "nombre"], "codigo_programa");
        setProgramas(sortOptions(raw).map(o => ({...o, nombre: (o.codigo != null ? `${o.codigo} - ${o.nombre}` : o.nombre)})));
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
        const arr = Array.isArray(r) ? r : (r?.items ?? r?.data ?? r?.results ?? []);
        const ops = sortOptions(normalizaFlex(arr, ["nombre_meta", "nombre"], "numero_meta"));
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
        if (ent === "DEPARTAMENTO") return;
        const raw = state.estructura_financiera_ui[keyFin(anio, ent)] ?? "";
        const num = parseDecimal2(raw);
        estructura_financiera.push({ anio, entidad: ent, valor: num ?? 0 });
      });
      const sumDept = estructura_financiera
        .filter(r => r.anio === anio && (
          r.entidad === "PROPIOS" ||
          r.entidad.startsWith("SGP_")
        ))
        .reduce((a, b) => a + (b.valor ?? 0), 0);
      estructura_financiera.push({ anio, entidad: "DEPARTAMENTO", valor: sumDept });
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
        cargo_responsable: datos.datos_basicos.cargo_responsable ?? "",
        nombre_secretario: datos.datos_basicos.nombre_secretario ?? "",
        fuentes: datos.datos_basicos.fuentes ?? "",
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
      const metasPayload = (payload.metas || []).map((id_meta) => ({
        id_meta,
        meta_proyecto: (metasProyectoById[id_meta] || "").trim() || null,
      }));
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/metas`, {
        method:"PUT", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ metas: metasPayload }),
      });
    }
    if (which === 3) {
      const ys = getYears(datos.anio_inicio);
      const filas: Array<{anio:number; entidad:EntidadFin; valor:number}> = [];

      ys.forEach(anio => {
        ENTIDADES.forEach(ent => {
          if (ent === "DEPARTAMENTO") return;
          const raw = datos.estructura_financiera_ui[keyFin(anio, ent)] ?? "";
          const num = parseDecimal2(raw) ?? 0;
          filas.push({ anio, entidad: ent, valor: num });
        });
        const dep = calcDepartamentoForYear(datos.estructura_financiera_ui, anio);
        filas.push({ anio, entidad: "DEPARTAMENTO", valor: dep });
      });
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/estructura-financiera`, {
        method:"PUT",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ filas }),
      });
    }
    if (which === 4) {
      const id = await ensureFormId();
      const bodySec = {
        respuestas: varsSectorialResp
          .filter(v => (v.respuesta ?? "") !== "")
          .map(v => ({ id: v.id, respuesta: v.respuesta }))
      };
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/variables-sectorial-respuestas`, {
        method:"PUT", headers:{"Content-Type":"application/json"}, body: JSON.stringify(bodySec)
      });

      const bodyTec = {
        respuestas: varsTecnicoResp
          .filter(v => (v.respuesta ?? "") !== "")
          .map(v => ({ id: v.id, respuesta: v.respuesta }))
      };
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/variables-tecnico-respuestas`, {
        method:"PUT", headers:{"Content-Type":"application/json"}, body: JSON.stringify(bodyTec)
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
      const id = await ensureFormId();

      const bodyV = {
        respuestas: viabResp
          .filter(v => (v.respuesta ?? "") !== "")
          .map(v => ({ id: v.id, respuesta: v.respuesta }))
      };
      await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${id}/viabilidades-respuestas`, {
        method:"PUT", headers:{"Content-Type":"application/json"}, body: JSON.stringify(bodyV)
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

  async function openFromRow(p: ProyectoListaItemFlex) {
    const rid = getRowId(p);
    if (rid != null) {
      setFormId(rid);
      setVista("form");
      await loadForm(rid);
      return;
    }

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

  async function loadForm(id: number) {
    try {
      const r = await fetchJson(`/proyecto/formulario/${id}`);
      const nombre_proyecto = r.nombre_proyecto ?? r.nombre ?? "";
      const cod_id_mga = Number(r.cod_id_mga ?? r.cod_mga ?? r.codigo_mga ?? 0);
      const efUI: Record<string, string> = {};
      let minAnio: number | null = null;
      const efArr: any[] = Array.isArray(r.estructura_financiera) ? r.estructura_financiera : [];
      efArr.forEach((row: any) => {
        const anio = Number(row.anio ?? row.year ?? NaN);
        const ent = (row.entidad ?? row.fuente) as EntidadFin;
        const valNum = Number(row.valor ?? row.monto ?? 0);
        if (!Number.isFinite(anio) || !ent) return;
        const isInt = Math.abs(valNum - Math.round(valNum)) < 0.005;
        const uiStr = valNum
          ? (isInt ? String(Math.round(valNum)) : valNum.toFixed(2).replace(".", ","))
          : "";
        const k = `${anio}|${ent}`;
        efUI[k] = uiStr;
        if (minAnio == null || anio < minAnio) minAnio = anio;
      });
      const metasSel = (Array.isArray(r.metas) ? r.metas : []).map((m: any) =>
        Number(m.id ?? m.id_meta ?? m.meta_id ?? m.codigo)
      ).filter(Number.isFinite);
      const metasProyectoMap = Object.fromEntries(
        (Array.isArray(r.metas) ? r.metas : [])
          .map((m: any) => [Number(m.id ?? m.id_meta ?? m.meta_id), String(m.meta_proyecto ?? "")])
          .filter(([id]) => Number.isFinite(id))
      ) as Record<number, string>;
      const varsSecSel = (r.variables_sectorial || r.variables_sectoriales || []).map((v: any) =>
        Number(v.id ?? v.id_variable ?? v.variable_id)
      ).filter(Number.isFinite);
      const varsTecSel = (r.variables_tecnico || r.variables_tecnicas || []).map((v: any) =>
        Number(v.id ?? v.id_variable ?? v.variable_id)
      ).filter(Number.isFinite);
      const viaSel = (Array.isArray(r.viabilidades) ? r.viabilidades : []).map((v:any) =>
        Number(v.id ?? v.id_viabilidad ?? v.viabilidad_id)
      ).filter(Number.isFinite);
      const funcs = Object.fromEntries(
        (Array.isArray(r.funcionarios_viabilidad) ? r.funcionarios_viabilidad : [])
          .map((f:any) => [Number(f.id_tipo_viabilidad), {
            nombre: String(f.nombre || ""),
            cargo:  String(f.cargo  || ""),
          }])
      );
      const politicasSrc: any[]     = Array.isArray(r.politicas)     ? r.politicas     : [];
      const categoriasSrc: any[]    = Array.isArray(r.categorias)    ? r.categorias    : [];
      const subcategoriasSrc: any[] = Array.isArray(r.subcategorias) ? r.subcategorias : [];
      const basePolitRows: PoliticaFila[] = politicasSrc.slice(0, 2).map((p: any) => {
        const id_politica = Number(p.id ?? p.id_politica ?? 0) || null;
        const catSel = categoriasSrc.find(
          (c: any) => Number(c.id_politica) === Number(id_politica)
        );
        const id_categoria = catSel ? Number(catSel.id) : null;
        const subSel = id_categoria
          ? subcategoriasSrc.find((s: any) => Number(s.id_categoria) === Number(id_categoria))
          : null;
        const id_subcategoria = subSel ? Number(subSel.id) : null;
        const valor_destinado = Number(p.valor_destinado ?? 0);
        return {
          id_politica,
          id_categoria,
          id_subcategoria,
          valor_destinado,
          opciones_categorias: [],
          opciones_subcategorias: [],
        } as PoliticaFila;
      });
      const politRows: PoliticaFila[] = await Promise.all(
        basePolitRows.map(async (row) => {
          let opciones_categorias: Opcion[] = [];
          let opciones_subcategorias: Opcion[] = [];

          if (row.id_politica) {
            try {
              const cats = await fetchJson(`/proyecto/categorias?politica_id=${row.id_politica}`);
              opciones_categorias = sortOptions(normalizaFlex(cats, ["nombre_categoria", "nombre"]));
            } catch { /* noop */ }
          }
          if (row.id_categoria) {
            try {
              const subs = await fetchJson(`/proyecto/subcategorias?categoria_id=${row.id_categoria}`);
              opciones_subcategorias = sortOptions(normalizaFlex(subs, ["nombre_subcategoria", "nombre"]));
            } catch { /* noop */ }
          }
          return { ...row, opciones_categorias, opciones_subcategorias };
        })
      );
      const politRowsFinal = politRows.length
        ? politRows
        : [{
            id_politica: null,
            id_categoria: null,
            id_subcategoria: null,
            valor_destinado: 0,
            opciones_categorias: [],
            opciones_subcategorias: [],
          }];
      setViabilidadesSel(viaSel);
      setFuncionariosViab(funcs);
      setMetasProyectoById(metasProyectoMap);
      setDatos(prev => ({
        ...prev,
        datos_basicos: {
          ...prev.datos_basicos,
          nombre_proyecto,
          cod_id_mga,
          id_dependencia:       r.id_dependencia       ?? prev.datos_basicos.id_dependencia ?? null,
          id_linea_estrategica: r.id_linea_estrategica ?? prev.datos_basicos.id_linea_estrategica ?? null,
          id_sector:            r.id_sector            ?? prev.datos_basicos.id_sector ?? null,
          id_programa:          r.id_programa          ?? prev.datos_basicos.id_programa ?? null,
          cargo_responsable:    r.cargo_responsable    ?? prev.datos_basicos.cargo_responsable ?? "",
          nombre_secretario:    r.nombre_secretario    ?? prev.datos_basicos.nombre_secretario ?? "",
          fuentes:              r.fuentes              ?? prev.datos_basicos.fuentes ?? "",
          duracion_proyecto:    r.duracion_proyecto    ?? prev.datos_basicos.duracion_proyecto ?? 0,
          cantidad_beneficiarios: r.cantidad_beneficiarios ?? prev.datos_basicos.cantidad_beneficiarios ?? 0,
        },
        metas_sel: metasSel,
        politicas: politRowsFinal,
        variables_sectorial_sel: varsSecSel,
        variables_tecnico_sel:   varsTecSel,
        variables_sel: Array.from(new Set([...varsSecSel, ...varsTecSel])),
        anio_inicio: minAnio,
        estructura_financiera_ui: efUI,
      }));
      const [vsr, vtr, vbr] = await Promise.all([
        fetchJson(`/proyecto/formulario/${id}/variables-sectorial-respuestas`),
        fetchJson(`/proyecto/formulario/${id}/variables-tecnico-respuestas`),
        fetchJson(`/proyecto/formulario/${id}/viabilidades-respuestas`),
      ]);
      setVarsSectorialResp(vsr);
      setVarsTecnicoResp(vtr);
      setViabResp(vbr);
      setStep(1);
    } catch (e) {
      console.error("No se pudo cargar el formulario", e);
      alert("No se pudo cargar el formulario seleccionado.");
    }
  }

  function initialDocContent(tipo: DocEvaluador): string {
    if (tipo === "viabilidad") {
      return "<p><strong>MOTIVACION DE LA VIABILIDAD:</strong></p><p><br></p>";
    }
    if (tipo === "viabilidad_ajustada") {
      return "<p><strong>MOTIVACION DE LA VIABILIDAD AJUSTADA:</strong></p><p><br></p>";
    }
    return "<p><strong>EVALUANDO EL PROYECTO, SE HACEN LAS SIGUIENTES OBSERVACIONES:</strong></p><p><br></p>";
  }

  function setSelectedEditorImage(img: HTMLImageElement | null) {
    if (selectedImageRef.current) {
      selectedImageRef.current.style.outline = "";
    }
    selectedImageRef.current = img;
    if (img) {
      img.style.outline = "2px solid #64748b";
      img.style.outlineOffset = "2px";
    }
  }

  function updateEditorContentFromDom() {
    if (!editorRef.current) return;
    setContenidoEvaluador(editorRef.current.innerHTML);
  }

  function resizeSelectedImage(factor: number) {
    const img = selectedImageRef.current;
    if (!img) {
      alert("Selecciona una imagen en el editor.");
      return;
    }
    const current = img.clientWidth || parseInt(img.style.width || "0", 10) || img.naturalWidth || 300;
    const next = Math.max(80, Math.min(1200, Math.round(current * factor)));
    img.style.width = `${next}px`;
    img.style.height = "auto";
    img.style.maxWidth = "100%";
    updateEditorContentFromDom();
  }

  function fitSelectedImage() {
    const img = selectedImageRef.current;
    if (!img) {
      alert("Selecciona una imagen en el editor.");
      return;
    }
    img.style.width = "100%";
    img.style.height = "auto";
    img.style.maxWidth = "100%";
    updateEditorContentFromDom();
  }

  async function openEvaluadorDoc(p: ProyectoListaItemFlex, tipo: DocEvaluador) {
    const rowId = getRowId(p);
    const nombreFila = String(p.nombre ?? p.nombre_proyecto ?? "(sin nombre)");
    const codFila = String(p.cod_id_mga ?? p.cod_mga ?? p.codigo_mga ?? "");
    const depFila = p.id_dependencia ?? p.dependencia_id;
    const depNombre = deps.find(x => x.id === depFila)?.nombre ?? String(depFila ?? "");

    setProyectoEvaluador({
      id: rowId,
      nombre: nombreFila,
      codMGA: codFila,
      dependencia: depNombre,
    });
    setDocEvaluador(tipo);
    const baseContent = initialDocContent(tipo);
    setContenidoEvaluador(baseContent);
    setNombreEvaluador("");
    setCargoEvaluador("");
    setFechaEvaluador(todayISODate());
    setConceptoTecnicoDep("");
    setConceptoSectorialDep("");
    setProyectoViableDep("");
    setIndicadoresObjetivo([{ indicador_objetivo_general: "", unidad_medida: "", meta_resultado: "" }]);
    setProductosAjustados([{ descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" }]);
    setResultadosAjustados([{ descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" }]);
    setMetasProyectoById({});
    setMetasPddEvaluador([]);
    setSelectedEditorImage(null);
    setVista("evaluador_doc");
    setTimeout(() => {
      if (editorRef.current) editorRef.current.innerHTML = baseContent;
    }, 0);

    if (!rowId) return;
    try {
      try {
        const form = await fetchJson(`/proyecto/formulario/${rowId}`);
        const metasForm = Array.isArray(form?.metas) ? form.metas : [];
        setMetasPddEvaluador(
          metasForm.map((m: any) => ({
            id: Number(m.id ?? m.id_meta ?? m.meta_id ?? 0),
            numero_meta: m.numero_meta ?? m.codigo ?? "",
            nombre_meta: String(m.nombre_meta ?? m.nombre ?? ""),
          })).filter((m: MetaPddEvaluadorItem) => Number.isFinite(m.id) && m.id > 0)
        );
        setMetasProyectoById(
          Object.fromEntries(
            metasForm.map((m: any) => [
              Number(m.id ?? m.id_meta ?? m.meta_id ?? 0),
              String(m.meta_proyecto ?? ""),
            ]).filter(([id]: [number, string]) => Number.isFinite(id) && id > 0)
          ) as Record<number, string>
        );
      } catch {
        // Si falla esta carga, igual permitimos abrir el documento.
      }

      const res = await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${rowId}/observaciones`);
      if (!res.ok) return;
      const data: ObservacionEvaluacionItem[] = await res.json();
      const tipoDb =
        tipo === "viabilidad"
          ? "VIABILIDAD"
          : tipo === "viabilidad_ajustada"
            ? "VIABILIDAD_AJUSTADA"
            : "OBSERVACIONES";
      const ultimo = data.find((x) => x.tipo_documento === tipoDb);
      if (!ultimo) return;
      setContenidoEvaluador(ultimo.contenido_html || baseContent);
      setNombreEvaluador(ultimo.nombre_evaluador || "");
      setCargoEvaluador(String(ultimo.cargo_evaluador || ""));
      setFechaEvaluador(todayISODate());
      setConceptoTecnicoDep((ultimo.concepto_tecnico_favorable_dep as SiNo) || "");
      setConceptoSectorialDep((ultimo.concepto_sectorial_favorable_dep as SiNo) || "");
      setProyectoViableDep((ultimo.proyecto_viable_dep as SiNo) || "");
      const indicadoresGuardados = Array.isArray(ultimo.indicadores_objetivo)
        ? ultimo.indicadores_objetivo
            .map((x) => ({
              indicador_objetivo_general: String(x?.indicador_objetivo_general ?? ""),
              unidad_medida: String(x?.unidad_medida ?? ""),
              meta_resultado: String(x?.meta_resultado ?? ""),
            }))
            .filter((x) => x.indicador_objetivo_general || x.unidad_medida || x.meta_resultado)
        : [];
      setIndicadoresObjetivo(
        tipo === "viabilidad" && indicadoresGuardados.length
          ? indicadoresGuardados
          : [{ indicador_objetivo_general: "", unidad_medida: "", meta_resultado: "" }]
      );
      setProductosAjustados([{ descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" }]);
      setResultadosAjustados([{ descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" }]);
      setTimeout(() => {
        if (editorRef.current) editorRef.current.innerHTML = ultimo.contenido_html || baseContent;
      }, 0);
    } catch {
      // Si falla la consulta, dejamos el contenido base.
    }
  }

  async function ensureRowFormId(p: ProyectoListaItemFlex): Promise<number | null> {
    const rid = getRowId(p);
    if (rid != null) return rid;

    const nombre = String(p.nombre ?? p.nombre_proyecto ?? "").trim();
    const cod = Number(p.cod_id_mga ?? p.cod_mga ?? p.codigo_mga ?? NaN);
    const dep = Number(p.id_dependencia ?? p.dependencia_id ?? NaN);
    if (!Number.isFinite(cod) || !Number.isFinite(dep)) return null;

    const r = await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/minimo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nombre_proyecto: nombre || `Proyecto ${cod}`,
        cod_id_mga: Number(cod),
        id_dependencia: Number(dep),
      }),
    });
    if (!r.ok) return null;
    const j = await r.json();
    const id = Number(j.id);
    return Number.isFinite(id) ? id : null;
  }

  async function openRadicacionModal(p: ProyectoListaItemFlex) {
    try {
      setRadicacionLoading(true);
      const formId = await ensureRowFormId(p);
      if (!formId) {
        alert("No se pudo obtener el proyecto para radicar.");
        return;
      }
      const form = await fetchJson(`/proyecto/formulario/${formId}`);
      setRadicacionFormId(formId);
      setRadicacionProyecto(String(form?.nombre_proyecto ?? p.nombre ?? p.nombre_proyecto ?? ""));
      setRadicacionState({
        numero_radicacion: String(form?.numero_radicacion ?? ""),
        fecha_radicacion: String(form?.fecha_radicacion ?? "") || todayISODate(),
        bpin: String(form?.bpin ?? ""),
        soportes_folios: Number(form?.soportes_folios ?? 0) || 0,
        soportes_planos: Number(form?.soportes_planos ?? 0) || 0,
        soportes_cds: Number(form?.soportes_cds ?? 0) || 0,
        soportes_otros: Number(form?.soportes_otros ?? 0) || 0,
      });
      setOpenRadicacion(true);
    } catch {
      alert("No se pudo cargar la radicacion del proyecto.");
    } finally {
      setRadicacionLoading(false);
    }
  }

  async function saveRadicacion() {
    if (!radicacionFormId) {
      alert("No hay proyecto seleccionado.");
      return;
    }
    try {
      setRadicacionSaving(true);
      const res = await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${radicacionFormId}/radicacion`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          numero_radicacion: radicacionState.numero_radicacion,
          fecha_radicacion: radicacionState.fecha_radicacion || todayISODate(),
          bpin: radicacionState.bpin,
          soportes_folios: Math.max(0, Number(radicacionState.soportes_folios || 0)),
          soportes_planos: Math.max(0, Number(radicacionState.soportes_planos || 0)),
          soportes_cds: Math.max(0, Number(radicacionState.soportes_cds || 0)),
          soportes_otros: Math.max(0, Number(radicacionState.soportes_otros || 0)),
        }),
      });
      if (!res.ok) {
        const err = await res.text().catch(() => "");
        throw new Error(err || "No se pudo guardar la radicacion.");
      }
      setOpenRadicacion(false);
      await queryLista(false);
    } catch (e: any) {
      alert(e?.message || "Error guardando radicacion.");
    } finally {
      setRadicacionSaving(false);
    }
  }

  function applyEditorCommand(command: string, value?: string) {
    if (!editorRef.current) return;
    editorRef.current.focus();
    document.execCommand(command, false, value);
    setContenidoEvaluador(editorRef.current.innerHTML);
  }

  function applyEditorFontSize(px: string) {
    if (!editorRef.current) return;
    setEditorFontSizePx(px);
    editorRef.current.focus();
    document.execCommand("styleWithCSS", false, true);
    document.execCommand("fontSize", false, "7");
    editorRef.current.querySelectorAll('font[size="7"]').forEach((node) => {
      const span = document.createElement("span");
      span.style.fontSize = `${px}px`;
      span.innerHTML = node.innerHTML;
      node.replaceWith(span);
    });
    setContenidoEvaluador(editorRef.current.innerHTML);
  }

  function applyBulletList() {
    applyEditorCommand("insertUnorderedList");
    if (!editorRef.current) return;
    editorRef.current.querySelectorAll("ul").forEach((ul) => {
      (ul as HTMLUListElement).style.listStyleType = "disc";
      (ul as HTMLUListElement).style.paddingLeft = "1.5rem";
    });
    setContenidoEvaluador(editorRef.current.innerHTML);
  }

  function onImageSelected(file?: File) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const src = String(reader.result ?? "");
      if (!src) return;
      applyEditorCommand("insertImage", src);
      if (editorRef.current) {
        const imgs = editorRef.current.querySelectorAll("img");
        const last = imgs[imgs.length - 1] as HTMLImageElement | undefined;
        if (last) {
          last.style.maxWidth = "100%";
          last.style.height = "auto";
          last.style.width = "480px";
          setSelectedEditorImage(last);
          updateEditorContentFromDom();
        }
      }
      if (imageInputRef.current) imageInputRef.current.value = "";
    };
    reader.readAsDataURL(file);
  }

  function htmlHasUserContent(html: string) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    return (tmp.textContent || "").trim().length > 0 || tmp.querySelector("img") != null;
  }

  async function guardarRegistroEvaluador(
    tipo: "OBSERVACIONES" | "VIABILIDAD" | "VIABILIDAD_AJUSTADA",
    html: string
  ) {
    const formId = proyectoEvaluador?.id;
    if (!formId) {
      throw new Error("No se encontro un formulario valido para guardar la observacion.");
    }

    if (tipo === "VIABILIDAD" && metasPddEvaluador.length) {
      const metasPayload = metasPddEvaluador.map((m) => ({
        id_meta: m.id,
        meta_proyecto: (metasProyectoById[m.id] || "").trim() || null,
      }));
      const metasRes = await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${formId}/metas`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ metas: metasPayload }),
      });
      if (!metasRes.ok) {
        const err = await metasRes.text().catch(() => "");
        throw new Error(err || "No se pudo guardar la meta del proyecto.");
      }
    }

    const res = await fetch(`${API_BASE_DEFAULT}/proyecto/formulario/${formId}/observaciones`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tipo_documento: tipo,
        contenido_html: html,
        nombre_evaluador: nombreEvaluador.trim(),
        cargo_evaluador: cargoEvaluador.trim(),
        indicadores_objetivo: tipo === "VIABILIDAD"
          ? indicadoresObjetivo
              .map((x) => ({
                indicador_objetivo_general: (x.indicador_objetivo_general || "").trim(),
                unidad_medida: (x.unidad_medida || "").trim(),
                meta_resultado: (x.meta_resultado || "").trim(),
              }))
              .filter((x) => x.indicador_objetivo_general || x.unidad_medida || x.meta_resultado)
          : [],
        concepto_tecnico_favorable_dep: tipo !== "OBSERVACIONES" ? (conceptoTecnicoDep || null) : null,
        concepto_sectorial_favorable_dep: tipo !== "OBSERVACIONES" ? (conceptoSectorialDep || null) : null,
        proyecto_viable_dep: tipo !== "OBSERVACIONES" ? (proyectoViableDep || null) : null,
      }),
    });
    if (!res.ok) {
      const err = await res.text().catch(() => "");
      throw new Error(err || "No se pudo guardar el registro de evaluacion.");
    }
  }

  async function descargarPdfEvaluador() {
    if (!docEvaluador || !proyectoEvaluador) return;
    const html = editorRef.current?.innerHTML ?? contenidoEvaluador;
    if (!htmlHasUserContent(html)) {
      alert("Completa el contenido antes de descargar.");
      return;
    }
    if (!nombreEvaluador.trim()) {
      alert("Ingresa el nombre del evaluador.");
      return;
    }
    if (!cargoEvaluador.trim()) {
      alert("Ingresa el cargo del evaluador.");
      return;
    }
    if (!fechaEvaluador) {
      alert("Selecciona la fecha del evaluador.");
      return;
    }

    const tipoDoc =
      docEvaluador === "viabilidad"
        ? "VIABILIDAD"
        : docEvaluador === "viabilidad_ajustada"
          ? "VIABILIDAD_AJUSTADA"
          : "OBSERVACIONES";
    if (tipoDoc !== "OBSERVACIONES") {
      if (!conceptoTecnicoDep || !conceptoSectorialDep || !proyectoViableDep) {
        alert("Completa los checks del Analisis de viabilidad.");
        return;
      }
    }
    try {
      await guardarRegistroEvaluador(tipoDoc, html);
    } catch (e: any) {
      alert(e?.message || "No fue posible guardar en BD.");
      return;
    }

    const formId = proyectoEvaluador.id;
    if (!formId) {
      alert("No se encontro el ID del proyecto para generar el documento.");
      return;
    }
    const docKey =
      docEvaluador === "viabilidad"
        ? "viabilidad"
        : docEvaluador === "viabilidad_ajustada"
          ? "viabilidad-ajustada"
          : "observaciones";
    const res = await fetch(`${API_BASE_DEFAULT}/descarga/evaluador/pdf/${docKey}/${formId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contenido_html: html,
        nombre_evaluador: nombreEvaluador.trim(),
        cargo_evaluador: cargoEvaluador.trim(),
        fecha_evaluador: fechaEvaluador,
        indicadores_objetivo: indicadoresObjetivo
          .map((x) => ({
            indicador_objetivo_general: (x.indicador_objetivo_general || "").trim(),
            unidad_medida: (x.unidad_medida || "").trim(),
            meta_resultado: (x.meta_resultado || "").trim(),
          }))
          .filter((x) => x.indicador_objetivo_general || x.unidad_medida || x.meta_resultado),
        productos_ajustados: productosAjustados
          .map((x) => ({
            descripcion: (x.descripcion || "").trim(),
            unidad_medida: (x.unidad_medida || "").trim(),
            meta_programada: (x.meta_programada || "").trim(),
            meta_alcanzada: (x.meta_alcanzada || "").trim(),
          }))
          .filter((x) => x.descripcion || x.unidad_medida || x.meta_programada || x.meta_alcanzada),
        resultados_ajustados: resultadosAjustados
          .map((x) => ({
            descripcion: (x.descripcion || "").trim(),
            unidad_medida: (x.unidad_medida || "").trim(),
            meta_programada: (x.meta_programada || "").trim(),
            meta_alcanzada: (x.meta_alcanzada || "").trim(),
          }))
          .filter((x) => x.descripcion || x.unidad_medida || x.meta_programada || x.meta_alcanzada),
        concepto_tecnico_favorable_dep: tipoDoc !== "OBSERVACIONES" ? (conceptoTecnicoDep || null) : null,
        concepto_sectorial_favorable_dep: tipoDoc !== "OBSERVACIONES" ? (conceptoSectorialDep || null) : null,
        proyecto_viable_dep: tipoDoc !== "OBSERVACIONES" ? (proyectoViableDep || null) : null,
      }),
    });
    if (!res.ok) {
      const err = await res.text().catch(() => "");
      alert(err || "No fue posible generar el PDF del documento.");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download =
      docKey === "viabilidad"
        ? "viabilidad.pdf"
        : docKey === "viabilidad-ajustada"
          ? "viabilidad_ajustada.pdf"
          : "observaciones.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
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
        cargo_responsable: "",
        nombre_secretario: "",
        fuentes: "",
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
    setMetasProyectoById({});
    setViabilidadesSel([]);
    setFuncionariosViab({});
    setStep(1);
  };

  /* ---------- RENDER ---------- */
  if (vista === "home") {
    return (
      <div key="home-view" className="min-h-screen bg-gradient-to-b from-slate-50 to-white p-4 md:p-8">
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Ingreso al Sistema</h1>
            <p className="text-slate-600">Selecciona el rol para continuar</p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Card className="shadow-sm">
              <CardContent className="p-6 space-y-4">
                <h2 className="text-xl font-semibold">Dependencia</h2>
                <p className="text-sm text-slate-600">Accede al flujo actual para creacion, edicion y descargas del proyecto.</p>
                <Button
                  className="w-full"
                  onClick={() => {
                    setSelectedEditorImage(null);
                    setRol("dependencia");
                    setVista("lista");
                  }}
                >
                  Continuar como Dependencia
                </Button>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardContent className="p-6 space-y-4">
                <h2 className="text-xl font-semibold">Radicador</h2>
                <p className="text-sm text-slate-600">Gestiona datos de radicacion y soportes del proyecto.</p>
                <Button
                  className="w-full"
                  onClick={() => {
                    setSelectedEditorImage(null);
                    setRol("radicador");
                    setVista("lista");
                  }}
                >
                  Continuar como Radicador
                </Button>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardContent className="p-6 space-y-4">
                <h2 className="text-xl font-semibold">Evaluador</h2>
                <p className="text-sm text-slate-600">Consulta proyectos y genera Observaciones o Viabilidad en formato PDF.</p>
                <Button
                  className="w-full"
                  onClick={() => {
                    setSelectedEditorImage(null);
                    setRol("evaluador");
                    setVista("lista");
                  }}
                >
                  Continuar como Evaluador
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  if (vista === "lista") {
    return (
      <div key="lista-view" className="min-h-screen bg-gradient-to-b from-slate-50 to-white p-4 md:p-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Proyectos</h1>
              <p className="text-sm text-slate-600">
                Rol activo: <span className="font-semibold capitalize">{rol ?? "sin rol"}</span>
              </p>
            </div>
            <div className="flex items-center gap-2">
              {rol === "dependencia" && (
                <Button className="gap-2" onClick={() => { limpiarFormulario(); setFormId(null); setVista("form"); }}>
                  <PlusCircle className="h-4 w-4"/> Nuevo proyecto
                </Button>
              )}
              <Button variant="outline" onClick={() => setVista("home")}>Cambiar rol</Button>
            </div>
          </div>

          {/* Filtros */}
          <Card className="shadow-sm">
            <CardContent className="p-4 grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <Label>Nombre</Label>
                <Input
                  value={fNombre}
                  onChange={(e) => setFNombre(sanitizeSearchTerm(e.target.value))}
                  onPaste={(e) => {
                    e.preventDefault();
                    const txt = e.clipboardData?.getData("text/plain") ?? "";
                    setFNombre(sanitizeSearchTerm(txt));
                  }}
                  onDrop={(e) => e.preventDefault()}
                  onDragOver={(e) => e.preventDefault()}
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
                          {rol === "dependencia" ? (
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => openFromRow(p)}
                            >
                              Abrir
                            </Button>
                          ) : rol === "radicador" ? (
                            <Button
                              size="sm"
                              variant="secondary"
                              disabled={radicacionLoading}
                              onClick={() => { void openRadicacionModal(p); }}
                            >
                              Radicar
                            </Button>
                          ) : (
                            <div className="flex items-center justify-end gap-2">
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => { void openEvaluadorDoc(p, "observaciones"); }}
                              >
                                Observaciones
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => { void openEvaluadorDoc(p, "viabilidad"); }}
                              >
                                Viabilidad
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => { void openEvaluadorDoc(p, "viabilidad_ajustada"); }}
                              >
                                Viabilidad ajustada
                              </Button>
                            </div>
                          )}
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

          <Dialog open={openRadicacion} onOpenChange={setOpenRadicacion}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Radicar proyecto</DialogTitle>
              </DialogHeader>
              <div className="grid gap-4">
                <div className="text-sm text-slate-600 break-words">
                  Proyecto: <span className="font-semibold">{radicacionProyecto || "-"}</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <Field label="Numero de radicacion">
                    <Input
                      value={radicacionState.numero_radicacion}
                      onChange={(e) => setRadicacionState((p) => ({ ...p, numero_radicacion: e.target.value }))}
                      placeholder="Ej. 2026-001234"
                    />
                  </Field>

                  <Field label="Fecha de radicacion">
                    <Input
                      type="date"
                      value={radicacionState.fecha_radicacion || todayISODate()}
                      onChange={(e) => setRadicacionState((p) => ({ ...p, fecha_radicacion: e.target.value }))}
                    />
                  </Field>

                  <Field label="BPIN">
                    <Input
                      value={radicacionState.bpin}
                      onChange={(e) => setRadicacionState((p) => ({ ...p, bpin: e.target.value }))}
                      placeholder="Codigo BPIN"
                    />
                  </Field>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <Field label="Folios">
                    <Input
                      type="number"
                      min={0}
                      value={radicacionState.soportes_folios}
                      onChange={(e) => setRadicacionState((p) => ({ ...p, soportes_folios: Math.max(0, Number(e.target.value || 0)) }))}
                    />
                  </Field>
                  <Field label="Planos">
                    <Input
                      type="number"
                      min={0}
                      value={radicacionState.soportes_planos}
                      onChange={(e) => setRadicacionState((p) => ({ ...p, soportes_planos: Math.max(0, Number(e.target.value || 0)) }))}
                    />
                  </Field>
                  <Field label="CDs">
                    <Input
                      type="number"
                      min={0}
                      value={radicacionState.soportes_cds}
                      onChange={(e) => setRadicacionState((p) => ({ ...p, soportes_cds: Math.max(0, Number(e.target.value || 0)) }))}
                    />
                  </Field>
                  <Field label="Otros">
                    <Input
                      type="number"
                      min={0}
                      value={radicacionState.soportes_otros}
                      onChange={(e) => setRadicacionState((p) => ({ ...p, soportes_otros: Math.max(0, Number(e.target.value || 0)) }))}
                    />
                  </Field>
                </div>

                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setOpenRadicacion(false)} disabled={radicacionSaving}>
                    Cancelar
                  </Button>
                  <Button onClick={() => { void saveRadicacion(); }} disabled={radicacionSaving}>
                    {radicacionSaving ? "Guardando..." : "Guardar radicacion"}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    );
  }

  if (vista === "evaluador_doc") {
    const tituloDoc =
      docEvaluador === "viabilidad"
        ? "Viabilidad"
        : docEvaluador === "viabilidad_ajustada"
          ? "Viabilidad ajustada"
          : "Observaciones";
    return (
      <div key="evaluador-doc-view" className="min-h-screen bg-gradient-to-b from-slate-50 to-white p-4 md:p-8">
        <div className="mx-auto max-w-6xl space-y-6">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight">{tituloDoc}</h1>
              <p className="text-sm text-slate-600">
                Proyecto: {proyectoEvaluador?.nombre ?? ""} | Cod. MGA: {proyectoEvaluador?.codMGA ?? ""}
              </p>
            </div>
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => {
                if (editorRef.current) {
                  editorRef.current.innerHTML = "";
                }
                if (document.activeElement instanceof HTMLElement) {
                  document.activeElement.blur();
                }
                setSelectedEditorImage(null);
                setVista("lista");
                setDocEvaluador(null);
                setProyectoEvaluador(null);
                setContenidoEvaluador("");
                setNombreEvaluador("");
                setCargoEvaluador("");
                setFechaEvaluador(todayISODate());
                setIndicadoresObjetivo([{ indicador_objetivo_general: "", unidad_medida: "", meta_resultado: "" }]);
                setProductosAjustados([{ descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" }]);
                setResultadosAjustados([{ descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" }]);
                setFNombre("");
                setFCodMga("");
                setFDependencia(null);
              }}
            >
              <ArrowLeft className="h-4 w-4" /> Volver a lista
            </Button>
          </div>

          <Card className="shadow-sm">
            <CardContent className="p-4 space-y-4">
              {(docEvaluador === "viabilidad" || docEvaluador === "viabilidad_ajustada") && (
                <div className="rounded-xl border p-3 space-y-3 bg-slate-50">
                  <h3 className="font-semibold text-sm">Analisis de viabilidad (Departamento)</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <Label>Concepto Tecnico Favorable</Label>
                      <select
                        className="h-10 w-full rounded-md border px-3 text-sm"
                        value={conceptoTecnicoDep}
                        onChange={(e) => setConceptoTecnicoDep((e.target.value as SiNo) || "")}
                      >
                        <option value="">Selecciona...</option>
                        <option value="SI">SI</option>
                        <option value="NO">NO</option>
                      </select>
                    </div>
                    <div className="space-y-1">
                      <Label>Concepto Sectorial Favorable</Label>
                      <select
                        className="h-10 w-full rounded-md border px-3 text-sm"
                        value={conceptoSectorialDep}
                        onChange={(e) => setConceptoSectorialDep((e.target.value as SiNo) || "")}
                      >
                        <option value="">Selecciona...</option>
                        <option value="SI">SI</option>
                        <option value="NO">NO</option>
                      </select>
                    </div>
                    <div className="space-y-1">
                      <Label>El Proyecto es Viable</Label>
                      <select
                        className="h-10 w-full rounded-md border px-3 text-sm"
                        value={proyectoViableDep}
                        onChange={(e) => setProyectoViableDep((e.target.value as SiNo) || "")}
                      >
                        <option value="">Selecciona...</option>
                        <option value="SI">SI</option>
                        <option value="NO">NO</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {docEvaluador === "viabilidad" && (
                <div className="rounded-xl border p-3 space-y-3 bg-slate-50">
                  <div className="space-y-2">
                    <h3 className="font-semibold text-sm">Metas PDD y Meta del proyecto</h3>
                    <div className="space-y-2">
                      {metasPddEvaluador.length ? metasPddEvaluador.map((m) => (
                        <div key={`meta-eval-${m.id}`} className="grid grid-cols-1 md:grid-cols-12 gap-2 items-center rounded-lg border bg-white p-2">
                          <div className="md:col-span-2 text-sm">
                            <div className="text-xs text-slate-500">NÚMERO DE META PDD</div>
                            <div>{m.numero_meta}</div>
                          </div>
                          <div className="md:col-span-5 text-sm">
                            <div className="text-xs text-slate-500">META DEL CUATRENIO PDD</div>
                            <div>{m.nombre_meta}</div>
                          </div>
                          <div className="md:col-span-5">
                            <Label>Meta del proyecto</Label>
                            <Input
                              value={metasProyectoById[m.id] ?? ""}
                              onChange={(e) => setMetasProyectoById((prev) => ({ ...prev, [m.id]: e.target.value }))}
                              placeholder="Digite la meta del proyecto"
                            />
                          </div>
                        </div>
                      )) : (
                        <div className="text-sm text-slate-500">No hay metas seleccionadas en el formulario.</div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-semibold text-sm">Indicadores objetivo general</h3>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="gap-1"
                      onClick={() =>
                        setIndicadoresObjetivo((prev) => [
                          ...prev,
                          { indicador_objetivo_general: "", unidad_medida: "", meta_resultado: "" },
                        ])
                      }
                    >
                      <Plus className="h-4 w-4" /> Agregar item
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {indicadoresObjetivo.map((item, idx) => (
                      <div key={`ind-${idx}`} className="grid grid-cols-1 md:grid-cols-12 gap-2 items-end">
                        <div className="md:col-span-5">
                          <Label>Indicador objetivo general</Label>
                          <Input
                            value={item.indicador_objetivo_general}
                            onChange={(e) =>
                              setIndicadoresObjetivo((prev) =>
                                prev.map((r, i) =>
                                  i === idx ? { ...r, indicador_objetivo_general: e.target.value } : r
                                )
                              )
                            }
                          />
                        </div>
                        <div className="md:col-span-3">
                          <Label>Unidad de medida</Label>
                          <Input
                            value={item.unidad_medida}
                            onChange={(e) =>
                              setIndicadoresObjetivo((prev) =>
                                prev.map((r, i) => (i === idx ? { ...r, unidad_medida: e.target.value } : r))
                              )
                            }
                          />
                        </div>
                        <div className="md:col-span-3">
                          <Label>Meta de resultado</Label>
                          <Input
                            value={item.meta_resultado}
                            onChange={(e) =>
                              setIndicadoresObjetivo((prev) =>
                                prev.map((r, i) => (i === idx ? { ...r, meta_resultado: e.target.value } : r))
                              )
                            }
                          />
                        </div>
                        <div className="md:col-span-1">
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            onClick={() =>
                              setIndicadoresObjetivo((prev) => {
                                if (prev.length === 1) {
                                  return [{ indicador_objetivo_general: "", unidad_medida: "", meta_resultado: "" }];
                                }
                                return prev.filter((_, i) => i !== idx);
                              })
                            }
                            title="Eliminar item"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {docEvaluador === "viabilidad_ajustada" && (
                <div className="rounded-xl border p-3 space-y-4 bg-slate-50">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="font-semibold text-sm">Productos</h3>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="gap-1"
                        onClick={() =>
                          setProductosAjustados((prev) => [
                            ...prev,
                            { descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" },
                          ])
                        }
                      >
                        <Plus className="h-4 w-4" /> Agregar item
                      </Button>
                    </div>
                    <div className="space-y-3">
                      {productosAjustados.map((item, idx) => (
                        <div key={`prod-aj-${idx}`} className="grid grid-cols-1 md:grid-cols-12 gap-2 items-end">
                          <div className="md:col-span-4">
                            <Label>Descripcion</Label>
                            <Input
                              value={item.descripcion}
                              onChange={(e) =>
                                setProductosAjustados((prev) =>
                                  prev.map((r, i) => (i === idx ? { ...r, descripcion: e.target.value } : r))
                                )
                              }
                            />
                          </div>
                          <div className="md:col-span-3">
                            <Label>Unidad de medida</Label>
                            <Input
                              value={item.unidad_medida}
                              onChange={(e) =>
                                setProductosAjustados((prev) =>
                                  prev.map((r, i) => (i === idx ? { ...r, unidad_medida: e.target.value } : r))
                                )
                              }
                            />
                          </div>
                          <div className="md:col-span-2">
                            <Label>Meta programada</Label>
                            <Input
                              value={item.meta_programada}
                              onChange={(e) =>
                                setProductosAjustados((prev) =>
                                  prev.map((r, i) => (i === idx ? { ...r, meta_programada: e.target.value } : r))
                                )
                              }
                            />
                          </div>
                          <div className="md:col-span-2">
                            <Label>Meta alcanzada</Label>
                            <Input
                              value={item.meta_alcanzada}
                              onChange={(e) =>
                                setProductosAjustados((prev) =>
                                  prev.map((r, i) => (i === idx ? { ...r, meta_alcanzada: e.target.value } : r))
                                )
                              }
                            />
                          </div>
                          <div className="md:col-span-1">
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              onClick={() =>
                                setProductosAjustados((prev) => {
                                  if (prev.length === 1) return [{ descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" }];
                                  return prev.filter((_, i) => i !== idx);
                                })
                              }
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="font-semibold text-sm">Resultados</h3>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="gap-1"
                        onClick={() =>
                          setResultadosAjustados((prev) => [
                            ...prev,
                            { descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" },
                          ])
                        }
                      >
                        <Plus className="h-4 w-4" /> Agregar item
                      </Button>
                    </div>
                    <div className="space-y-3">
                      {resultadosAjustados.map((item, idx) => (
                        <div key={`res-aj-${idx}`} className="grid grid-cols-1 md:grid-cols-12 gap-2 items-end">
                          <div className="md:col-span-4">
                            <Label>Descripcion</Label>
                            <Input
                              value={item.descripcion}
                              onChange={(e) =>
                                setResultadosAjustados((prev) =>
                                  prev.map((r, i) => (i === idx ? { ...r, descripcion: e.target.value } : r))
                                )
                              }
                            />
                          </div>
                          <div className="md:col-span-3">
                            <Label>Unidad de medida</Label>
                            <Input
                              value={item.unidad_medida}
                              onChange={(e) =>
                                setResultadosAjustados((prev) =>
                                  prev.map((r, i) => (i === idx ? { ...r, unidad_medida: e.target.value } : r))
                                )
                              }
                            />
                          </div>
                          <div className="md:col-span-2">
                            <Label>Meta programada</Label>
                            <Input
                              value={item.meta_programada}
                              onChange={(e) =>
                                setResultadosAjustados((prev) =>
                                  prev.map((r, i) => (i === idx ? { ...r, meta_programada: e.target.value } : r))
                                )
                              }
                            />
                          </div>
                          <div className="md:col-span-2">
                            <Label>Meta alcanzada</Label>
                            <Input
                              value={item.meta_alcanzada}
                              onChange={(e) =>
                                setResultadosAjustados((prev) =>
                                  prev.map((r, i) => (i === idx ? { ...r, meta_alcanzada: e.target.value } : r))
                                )
                              }
                            />
                          </div>
                          <div className="md:col-span-1">
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              onClick={() =>
                                setResultadosAjustados((prev) => {
                                  if (prev.length === 1) return [{ descripcion: "", unidad_medida: "", meta_programada: "", meta_alcanzada: "" }];
                                  return prev.filter((_, i) => i !== idx);
                                })
                              }
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-2 border rounded-lg p-2 bg-slate-50">
                <Button type="button" variant="outline" size="sm" onClick={() => applyEditorCommand("bold")}>Negrita</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => applyEditorCommand("italic")}>Cursiva</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => applyEditorCommand("underline")}>Subrayado</Button>
                <select
                  className="h-9 rounded-md border bg-white px-2 text-sm"
                  value={editorFontSizePx}
                  onChange={(e) => applyEditorFontSize(e.target.value)}
                  title="Tamaño de letra"
                >
                  {["10","11","12","14","16","18","20","24","28"].map((s) => (
                    <option key={`fs-${s}`} value={s}>{s}px</option>
                  ))}
                </select>
                <Button type="button" variant="outline" size="sm" onClick={() => applyEditorCommand("justifyLeft")}>Izq</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => applyEditorCommand("justifyCenter")}>Centro</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => applyEditorCommand("justifyRight")}>Der</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => applyEditorCommand("justifyFull")}>Justificado</Button>
                <Button type="button" variant="outline" size="sm" onClick={applyBulletList}>Lista •</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => resizeSelectedImage(0.85)}>Img -</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => resizeSelectedImage(1.15)}>Img +</Button>
                <Button type="button" variant="outline" size="sm" onClick={fitSelectedImage}>Ajustar imagen</Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => imageInputRef.current?.click()}
                >
                  Insertar imagen
                </Button>
                <input
                  ref={imageInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => onImageSelected(e.target.files?.[0])}
                />
              </div>

              <div
                ref={editorRef}
                contentEditable
                suppressContentEditableWarning
                className="min-h-[420px] rounded-xl border bg-white p-4 outline-none focus:ring-2 focus:ring-slate-300 [&_img]:max-w-full [&_img]:h-auto [&_ul]:list-disc [&_ul]:pl-6 [&_ul]:my-2 [&_ol]:list-decimal [&_ol]:pl-6 [&_ol]:my-2"
                onInput={(e) => setContenidoEvaluador((e.target as HTMLDivElement).innerHTML)}
                onClick={(e) => {
                  const target = e.target as HTMLElement;
                  if (target?.tagName === "IMG") {
                    setSelectedEditorImage(target as HTMLImageElement);
                  } else {
                    setSelectedEditorImage(null);
                  }
                }}
              />
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardContent className="p-4 grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
              <div className="md:col-span-2">
                <Label>Nombre del evaluador</Label>
                <Input
                  value={nombreEvaluador}
                  onChange={(e) => setNombreEvaluador(e.target.value)}
                  placeholder="Nombre completo del evaluador"
                />
              </div>
              <div>
                <Label>Cargo del evaluador</Label>
                <Input
                  value={cargoEvaluador}
                  onChange={(e) => setCargoEvaluador(e.target.value)}
                  placeholder="Cargo"
                />
              </div>
              <div>
                <Label>Fecha del evaluador</Label>
                <Input
                  type="date"
                  value={fechaEvaluador}
                  onChange={(e) => setFechaEvaluador(e.target.value)}
                />
              </div>
              <Button onClick={descargarPdfEvaluador}>Descargar PDF</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  /* ---------- FORM ---------- */
  return (
    <div key="form-view" className="min-h-screen bg-gradient-to-b from-slate-50 to-white p-4 md:p-8">
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
            [5, "Políticas transversales"],
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

              <Field label="Cargo responsable">
                <select
                  className="h-10 w-full rounded-md border px-3 text-sm"
                  value={datos.datos_basicos.cargo_responsable}
                  onChange={(e) =>
                    setDatos((p) => ({
                      ...p,
                      datos_basicos: {
                        ...p.datos_basicos,
                        cargo_responsable: e.target.value,
                      },
                    }))
                  }
                >
                  <option value="">Selecciona…</option>
                  <option value="JEFE DE OFICINA">Jefe de Oficina</option>
                  <option value="SECRETARIO(A)">Secretario(a)</option>
                </select>
              </Field>

              <Field label="Nombre Responsable">
                <Input type="text" value={datos.datos_basicos.nombre_secretario}
                  onChange={(e) => setDatos(p => ({ ...p, datos_basicos: { ...p.datos_basicos, nombre_secretario: e.target.value } }))} />
              </Field>

              <Field label="Duración del proyecto (meses)">
                <Input type="number" value={datos.datos_basicos.duracion_proyecto}
                  onChange={e=> setDatos(p=>({ ...p, datos_basicos: { ...p.datos_basicos, duracion_proyecto: Number(e.target.value || 0) } }))} />
              </Field>

              <Field label="Cantidad de beneficiarios">
                <Input type="number" value={datos.datos_basicos.cantidad_beneficiarios} 
                onChange={(e) => setDatos(p => ({ ...p, datos_basicos: { ...p.datos_basicos, cantidad_beneficiarios: Number(e.target.value || 0) } }))} />
              </Field>

              <Field label="Fuentes de beneficiarios">
                <Input type="text" value={datos.datos_basicos.fuentes}
                  onChange={(e) => setDatos(p => ({ ...p, datos_basicos: { ...p.datos_basicos, fuentes: e.target.value } }))} />
              </Field>
            </CardContent>
          </Card>
        )}

        {/* Paso 2 */}
        {step===2 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 space-y-2">
              <h3 className="font-semibold">Metas — depende del Programa</h3>
              <div className="border rounded-xl p-3 max-h-120 overflow-auto space-y-1">
                {metas.map(o => (
                  <CheckItem
                    key={`m-${o.codigo}`}
                    label={`${o.codigo ?? ""} — ${o.nombre}`}
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
                      {ENTIDADES.map(ent => {
                        const isMain = ["DEPARTAMENTO", "NACION", "MUNICIPIO", "OTROS"].includes(ent);
                        const isSub = ent === "PROPIOS" || ent.startsWith("SGP_");

                        return (
                          <tr key={ent} className="border-t align-top">
                            <td
                              className={cx(
                                "px-3 py-2",
                                isMain && "font-bold",
                                isSub && "italic text-right pr-6"
                              )}
                            >
                              {ent === "NACION" ? "Nación" : ent.charAt(0) + ent.slice(1).toLowerCase()}
                            </td>

                            {years.map(y => {
                              const k = keyFin(y, ent);

                              if (ent === "DEPARTAMENTO") {
                                const depVal = calcDepartamentoForYear(datos.estructura_financiera_ui, y);
                                return (
                                  <td key={k} className="px-2 py-1">
                                    <input
                                      type="text"
                                      className="w-full rounded-md border px-2 py-1 text-right bg-slate-100 text-slate-700 font-bold"
                                      value={depVal === 0 ? "" : formatMiles(depVal)}
                                      disabled
                                      readOnly
                                      title="Valor calculado: PROPIOS + todos los SGP"
                                    />
                                  </td>
                                );
                              }
                              const raw = datos.estructura_financiera_ui[k] ?? "";
                              return (
                                <td key={k} className="px-2 py-1">
                                  <input
                                    type="text"
                                    inputMode="decimal"
                                    placeholder="0"
                                    className={cx(
                                      "w-full rounded-md border px-2 py-1 text-right",
                                      isSub && "italic text-right pr-6"
                                    )}
                                    value={formatInputMiles(raw ?? "")}
                                    onChange={(e) => {
                                      const clean = sanitizeMoneyInput(e.target.value);
                                      setDatos((p) => ({
                                        ...p,
                                        estructura_financiera_ui: {
                                          ...p.estructura_financiera_ui,
                                          [k]: clean,
                                        },
                                      }));
                                    }}
                                    onBlur={(e) => {
                                      const clean = sanitizeMoneyInput(e.target.value);
                                      setDatos((p) => ({
                                        ...p,
                                        estructura_financiera_ui: {
                                          ...p.estructura_financiera_ui,
                                          [k]: clean,
                                        },
                                      }));
                                    }}
                                  />
                                </td>
                              );
                            })}
                            <td className={cx("px-3 py-2 text-right", isMain && "font-bold", isSub && "italic")}>
                              {toMoney(
                                years.reduce((s, y) => {
                                  if (ent === "DEPARTAMENTO") {
                                    return s + calcDepartamentoForYear(datos.estructura_financiera_ui, y);
                                  }
                                  return (
                                    s +
                                    (parseDecimal2(datos.estructura_financiera_ui[keyFin(y, ent)] ?? "") ??
                                      0)
                                  );
                                }, 0)
                              )}
                            </td>
                          </tr>
                        );
                      })}
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
                <div className="border rounded-xl p-3 max-h-120 overflow-auto space-y-5">
                  {varsSectorialRespSorted.map(v => (
                    <div key={`vs-${v.id}`} className="grid md:grid-cols-[7fr_1fr] gap-2 items-center">
                      <div className="text-sm">{v.id} — {v.nombre}</div>
                      <select
                        className="h-8 rounded-md border px-2 text-sm"
                        value={v.respuesta ?? ""}
                        onChange={(e)=>{
                          const value = e.target.value as Respuesta;
                          setVarsSectorialResp(prev => prev.map(x => x.id===v.id ? { ...x, respuesta:value } : x));
                        }}
                      >
                        <option value="">Selecciona…</option>
                        <option value="SI">SI</option>
                        <option value="NO">NO</option>
                        {v.no_aplica && <option value="N/A">N/A</option>}
                      </select>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="font-semibold">Variables concepto técnico</h3>
                <div className="border rounded-xl p-3 max-h-120 overflow-auto space-y-5">
                  {varsTecnicoRespSorted.map(v => (
                    <div key={`vt-${v.id}`} className="grid md:grid-cols-[7fr_1fr] gap-2 items-center">
                      <div className="text-sm">{v.id} — {v.nombre}</div>
                      <select
                        className="h-8 rounded-md border px-2 text-sm"
                        value={v.respuesta ?? ""}
                        onChange={(e)=>{
                          const value = e.target.value as Respuesta;
                          setVarsTecnicoResp(prev => prev.map(x => x.id===v.id ? { ...x, respuesta:value } : x));
                        }}
                      >
                        <option value="">Selecciona…</option>
                        <option value="SI">SI</option>
                        <option value="NO">NO</option>
                        {v.no_aplica && <option value="N/A">N/A</option>}
                      </select>
                    </div>
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
                    {(() => {
                      const uiRaw =
                        row.valor_ui ??
                        (row.valor_destinado != null
                          ? row.valor_destinado.toString().replace(".", ",")
                          : "");
                      return (
                        <>
                          <Input
                            type="text"
                            inputMode="decimal"
                            placeholder="0,00"
                            value={formatInputMiles(uiRaw)}
                            onChange={(e) => {
                              const clean = sanitizeMoneyInput(e.target.value);
                              setDatos((p) => {
                                const arr = [...p.politicas];
                                arr[idx] = {
                                  ...arr[idx],
                                  valor_ui: clean,
                                };
                                return { ...p, politicas: arr };
                              });
                            }}
                            onBlur={(e) => {
                              const num = parseDecimal2(e.target.value);
                              setDatos((p) => {
                                const arr = [...p.politicas];
                                if (num !== null) {
                                  arr[idx] = {
                                    ...arr[idx],
                                    valor_destinado: num,
                                    valor_ui: undefined,
                                  };
                                } else {
                                  arr[idx] = {
                                    ...arr[idx],
                                    valor_ui: e.target.value,
                                  };
                                }
                                return { ...p, politicas: arr };
                              });
                            }}
                          />
                          <div className="text-[11px] text-slate-500 mt-1">
                            {toMoney(
                              row.valor_ui !== undefined
                                ? parseDecimal2(row.valor_ui) ?? row.valor_destinado
                                : row.valor_destinado
                            )}
                          </div>
                        </>
                      );
                    })()}
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
                <div className="border rounded-xl p-3 max-h-120 overflow-auto space-y-5">
                  {viabRespSorted.map(v => (
                    <div key={`vb-${v.id}`} className="grid md:grid-cols-[7fr_1fr] gap-2 items-center">
                      <div className="text-sm">{v.id} — {v.nombre}</div>
                      <select
                        className="h-8 rounded-md border px-2 text-sm"
                        value={v.respuesta ?? ""}
                        onChange={(e)=>{
                          const value = e.target.value as Respuesta;
                          setViabResp(prev => prev.map(x => x.id===v.id ? { ...x, respuesta:value } : x));
                        }}
                      >
                        <option value="">Selecciona…</option>
                        <option value="SI">SI</option>
                        <option value="NO">NO</option>
                        {v.no_aplica && <option value="N/A">N/A</option>}
                      </select>
                    </div>
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

              {/* ALERTA: Políticas > Total del proyecto */}
              {totalPoliticas > totalProyecto && (
                <div className="mb-4 rounded-lg border border-red-300 bg-red-50 text-red-800 px-3 py-2 text-sm">
                  Atención: el valor de <b>políticas transversales</b> ({toMoney(totalPoliticas)}) supera el
                  <b> total del proyecto</b> ({toMoney(totalProyecto)}). Revisa la estructura financiera o ajusta los valores destinados a políticas.
                </div>
              )}

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
