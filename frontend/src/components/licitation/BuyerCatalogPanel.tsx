import { useEffect, useMemo, useState } from "react";
import { AlertCircle, ChevronDown, RefreshCw, ShoppingBasket } from "lucide-react";

type Unit = { code: string; name: string; uf: string; municipio: string; codigo_ibge: string; contract_count: number };
type Buyer = { cnpj: string; name: string; cnpj_valid: boolean; unit_count: number; contract_count: number; units: Unit[] };
type Contract = { control_id: string; cnpj: string; year: number; sequence: number; number: string; process: string; object: string; status: string; published_at: string; proposal_end: string; estimated_value: number | null; pncp_url: string | null };
type Item = { number: number; description: string; type: string; quantity: number; unit: string; unit_estimated_value: number | null; total_estimated_value: number | null; budget_confidential: boolean; status: string; award_criterion: string; benefit: string; catalog_code: string; ncm_nbs_code: string; has_result: boolean };
const money = (value: number | null | undefined) => value == null ? "Não informado" : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);

export default function BuyerCatalogPanel() {
  const [query, setQuery] = useState("");
  const [uf, setUf] = useState("");
  const [buyers, setBuyers] = useState<Buyer[]>([]);
  const [selectedBuyer, setSelectedBuyer] = useState("");
  const [selectedUnit, setSelectedUnit] = useState("");
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [selectedContract, setSelectedContract] = useState("");
  const [items, setItems] = useState<Item[]>([]);
  const [coverage, setCoverage] = useState("A consultar");
  const [capturedAt, setCapturedAt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const buyer = useMemo(() => buyers.find(row => row.cnpj === selectedBuyer), [buyers, selectedBuyer]);
  const unit = useMemo(() => buyer?.units.find(row => row.code === selectedUnit), [buyer, selectedUnit]);
  const contract = useMemo(() => contracts.find(row => row.control_id === selectedContract), [contracts, selectedContract]);

  async function loadBuyers() {
    setLoading(true); setError("");
    try {
      const params = new URLSearchParams({ q: query, uf, page: "1", page_size: "100" });
      const response = await fetch(`/api/licitation/buyers?${params}`);
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
      setBuyers(body.buyers || []);
      setCoverage(body.coverage || "Indisponível");
      setCapturedAt(body.source?.captured_at || "");
      if (!body.buyers?.some((row: Buyer) => row.cnpj === selectedBuyer)) {
        setSelectedBuyer(""); setSelectedUnit(""); setContracts([]); setItems([]);
      }
    } catch (e) { setError(e instanceof Error ? e.message : "Falha ao consultar catálogo."); }
    finally { setLoading(false); }
  }

  useEffect(() => { void loadBuyers(); }, []);

  async function chooseBuyer(cnpj: string) {
    setSelectedBuyer(cnpj); setSelectedUnit(""); setSelectedContract(""); setContracts([]); setItems([]);
  }

  async function chooseUnit(code: string) {
    setSelectedUnit(code); setSelectedContract(""); setItems([]);
    if (!selectedBuyer || !code) return;
    setLoading(true); setError("");
    try {
      const response = await fetch(`/api/licitation/buyers/${encodeURIComponent(selectedBuyer)}/units/${encodeURIComponent(code)}/contracts`);
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
      setContracts(body.contracts || []);
    } catch (e) { setError(e instanceof Error ? e.message : "Falha ao consultar contratações."); }
    finally { setLoading(false); }
  }

  async function chooseContract(controlId: string) {
    setSelectedContract(controlId); setItems([]);
    const selected = contracts.find(row => row.control_id === controlId);
    if (!selected) return;
    setLoading(true); setError("");
    try {
      const response = await fetch(`/api/licitation/contracts/${encodeURIComponent(selected.cnpj)}/${selected.year}/${selected.sequence}/items`);
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
      setItems(body.items || []);
    } catch (e) { setError(e instanceof Error ? e.message : "Falha ao consultar itens no PNCP."); }
    finally { setLoading(false); }
  }

  return <section className="buyer-catalog">
    <article className="module-intro card">
      <div className="module-icon"><ShoppingBasket /></div>
      <div><label>PNCP · CATÁLOGO DE COMPRADORES</label><h2>Órgãos, unidades e itens solicitados</h2>
        <p>Selecione o órgão comprador, a unidade e uma contratação. Os itens são consultados na API pública do PNCP, sem inferir conteúdo a partir do objeto.</p>
      </div>
    </article>
    <div className="buyer-toolbar">
      <input aria-label="Pesquisar comprador" placeholder="Pesquisar órgão, CNPJ ou município" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === "Enter" && void loadBuyers()} />
      <select aria-label="Filtrar UF" value={uf} onChange={e => { setUf(e.target.value); }}><option value="">Todas as UFs</option>{["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"].map(state => <option key={state}>{state}</option>)}</select>
      <button className="text-action" onClick={() => void loadBuyers()} disabled={loading}><RefreshCw size={13}/>{loading ? "A CONSULTAR" : "PESQUISAR"}</button>
    </div>
    {error && <article className="notice"><AlertCircle size={17}/><p><b>Consulta não concluída.</b> {error}</p></article>}
    <div className="buyer-layout">
      <article className="card buyer-selector">
        <div className="cardhead"><div><label>CAPTURA DISPONÍVEL</label><h3>Órgãos compradores</h3></div><span className="statusline"><i className="pending"/>{coverage}</span></div>
        <p className="buyer-muted">Fonte: LICITACAO · {buyers.length} resultados nesta página</p>
        <div className="buyer-list">{buyers.map(row => <button key={row.cnpj} className={selectedBuyer === row.cnpj ? "buyer-option selected" : "buyer-option"} onClick={() => void chooseBuyer(row.cnpj)}>
          <b>{row.name || "Órgão sem denominação"}</b><small>{row.cnpj} · {row.unit_count} unidade(s) · {row.contract_count} contratação(ões)</small>
          {!row.cnpj_valid && <em>CNPJ requer revisão de dígitos verificadores</em>}
        </button>)}</div>
        <small className="buyer-muted">Captura em: {capturedAt || "não informada"}</small>
      </article>
      <div className="buyer-detail">
        <article className="card">
          <label>1 · UNIDADE COMPRADORA</label>
          <h3>{buyer?.name || "Selecione um órgão comprador"}</h3>
          <div className="buyer-select-wrap"><select value={selectedUnit} onChange={e => void chooseUnit(e.target.value)} disabled={!buyer}><option value="">Selecione uma unidade</option>{buyer?.units.map(row => <option key={row.code + row.uf + row.municipio} value={row.code}>{row.name} · {row.municipio}/{row.uf} · {row.contract_count} contratação(ões)</option>)}</select><ChevronDown/></div>
          {unit && <p className="buyer-muted">CNPJ {selectedBuyer} · código da unidade {unit.code} · IBGE {unit.codigo_ibge || "não informado"}</p>}
        </article>
        <article className="card">
          <label>2 · CONTRATAÇÕES DA UNIDADE</label>
          <h3>{contracts.length ? `${contracts.length} contratação(ões) no snapshot` : "Selecione uma unidade"}</h3>
          <div className="buyer-select-wrap"><select value={selectedContract} onChange={e => void chooseContract(e.target.value)} disabled={!unit}><option value="">Selecione uma contratação</option>{contracts.map(row => <option key={row.control_id} value={row.control_id}>{row.number || row.sequence} · {row.object?.slice(0,100)}</option>)}</select><ChevronDown/></div>
          {contract && <><p className="buyer-muted">{contract.status} · {contract.process || "Processo não informado"} · Valor estimado: {money(contract.estimated_value)}</p><p className="buyer-contract-object">{contract.object}</p>{contract.pncp_url && <a href={contract.pncp_url} target="_blank" rel="noreferrer">Abrir contratação no PNCP ↗</a>}</>}
        </article>
        <article className="card">
          <div className="cardhead"><div><label>3 · ITENS SOLICITADOS</label><h3>{items.length ? `${items.length} item(ns) retornado(s) pelo PNCP` : "Itens da contratação"}</h3></div></div>
          {!selectedContract && <p className="buyer-muted">Selecione uma contratação para consultar os itens reais.</p>}
          {selectedContract && !items.length && !loading && <p className="buyer-muted">A API não devolveu itens para esta contratação ou a resposta está vazia.</p>}
          {items.map(item => <div className="buyer-item" key={item.number}>
            <div className="buyer-item-head"><b>Item {item.number}</b><span>{item.type || "Tipo não informado"} · {item.status || "Estado não informado"}</span></div>
            <p>{item.description || "Descrição não informada"}</p>
            <div className="buyer-item-meta"><span>Qtd. <b>{item.quantity ?? "—"} {item.unit || ""}</b></span><span>Unitário <b>{money(item.unit_estimated_value)}</b></span><span>Total <b>{money(item.total_estimated_value)}</b></span></div>
            <small>Catálogo: {item.catalog_code || "—"} · NCM/NBS: {item.ncm_nbs_code || "—"} · Orçamento sigiloso: {item.budget_confidential ? "Sim" : item.budget_confidential === false ? "Não" : "Não informado"}</small>
          </div>)}
        </article>
      </div>
    </div>
    <article className="notice"><AlertCircle size={17}/><p><b>Limite de cobertura.</b> O catálogo de compradores utiliza a captura parcial de 34 contratações (30 CNPJs) da fonte LICITACAO. A consulta de itens é feita por contratação, diretamente à API pública do PNCP. Isto não representa o histórico integral de compras de cada órgão ou unidade.</p></article>
  </section>;
}
