import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import BuyerCatalogPanel from "./components/licitation/BuyerCatalogPanel";
import {
  Activity, ArrowUpRight, Bell, Boxes, Command, Cpu, Database,
  Gauge, LayoutDashboard, Network, Server, ShieldCheck, Workflow,
  RefreshCw, AlertCircle
} from "lucide-react";

type Health = { status: string; service: string; version: string; timestamp?: string };
type Module = "Visão geral" | "Infraestrutura" | "Integrações" | "Dados" | "Topologia" | "Segurança";

const nav: { name: Module; icon: typeof LayoutDashboard; group: "PLATAFORMA" | "SISTEMA" }[] = [
  { name: "Visão geral", icon: LayoutDashboard, group: "PLATAFORMA" },
  { name: "Infraestrutura", icon: Server, group: "PLATAFORMA" },
  { name: "Integrações", icon: Workflow, group: "PLATAFORMA" },
  { name: "Dados", icon: Database, group: "PLATAFORMA" },
  { name: "Topologia", icon: Network, group: "SISTEMA" },
  { name: "Segurança", icon: ShieldCheck, group: "SISTEMA" },
];

function Status({ kind = "pending", children }: { kind?: "good" | "pending" | "neutral"; children: ReactNode }) {
  return <span className="statusline"><i className={kind} />{children}</span>;
}

function Placeholder({ title, description, icon: Icon, items }: {
  title: string; description: string; icon: typeof Server; items: { title: string; detail: string; state: string; kind?: "good" | "pending" | "neutral" }[];
}) {
  return <section className="module-page">
    <article className="module-intro card">
      <div className="module-icon"><Icon /></div>
      <div><label>MÓDULO DO SISTEMA</label><h2>{title}</h2><p>{description}</p></div>
    </article>
    <section className="sectionhead"><div><label>CAPACIDADES E COMPONENTES</label><h3>Estado de implementação</h3></div><small>ESTADO DOCUMENTADO</small></section>
    <div className="module-list">
      {items.map((item) => <article className="module-item card" key={item.title}>
        <div><b>{item.title}</b><p>{item.detail}</p></div>
        <Status kind={item.kind ?? "pending"}>{item.state}</Status>
      </article>)}
    </div>
    <article className="notice"><AlertCircle size={17}/><p><b>Transparência operacional.</b> Este ecrã apresenta o estado de implementação conhecido. Ainda não representa monitorização dinâmica nem validação automática dos componentes listados.</p></article>
  </section>;
}


type LicitationResult = {
  data: {
    id: string;
    object: string;
    status: string;
    validation_status: string;
    buyer?: { name?: string | null; city?: string | null; state?: string | null } | null;
    estimated_value?: { amount: number; currency: string; evidence_status: string } | null;
    source: { system: string; external_id?: string | null; url: string; captured_at: string; capture_status: string };
  };
  provenance: {
    repository: string;
    ref: string;
    path: string;
    blob_sha: string;
    content_sha256: string;
    validation: string;
    access_mode: string;
  };
};

