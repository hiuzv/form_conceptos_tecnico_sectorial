import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Loader2, Plus, Trash2, Download } from "lucide-react";

type ID = number;
interface Opcion { id: ID; nombre: string; codigo?: number | null; }

interface DatosBasicosDB {
  nombre_proyecto: string;
  cod_id_mga: number;
  id_dependencia: ID | null;
  id_linea_estrategica: ID | null;
  id_programa: ID | null;
  id_sector: ID | null;
}

interface PoliticaFila {
  id_politica: ID | null;
  id_categoria: ID | null;
  id_subcategoria: ID | null;
  valor_destinado: number;
  opciones_categorias?: Opcion[];
  opciones_subcategorias?: Opcion[];
}

interface EstadoFormulario {
  datos_basicos: DatosBasicosDB;
  politicas: PoliticaFila[];           // máx 2
  metas_slots: Array<ID | null>;       // 3 selects
  variables_sel: ID[];                 // check múltiple (se mantiene como estaba)
}

const API_BASE_DEFAULT = "http://localhost:8000";

function cx(...xs: Array<string | false | null | undefined>) { return xs.filter(Boolean).join(" "); }
function toMoney(n: number | undefined) {
  const v = Number(n ?? 0);
  return v.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
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
      id: Number(x.id),
      nombre: String(x[nombreKey]),
      codigo: campoCodigo ? (x[campoCodigo] ?? null) : null,
    };
  });
}

