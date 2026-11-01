import { useEffect, useState } from "react";
import type { ReactNode } from "react";
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

      {active === "Integrações" && <Placeholder title="Integrações" description="Catálogo de conectores previstos. A primeira integração será de leitura, sem capacidade de alterar os serviços de origem." icon={Workflow} items={[
        { title: "Zabbix", detail: "API para consulta de hosts, problemas e métricas", state: "Próxima integração" },
        { title: "ChirpStack", detail: "API para consulta de gateways, dispositivos e eventos LoRaWAN", state: "Planeado" },
        { title: "Docker Engine", detail: "Consulta de estado e metadados dos contentores", state: "Planeado" },
        { title: "Ubuntu Server", detail: "Consulta controlada de recursos e serviços", state: "Planeado" },
      ]}/>}

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