function LicitationIntegration() {
  const [result, setResult] = useState<LicitationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/integrations/licitation/opportunities/reference");
      const body = await response.json();
      if (!response.ok) {
        const detail = typeof body.detail === "string" ? body.detail : body.detail?.message;
        throw new Error(detail || `Falha HTTP ${response.status}`);
      }
      setResult(body as LicitationResult);
    } catch (e) {
      setResult(null);
      setError(e instanceof Error ? e.message : "Falha desconhecida na integração.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return <section className="module-page">
    <article className="module-intro card">
      <div className="module-icon"><Workflow /></div>
      <div><label>FONTE PRIVADA · CONSULTA</label><h2>LICITACAO</h2>
        <p>Leitura do repositório de origem através do backend. Nenhuma operação de escrita é executada na fonte.</p>
      </div>
    </article>
    <section className="sectionhead"><div><label>PROVA DE CONCEITO V1.2</label><h3>Oportunidade de referência</h3></div>
      <button className="text-action" type="button" onClick={() => void load()} disabled={loading}>
        <RefreshCw size={13}/> {loading ? "A CONSULTAR" : "ATUALIZAR FONTE"}
      </button>
    </section>
    {loading && <article className="module-item card"><Status>Consulta ao GitHub em curso</Status></article>}
    {error && <article className="notice"><AlertCircle size={17}/><p><b>Integração indisponível.</b> {error} Configure o token de leitura no ambiente do backend e tente novamente.</p></article>}
    {result && <>
      <article className="module-item card">
        <div><label>IDENTIFICADOR</label><h3>{result.data.id}</h3><p>{result.data.object}</p></div>
        <Status kind={result.provenance.validation === "valid" ? "good" : "pending"}>
          {result.provenance.validation === "valid" ? "Schema válido" : "Validação pendente"}
        </Status>
      </article>
      <section className="metrics">
        <article><label>ÓRGÃO COMPRADOR</label><b>{result.data.buyer?.name ?? "Não informado"}</b><small>{[result.data.buyer?.city, result.data.buyer?.state].filter(Boolean).join(" / ") || "Local não informado"}</small></article>
        <article><label>ESTADO DA OPORTUNIDADE</label><b>{result.data.status}</b><small><i className="pending"/> Estado declarado na origem</small></article>
        <article><label>VALIDAÇÃO DE CONTEÚDO</label><b>{result.data.validation_status}</b><small><i className={result.data.validation_status === "validated" ? "good" : "pending"}/> Não equivale à validação material</small></article>
        <article><label>VALOR ESTIMADO</label><b>{result.data.estimated_value ? new Intl.NumberFormat("pt-PT", { style: "currency", currency: result.data.estimated_value.currency }).format(result.data.estimated_value.amount) : "Não informado"}</b><small>{result.data.estimated_value?.evidence_status ?? "Sem evidência"}</small></article>
      </section>
      <article className="card">
        <div className="cardhead"><div><label>PROVENIÊNCIA</label><h3>Rastreabilidade da fonte</h3></div><Database/></div>
        <div className="detail"><span>Repositório</span><b>{result.provenance.repository}</b></div>
        <div className="detail"><span>Branch</span><b>{result.provenance.ref}</b></div>
        <div className="detail"><span>Validação estrutural</span><b>{result.provenance.validation}</b></div>
        <div className="detail"><span>Modo de acesso</span><b>{result.provenance.access_mode}</b></div>
        <div className="detail"><span>Git blob SHA</span><code>{result.provenance.blob_sha}</code></div>
        <div className="detail"><span>SHA-256 do conteúdo</span><code>{result.provenance.content_sha256}</code></div>
        <p className="connection">Ficheiro: <code>{result.provenance.path}</code></p>
      </article>
      <article className="notice"><AlertCircle size={17}/><p><b>Limite de validação.</b> Schema válido confirma estrutura e tipos de dados. Não confirma a exatidão factual, a atualidade do edital nem a sua viabilidade.</p></article>
    </>}
    <footer>LICITACAO · FONTE EXTERNA READ-ONLY</footer>
  </section>;
}

export default function App() {
  const [active, setActive] = useState<Module>("Visão geral");
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState(false);
  const [checking, setChecking] = useState(false);

  async function checkApi(signal?: AbortSignal) {
    setChecking(true);
    try {
      const response = await fetch("/api/health", { signal });
      if (!response.ok) throw new Error("API indisponível");
      const data = await response.json() as Health;
      setHealth(data);
      setError(false);
    } catch (e) {
      if (e instanceof Error && e.name !== "AbortError") {
        setError(true);
        setHealth(null);
      }
    } finally {
      setChecking(false);
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    void checkApi(controller.signal);
    return () => controller.abort();
  }, []);

  const pageTitle = active;
  const pageDescription: Record<Module, string> = {
    "Visão geral": "Uma visão centralizada da plataforma e dos seus componentes.",
    "Infraestrutura": "Inventário e estado dos recursos computacionais que suportam a plataforma.",
    "Integrações": "Ponto central para ligação controlada aos serviços e sistemas externos.",
    "Dados": "Camada de dados, armazenamento, qualidade e rastreabilidade.",
    "Topologia": "Representação lógica das ligações entre os componentes da solução.",
    "Segurança": "Controlo de acesso, exposição de serviços e postura de segurança.",
  };

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brandmark"><Command /></div><div><b>SISTEMA<span>WEB</span></b><small>CONTROL CENTER · V1</small></div></div>
      {(["PLATAFORMA", "SISTEMA"] as const).map(group => <div className="navgroup" key={group}>
        <label>{group}</label>
        <nav>{nav.filter(item => item.group === group).map(({ name, icon: Icon }) =>
          <button type="button" className={active === name ? "nav active" : "nav"} key={name} onClick={() => setActive(name)} aria-current={active === name ? "page" : undefined}>
            <Icon size={18}/><span>{name}</span>{active === name && <i/>}
          </button>)}</nav>
      </div>)}
      <div className="sidebottom"><span className="pulse"/> AMBIENTE LOCAL <b>DEV</b><small>SISTEMA WEB V1.1</small></div>
    </aside>

    <main>
      <header><div>Plataforma <span>/</span> <b>{pageTitle}</b></div><div className="headright"><small><i className="pulse"/> SISTEMA EM DESENVOLVIMENTO</small><Bell size={18}/><strong>CA</strong></div></header>
      <section className="heading"><div><label>CENTRO DE OPERAÇÕES <em>•</em> VERSÃO 1.1</label><h1>{pageTitle}</h1><p>{pageDescription[active]}</p></div>
        {active === "Visão geral" && <div className="chip"><Activity size={15}/> PAINEL DE DESENVOLVIMENTO</div>}
      </section>

      {active === "Visão geral" && <>
        <section className="hero"><div className="herocopy"><label><i className="pulse"/> CORE INITIALIZED</label><h2>A infraestrutura começa aqui.</h2><p>O SISTEMA WEB valida a interface, a API e a comunicação entre contentores. Os módulos estão a ser preparados para receber integrações reais.</p></div><div className="orb"><div/><div/><Command/></div><small className="index">01 <span>/ 06</span></small></section>
        <section className="sectionhead"><div><label>TELEMETRIA</label><h3>Estado dos componentes</h3></div><button className="text-action" type="button" onClick={() => void checkApi()} disabled={checking}><RefreshCw size={13}/> {checking ? "A VERIFICAR" : "ATUALIZAR API"}</button></section>
        <section className="metrics">
          <article><label>API BACKEND <Activity/></label><b>{health ? "Online" : error ? "Offline" : "A verificar"}</b><small><i className={health ? "good" : "pending"}/>{health ? "FastAPI respondeu com sucesso" : error ? "Não foi possível contactar a API" : "A aguardar resposta da API"}</small></article>
          <article><label>FRONTEND <Boxes/></label><b>Online</b><small><i className="good"/>React + Vite em execução</small></article>
          <article><label>CONTENTORIZAÇÃO <Cpu/></label><b>Docker</b><small><i className="good"/>Ambiente isolado por Compose</small></article>
          <article><label>PERSISTÊNCIA <Database/></label><b>Planeada</b><small><i className="pending"/>Não incluída no bootstrap V1</small></article>
        </section>
        <section className="bottomgrid">
          <article className="card"><div className="cardhead"><div><label>ARQUITETURA</label><h3>Camadas da aplicação</h3></div><Gauge/></div>
            <div className="layer"><span><LayoutDashboard/></span><div><b>Frontend</b><small>React · TypeScript · Vite</small></div><code>01</code></div><div className="connector"/>
            <div className="layer"><span><Workflow/></span><div><b>Backend API</b><small>Python · FastAPI</small></div><code>02</code></div><div className="connector"/>
            <div className="layer planned"><span><Database/></span><div><b>Persistência</b><small>PostgreSQL · etapa futura</small></div><code>PLANEADO</code></div>
          </article>
          <article className="card"><div className="cardhead"><div><label>DIAGNÓSTICO</label><h3>Conectividade da API</h3></div><ArrowUpRight/></div>
            <p className="connection"><i className={health ? "good" : "pending"}/>{health ? "Ligação estabelecida" : error ? "Sem ligação" : "A testar ligação"}</p><p>Endpoint de verificação: <code>/api/health</code></p>
            <div className="detail"><span>Serviço</span><b>{health?.service ?? "backend"}</b></div><div className="detail"><span>Versão da API</span><b>{health?.version ?? "1.0.0"}</b></div><div className="detail"><span>Resposta</span><b>{health?.status ?? "—"}</b></div>
          </article>
        </section>
      </>}

      {active === "Infraestrutura" && <Placeholder title="Infraestrutura" description="Inventário inicial dos elementos que suportam o SISTEMA-WEB. A leitura dinâmica do servidor será implementada numa etapa posterior." icon={Server} items={[
        { title: "Servidor Ubuntu", detail: "Ubuntu Server 24.04 LTS · ambiente de execução conhecido", state: "Identificado", kind: "good" },
        { title: "Docker Engine", detail: "Motor de contentores utilizado pela V1", state: "Validado", kind: "good" },
        { title: "Contentores SISTEMA-WEB", detail: "Frontend Vite e backend FastAPI", state: "Em execução", kind: "good" },
        { title: "Recursos CPU, RAM e disco", detail: "Recolha periódica e histórico ainda não implementados", state: "Não monitorizado" },
        { title: "Serviços do sistema operativo", detail: "Inventário e estado por agente/API ainda não integrados", state: "Não integrado" },
      ]}/>}

      {active === "Integrações" && <><LicitationIntegration /><BuyerCatalogPanel /></>}

      {active === "Dados" && <Placeholder title="Dados" description="Camada responsável pela persistência, organização, qualidade e rastreabilidade da informação." icon={Database} items={[
        { title: "API de saúde", detail: "Resposta operacional consultada diretamente no backend", state: health ? "Disponível" : "Sem confirmação", kind: health ? "good" : "pending" },
        { title: "PostgreSQL", detail: "Base de dados da aplicação ainda não configurada", state: "Planeado" },
        { title: "Histórico de métricas", detail: "Retenção, agregação e consulta temporal ainda não implementadas", state: "Não implementado" },
        { title: "Auditoria de dados", detail: "Origem, timestamp, integridade e trilho de alterações", state: "Planeado" },
      ]}/>}

      {active === "Topologia" && <Placeholder title="Topologia" description="Visão lógica da arquitetura atualmente implementada e das integrações previstas." icon={Network} items={[
        { title: "Navegador → Frontend", detail: "HTTP na rede local · porta TCP 5173", state: "Validado", kind: "good" },
        { title: "Frontend → Backend", detail: "Proxy Vite /api · porta TCP 8000", state: "Validado", kind: "good" },
        { title: "Backend → serviços externos", detail: "Adaptadores de integração ainda não implementados", state: "Planeado" },
        { title: "Persistência", detail: "PostgreSQL não faz parte do bootstrap atual", state: "Planeado" },
      ]}/>}

      {active === "Segurança" && <Placeholder title="Segurança" description="Estado conhecido dos controlos de segurança. Esta página não representa uma auditoria ou certificação de segurança." icon={ShieldCheck} items={[
        { title: "Exposição de portas", detail: "Frontend e backend vinculados ao IP local 192.168.60.141", state: "Configuração validada", kind: "good" },
        { title: "Isolamento Docker", detail: "Rede própria sistema-web-v1-network", state: "Configurado", kind: "good" },
        { title: "Autenticação e autorização", detail: "Gestão de utilizadores, sessões e permissões", state: "Não implementado" },
        { title: "HTTPS / TLS", detail: "Acesso atual por HTTP na rede local", state: "Pendente" },
        { title: "Auditoria e gestão de segredos", detail: "Políticas e mecanismos ainda por definir", state: "Planeado" },
      ]}/>}
      <footer>© 2026 SISTEMA WEB <span>ENGENHARIA · CONTROLO · RASTREABILIDADE</span></footer>
    </main>
  </div>;
}
