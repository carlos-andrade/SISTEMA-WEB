import { useEffect, useState } from "react";
import { Activity, ArrowUpRight, Bell, Boxes, Command, Cpu, Database, Gauge, LayoutDashboard, Network, Server, ShieldCheck, Workflow } from "lucide-react";

type Health = {status:string;service:string;version:string};
const nav=[["Visão geral",LayoutDashboard],["Infraestrutura",Server],["Integrações",Workflow],["Dados",Database]] as const;

export default function App(){
 const [health,setHealth]=useState<Health|null>(null);
 const [error,setError]=useState(false);
 useEffect(()=>{const c=new AbortController();fetch("/api/health",{signal:c.signal}).then(r=>{if(!r.ok)throw Error("API indisponível");return r.json() as Promise<Health>}).then(setHealth).catch(e=>{if(e.name!=="AbortError")setError(true)});return()=>c.abort()},[]);
 return <div className="shell">
  <aside className="sidebar">
   <div className="brand"><div className="brandmark"><Command/></div><div><b>SISTEMA<span>WEB</span></b><small>CONTROL CENTER · V1</small></div></div>
   <label>PLATAFORMA</label><nav>{nav.map(([name,Icon],i)=><a className={i===0?"nav active":"nav"} key={name}><Icon size={18}/>{name}{i===0&&<i/>}</a>)}</nav>
   <label className="system-label">SISTEMA</label><a className="nav"><Network size={18}/>Topologia</a><a className="nav"><ShieldCheck size={18}/>Segurança</a>
   <div className="sidebottom"><span className="pulse"/> AMBIENTE LOCAL <b>DEV</b><small>SISTEMA WEB V1.0.0</small></div>
  </aside>
  <main>
   <header><div>Plataforma <span>/</span> <b>Visão geral</b></div><div className="headright"><small><i className="pulse"/> SISTEMA EM DESENVOLVIMENTO</small><Bell size={18}/><strong>CA</strong></div></header>
   <section className="heading"><div><label>CENTRO DE OPERAÇÕES <em>•</em> VERSÃO 1.0</label><h1>Visão geral</h1><p>Uma visão centralizada da plataforma e dos seus componentes.</p></div><div className="chip"><Activity size={15}/> PAINEL DE DESENVOLVIMENTO</div></section>
   <section className="hero"><div className="herocopy"><label><i className="pulse"/> CORE INITIALIZED</label><h2>A infraestrutura começa aqui.</h2><p>O SISTEMA WEB está a ganhar forma. Esta primeira versão valida a interface, a API e a comunicação entre contentores.</p></div><div className="orb"><div/><div/><Command/></div><small className="index">01 <span>/ 04</span></small></section>
   <section className="sectionhead"><div><label>TELEMETRIA</label><h3>Estado dos componentes</h3></div><small>ATUALIZAÇÃO AO CARREGAR</small></section>
   <section className="metrics">
    <article><label>API BACKEND <Activity/></label><b>{health?"Online":error?"Offline":"A verificar"}</b><small><i className={health?"good":"pending"}/>{health?"FastAPI respondeu com sucesso":error?"Não foi possível contactar a API":"A aguardar resposta da API"}</small></article>
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
     <p className="connection"><i className={health?"good":"pending"}/>{health?"Ligação estabelecida":error?"Sem ligação":"A testar ligação"}</p><p>Endpoint de verificação: <code>/api/health</code></p>
     <div className="detail"><span>Serviço</span><b>{health?.service??"backend"}</b></div><div className="detail"><span>Versão da API</span><b>{health?.version??"1.0.0"}</b></div><div className="detail"><span>Resposta</span><b>{health?.status??"—"}</b></div>
    </article>
   </section>
   <footer>© 2026 SISTEMA WEB <span>ENGENHARIA · CONTROLO · RASTREABILIDADE</span></footer>
  </main>
 </div>
}