export default function App() {
  const [datos, setDatos] = useState<EstadoFormulario>({
    datos_basicos: {
      nombre_proyecto: "",
      cod_id_mga: 0,
      id_dependencia: null,
      id_linea_estrategica: null,
      id_programa: null,
      id_sector: null,
    },
    politicas: [{ id_politica: null, id_categoria: null, id_subcategoria: null, valor_destinado: 0 }],
    metas_slots: [null, null, null],
    variables_sel: [],
  });

  // Opciones maestras
  const [deps, setDeps] = useState<Opcion[]>([]);
  const [lineas, setLineas] = useState<Opcion[]>([]);
  const [programas, setProgramas] = useState<Opcion[]>([]);
  const [sectores, setSectores] = useState<Opcion[]>([]);
  const [metas, setMetas] = useState<Opcion[]>([]);        // depende de sector
  const [variables, setVariables] = useState<Opcion[]>([]);
  const [politicas, setPoliticas] = useState<Opcion[]>([]);

  const [step, setStep] = useState(1);
  const [sending, setSending] = useState(false);

  const totalPoliticas = useMemo(
    () => datos.politicas.reduce((a, b) => a + (Number(b.valor_destinado) || 0), 0),
    [datos.politicas]
  );

  // Carga inicial
  useEffect(() => {
    (async () => {
      try {
        const [depsR, lineasR, varsR, politR] = await Promise.all([
          fetchJson("/llenado/dependencias"),
          fetchJson("/llenado/lineas"),
          fetchJson("/llenado/variables"),
          fetchJson("/llenado/politicas"),
        ]);
        setDeps(normalizaFlex(depsR, ["nombre_dependencia", "nombre"]));
        setLineas(normalizaFlex(lineasR, ["nombre", "nombre_linea_estrategica"])); // línea: solo nombre
        setVariables(normalizaFlex(varsR, ["nombre_variable", "nombre"]));
        setPoliticas(normalizaFlex(politR, ["nombre_politica", "nombre"]));
      } catch (e) { console.error(e); }
    })();
  }, []);

  // Línea → Programas
  useEffect(() => {
    const idLinea = datos.datos_basicos.id_linea_estrategica;
    if (!idLinea) { setProgramas([]); return; }
    (async () => {
      try {
        const r = await fetchJson(`/llenado/programas?linea_id=${idLinea}`);
        setProgramas(normalizaFlex(r, ["nombre_programa", "nombre"], "codigo_programa"));
      } catch (e) { console.error(e); setProgramas([]); }
    })();
  }, [datos.datos_basicos.id_linea_estrategica]);

  // Programa → Sectores
  useEffect(() => {
    const idProg = datos.datos_basicos.id_programa;
    if (!idProg) { setSectores([]); return; }
    (async () => {
      try {
        const r = await fetchJson(`/llenado/sectores?programa_id=${idProg}`);
        setSectores(normalizaFlex(r, ["nombre_sector", "nombre"], "codigo_sector"));
      } catch (e) { console.error(e); setSectores([]); }
    })();
  }, [datos.datos_basicos.id_programa]);

  // Sector → Metas
  useEffect(() => {
    const idSector = datos.datos_basicos.id_sector;
    if (!idSector) { setMetas([]); setDatos(p=> ({...p, metas_slots: [null, null, null]})); return; }
    (async () => {
      try {
        const r = await fetchJson(`/llenado/metas?sector_id=${idSector}`);
        const ops = normalizaFlex(r, ["nombre_meta", "nombre"]);
        setMetas(ops);
        // limpiar/evitar duplicados en los 3 selects
        setDatos(p => {
          const cleaned = p.metas_slots.map(v => (v && ops.some(o=>o.id===v) ? v : null)) as Array<ID|null>;
          const seen = new Set<number>();
          const unique = cleaned.map(v => (v && !seen.has(v) ? (seen.add(v), v) : (v ? null : null)));
          return { ...p, metas_slots: unique };
        });
      } catch (e) {
        console.error(e);
        setMetas([]);
        setDatos(p=> ({...p, metas_slots: [null, null, null]}));
      }
    })();
  }, [datos.datos_basicos.id_sector]);

  // Helpers
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

    const metas_ids = state.metas_slots.filter((x): x is number => x!=null);

    return {
      nombre_proyecto: db.nombre_proyecto,
      cod_id_mga: Number(db.cod_id_mga || 0),
      id_dependencia: db.id_dependencia,
      id_linea_estrategica: db.id_linea_estrategica,
      id_programa: db.id_programa,
      id_sector: db.id_sector,
      metas: metas_ids,
      variables: state.variables_sel,
      politicas: politicas_ids,
      valores_politicas,
      categorias: categorias_ids,
      subcategorias: subcategorias_ids,
    };
  }

  function sanitizeFileName(s: string) {
    return (s || "Formulario")
      .trim()
      .replace(/\s+/g, "_")
      .replace(/[^\w\-\.]+/g, "");
  }

  async function crearYDescargar() {
    try {
      setSending(true);
      const payload = buildBackendPayload(datos);

      const crear = await fetch(`${API_BASE_DEFAULT.replace(/\/$/,"")}/llenado/formulario`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!crear.ok) {
        const txt = await crear.text().catch(()=>"");
        throw new Error(`POST /llenado/formulario → ${crear.status} ${txt || crear.statusText}`);
      }
      const resp = await crear.json().catch(()=> ({}));
      const form_id: ID | undefined = Number(resp?.form_id ?? resp?.id ?? resp?.formId);
      if (!form_id) throw new Error("El backend no devolvió form_id");

      const down = await fetch(`${API_BASE_DEFAULT.replace(/\/$/,"")}/descarga/formulario/${form_id}/excel`);
      if (!down.ok) {
        const txt = await down.text().catch(()=>"");
        throw new Error(`GET /descarga/formulario/${form_id}/excel → ${down.status} ${txt || down.statusText}`);
      }
      const blob = await down.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      const base = sanitizeFileName(datos.datos_basicos.nombre_proyecto);
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white p-4 md:p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Formulario Concepto Técnico y Sectorial</h1>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant="secondary">Total Políticas: {toMoney(totalPoliticas)}</Badge>
          </div>
        </div>

        {/* Stepper */}
        <div className="flex flex-wrap gap-2 text-sm">
          {[
            [1, "Datos básicos"],
            [2, "Metas & Variables"],
            [3, "Políticas"],
            [4, "Revisión"],
          ].map(([idx, label]) => (
            <button
              key={idx}
              onClick={()=>setStep(Number(idx))}
              className={cx("px-3 py-1.5 rounded-full border", step===idx ? "bg-black text-white" : "bg-white hover:bg-slate-50")}
            >{label}</button>
          ))}
        </div>

        {/* Paso 1: Datos básicos */}
        {step===1 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label="Nombre del proyecto">
                <Input
                  value={datos.datos_basicos.nombre_proyecto}
                  onChange={e=> setDatos(p=>({ ...p, datos_basicos: { ...p.datos_basicos, nombre_proyecto: e.target.value } }))}
                />
              </Field>

              <Field label="Código ID MGA">
                <Input
                  type="number"
                  value={datos.datos_basicos.cod_id_mga}
                  onChange={e=> setDatos(p=>({ ...p, datos_basicos: { ...p.datos_basicos, cod_id_mga: Number(e.target.value || 0) } }))}
                />
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
                  onChange={(id)=> setDatos(p=> ({
                    ...p,
                    datos_basicos: { ...p.datos_basicos, id_linea_estrategica: id, id_programa: null, id_sector: null },
                  }))}
                  placeholder="Selecciona línea"
                />
              </Field>

              <Field label="Programa (según línea)">
                <SelectNative
                  opciones={programas}
                  value={datos.datos_basicos.id_programa}
                  onChange={(id)=> setDatos(p=> ({
                    ...p,
                    datos_basicos: { ...p.datos_basicos, id_programa: id, id_sector: null },
                  }))}
                  placeholder={datos.datos_basicos.id_linea_estrategica ? "Selecciona programa" : "Primero elige una línea"}
                />
              </Field>

              <Field label="Sector (según programa)">
                <SelectNative
                  opciones={sectores}
                  value={datos.datos_basicos.id_sector}
                  onChange={(id)=> setDatos(p=> ({ ...p, datos_basicos: { ...p.datos_basicos, id_sector: id } }))}
                  placeholder={datos.datos_basicos.id_programa ? "Selecciona sector" : "Primero elige un programa"}
                />
              </Field>
            </CardContent>
          </Card>
        )}

        {/* Paso 2: Metas & Variables */}
        {step===2 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <h3 className="font-semibold">Metas (1 a 3) — depende del Sector</h3>
                {[0,1,2].map((slot) => {
                  const selected = datos.metas_slots[slot];
                  const metaSel = metas.find(m => m.id === selected || 0);
                  return (
                    <div key={slot} className="grid gap-1">
                      <Label>Meta #{slot+1}</Label>
                      <SelectNative
                        value={selected}
                        onChange={(id)=> {
                          setDatos(p=>{
                            const arr = [...p.metas_slots] as Array<ID|null>;
                            if (id!=null && arr.some((v, i) => i!==slot && v===id)) return p;
                            arr[slot] = id;
                            return { ...p, metas_slots: arr };
                          });
                        }}
                        opciones={metas}
                        placeholder="Selecciona meta (opcional)"
                      />
                      {metaSel && <div className="text-xs text-slate-600">Meta de cuatrienio: <b>{metaSel.nombre}</b></div>}
                    </div>
                  );
                })}
              </div>

              <div className="space-y-2">
                <h3 className="font-semibold">Variables</h3>
                <div className="border rounded-xl p-3 max-h-72 overflow-auto space-y-1">
                  {variables.map(o => (
                    <CheckItem
                      key={`v-${o.id}`}
                      label={`${o.id} — ${o.nombre}`}
                      checked={datos.variables_sel.includes(o.id)}
                      onChange={(v)=> setDatos(prev => {
                        const set = new Set<number>(prev.variables_sel);
                        if (v) set.add(o.id); else set.delete(o.id);
                        return { ...prev, variables_sel: Array.from(set) };
                      })}
                    />
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Paso 3: Políticas (máx 2) */}
        {step===3 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Políticas (máximo 2)</h3>
                <Button
                  size="sm"
                  className="gap-2"
                  disabled={datos.politicas.length >= 2}
                  onClick={()=> setDatos(p=> ({
                    ...p,
                    politicas: [...p.politicas, { id_politica: null, id_categoria: null, id_subcategoria: null, valor_destinado: 0 }],
                  }))}
                >
                  <Plus className="h-4 w-4"/> Añadir fila
                </Button>
              </div>

              {datos.politicas.map((row, idx) => (
                <div key={idx} className="grid md:grid-cols-4 gap-3 border rounded-2xl p-3">
                  {/* Política */}
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
                            const r = await fetchJson(`/llenado/categorias?politica_id=${id}`);
                            opciones_categorias = normalizaFlex(r, ["nombre_categoria", "nombre"]);
                          } catch (e) { console.error(e); }
                        }

                        setDatos(p=>{
                          const arr = [...p.politicas];
                          arr[idx] = {
                            ...arr[idx],
                            id_politica: id,
                            id_categoria,
                            id_subcategoria,
                            opciones_categorias,
                            opciones_subcategorias,
                          };
                          return { ...p, politicas: arr };
                        });
                      }}
                      opciones={politicas}
                      placeholder="Selecciona política"
                    />
                  </div>

                  {/* Categoría */}
                  <div>
                    <Label>Categoría</Label>
                    <SelectNative
                      value={row.id_categoria}
                      onChange={async (idCat)=> {
                        let opciones_subcategorias: Opcion[] = [];
                        let id_subcategoria: ID | null = null;

                        if (idCat!=null) {
                          try {
                            const r = await fetchJson(`/llenado/subcategorias?categoria_id=${idCat}`);
                            opciones_subcategorias = normalizaFlex(r, ["nombre_subcategoria", "nombre"]);
                          } catch (e) { console.error(e); }
                        }

                        setDatos(p=>{
                          const arr = [...p.politicas];
                          arr[idx] = {
                            ...arr[idx],
                            id_categoria: idCat,
                            id_subcategoria,
                            opciones_subcategorias,
                          };
                          return { ...p, politicas: arr };
                        });
                      }}
                      opciones={row.opciones_categorias ?? []}
                      placeholder={row.id_politica ? "Selecciona categoría" : "Primero selecciona política"}
                    />
                  </div>

                  {/* Subcategoría */}
                  <div>
                    <Label>Subcategoría</Label>
                    <SelectNative
                      value={row.id_subcategoria}
                      onChange={(id)=> setDatos(p=>{
                        const arr = [...p.politicas];
                        arr[idx] = { ...arr[idx], id_subcategoria: id };
                        return { ...p, politicas: arr };
                      })}
                      opciones={row.opciones_subcategorias ?? []}
                      placeholder={row.id_categoria ? "Selecciona subcategoría" : "Primero selecciona categoría"}
                    />
                  </div>

                  {/* Valor */}
                  <div>
                    <Label>Valor destinado</Label>
                    <Input
                      type="number"
                      value={row.valor_destinado}
                      onChange={e=>{
                        const v = Number(e.target.value || 0);
                        setDatos(p=>{ const arr=[...p.politicas]; arr[idx]={...arr[idx], valor_destinado:v}; return {...p, politicas:arr};});
                      }}
                    />
                    <div className="text-[11px] text-slate-500 mt-1">{toMoney(row.valor_destinado)}</div>
                  </div>

                  <div className="md:col-span-4 text-right">
                    <Button size="icon" variant="ghost" onClick={()=>
                      setDatos(p=> ({ ...p, politicas: p.politicas.filter((_,i)=> i!==idx) }))
                    }>
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

        {/* Paso 4: Revisión y descarga */}
        {step===4 && (
          <Card className="shadow-sm">
            <CardContent className="p-4 space-y-3">
              <h3 className="font-semibold">Resumen que se enviará</h3>
              <pre className="bg-slate-950 text-slate-50 rounded-xl p-3 text-xs overflow-auto max-h-[420px]">
                {JSON.stringify(buildBackendPayload(datos), null, 2)}
              </pre>
              <div className="flex flex-wrap gap-2">
                <Button className="gap-2" onClick={crearYDescargar} disabled={sending}>
                  {sending ? <Loader2 className="h-4 w-4 animate-spin"/> : <Download className="h-4 w-4"/>}
                  DESCARGAR
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Navegación inferior */}
        <div className="flex items-center justify-between">
          <Button variant="outline" onClick={()=> setStep(s=> Math.max(1, s-1))}>Atrás</Button>
          <div className="flex items-center gap-2">
            {step<4 && <Button onClick={()=> setStep(s=> Math.min(4, s+1))}>Siguiente</Button>}
            {step===4 && (
              <Button onClick={crearYDescargar} className="gap-2" disabled={sending}>
                {sending ? <Loader2 className="h-4 w-4 animate-spin"/> : <Download className="h-4 w-4"/>}
                DESCARGAR
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/** ==== UI auxiliares ==== */
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
}: {
  opciones: Opcion[];
  value: ID | null;
  onChange: (id: ID | null) => void;
  placeholder?: string;
}) {
  return (
    <select
      className="h-10 w-full rounded-md border px-3 text-sm"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
    >
      <option value="">{placeholder || "Selecciona"}</option>
      {opciones.map((o) => (
        <option key={o.id} value={o.id}>
          {o.nombre}
        </option>
      ))}
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
