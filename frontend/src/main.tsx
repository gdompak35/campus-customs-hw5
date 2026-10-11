import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import './dan.css';
import './readability.css';
import './token.css';
import './huddle.css';
import './photo.css';
import './boss-modal.css';
import './boss-hint.css';
import './decision.css';
import './activity.css';
import './activity-dates.css';

const API = 'http://localhost:8000';
type Ticket = { id:number; type:string; requester:string; subject:string; sku?:string; size?:string; qty?:number; status:string; notes:string };
type AuditEvent = { timestamp:string; agent:string; step:string; ticket_id?:number; detail:any };
const roles = ['boss','inventory','accounting','facilities','customer_service'];
const roleNames: Record<string,string> = {boss:'Boss',inventory:'Inventory',accounting:'Accounting',facilities:'Facilities',customer_service:'Customer Service'};
const roleColors: Record<string,string> = {boss:'#d56b4d',inventory:'#3b86a8',accounting:'#6d62a8',facilities:'#b17a45',customer_service:'#448b72'};

const displayEventDate = (date: Date) => date.toLocaleString([], {month:'short', day:'numeric', hour:'numeric', minute:'2-digit'});

async function get<T>(path:string):Promise<T>{ const r=await fetch(API+path); if(!r.ok) throw new Error(await r.text()); return r.json(); }
async function post<T>(path:string, body?:any):Promise<T>{ const r=await fetch(API+path,{method:'POST',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined}); if(!r.ok) throw new Error(await r.text()); return r.json(); }

function App(){
  const [tickets,setTickets]=useState<Ticket[]>([]), [selected,setSelected]=useState<number>(101), [events,setEvents]=useState<AuditEvent[]>([]), [cash,setCash]=useState<any>(null), [running,setRunning]=useState(false), [error,setError]=useState(''), [bossExpanded,setBossExpanded]=useState(false);
  const [danVisible,setDanVisible]=useState(false);
  useEffect(()=>{setDanVisible(false);const rise=setTimeout(()=>setDanVisible(true),1300);const lower=setTimeout(()=>setDanVisible(false),5300);return()=>{clearTimeout(rise);clearTimeout(lower)}},[selected]);
  useEffect(()=>{if(running){const image=document.querySelector<HTMLImageElement>('.huddle-rings img');if(image)image.src='/handsome-dan-office.png'}},[running]);
  const ticket=tickets.find(t=>t.id===selected); const ticketEvents=events.filter(e=>e.ticket_id===selected);
  useEffect(()=>{const labels=Array.from(document.querySelectorAll('.activity .event small'));ticketEvents.slice().reverse().forEach((event,index)=>{if(labels[index])labels[index].textContent=displayEventDate(new Date(event.timestamp))})},[ticketEvents]);
  const agentState=useMemo(()=>Object.fromEntries(roles.map(r=>[r, ticketEvents.filter(e=>e.agent===r).slice(-1)[0]])),[ticketEvents]);
  const usage=useMemo(()=>{const completed=ticketEvents.filter(e=>e.step==='run_complete').slice(-1)[0];return completed?.detail?.usage||{}},[ticketEvents]);
  const bossResult=ticketEvents.filter(e=>e.agent==='boss'&&e.step==='run_complete').slice(-1)[0];
  useEffect(()=>{const open=(event:Event)=>{if(!bossResult||(event.target as Element)?.closest('.agent-grid .agent:first-child')===null)return;const modal=document.createElement('div');modal.className='boss-modal';modal.innerHTML=`<div class="boss-window"><button class="boss-close" aria-label="Close">×</button><p class="eyebrow">BOSS DECISION · TICKET #${selected}</p><h2>What the team decided</h2><div class="boss-decision">${bossResult.detail?.decision||'No decision recorded.'}</div></div>`;document.body.appendChild(modal);const close=()=>modal.remove();modal.querySelector('.boss-close')?.addEventListener('click',close);modal.addEventListener('click',e=>{if(e.target===modal)close()})};document.addEventListener('click',open);return()=>document.removeEventListener('click',open)},[bossResult,selected]);
  const load=async()=>{try{const [ts,ev,c]=await Promise.all([get<Ticket[]>('/api/tickets'),get<AuditEvent[]>('/api/events?limit=200'),get<any>('/api/cash')]);setTickets(ts);setEvents(ev);setCash(c);setError('')}catch(e){setError(String(e))}};
  useEffect(()=>{load()},[]);
  const run=async()=>{setRunning(true);setError('');try{await post(`/api/tickets/${selected}/run`);await load()}catch(e){setError(String(e))}finally{setRunning(false)}};
  const approve=async()=>{if(!ticket) return; const kind=prompt('Approval type: invoice, lease, or purchase','invoice')||''; const ref=Number(prompt('Database reference ID','501')); const who=prompt('Human approver name','Shop manager')||''; if(!['invoice','lease','purchase'].includes(kind)||!ref||!who)return;try{await post('/api/approvals',{kind,ref_id:ref,approved_by:who});await load()}catch(e){setError(String(e))}};
  return <div className="app"><img className={`dan ${danVisible?'dan-visible':''}`} src="/bulldog-mascot.png" alt="Handsome Dan, Campus Customs mascot"/>{running&&<div className="huddle" role="status"><div className="huddle-card"><div className="huddle-rings"><span></span><span></span><img src="/bulldog-mascot.png" alt="Handsome Dan watching the team"/></div><p className="eyebrow">TEAM HUDDLE IN PROGRESS</p><h2>Handsome Dan is keeping watch.</h2><p>The agents are reading the ticket, checking shop facts, and handing work to one another.</p><div className="typing"><i></i><i></i><i></i></div></div></div>}<header><div className="brand"><span className="crest">CC</span><div><div className="eyebrow">CAMPUS CUSTOMS</div><h1>Operations desk</h1></div></div><div className="balance"><span>CHECKING BALANCE</span><strong>{cash?`$${Number(cash.balance).toLocaleString()}`:'—'}</strong></div></header>
    <main><section className="hero"><div><p className="eyebrow">THE SHOP FLOOR</p><h2>Keep the work moving.</h2><p>Watch the team think through each open ticket, then step in when a real-world approval is needed.</p></div><img src="/bulldog-mascot.png" alt="Campus Customs bulldog mascot"/></section>
    {error&&<div className="error">{error}</div>}<div className="layout"><aside><div className="ticket-list"><div className="section-label">TICKETS <span>{tickets.length}</span></div>{tickets.map(t=><button className={`ticket ${selected===t.id?'chosen':''}`} onClick={()=>setSelected(t.id)} key={t.id}><span className={`status ${t.status}`}></span><span><b>#{t.id} · {t.subject}</b><small>{t.requester}</small></span><em>{t.status}</em></button>)}</div><div className="token-card"><div className="section-label">TOKEN USE</div><strong>{usage.total_tokens??'—'}</strong><p>Actual model tokens for this ticket</p><div className="token-cost"><span>Input / output</span><b>{usage.input_tokens??'—'} / {usage.output_tokens??'—'}</b></div><small>Reported by PydanticAI after the agent run. Dollar pricing is not configured.</small></div></aside>
    <section className="workspace">{ticket&&<><div className="ticket-head"><div><p className="eyebrow">TICKET #{ticket.id} · {ticket.type.replace('_',' ')}</p><h2>{ticket.subject}</h2><p>{ticket.requester} · {ticket.sku||'Lease / facilities request'} {ticket.size?`· size ${ticket.size}`:''} {ticket.qty?`· qty ${ticket.qty}`:''}</p></div><button className="primary" disabled={running} onClick={run}>{running?'Team is working…':'Start agent team'}</button></div><div className="agent-grid">{roles.map(r=><div className="agent" key={r} style={{'--role':roleColors[r]} as React.CSSProperties}><div className="agent-top"><span className="avatar">{roleNames[r][0]}</span><div><b>{roleNames[r]}</b><small>{agentState[r]?.step?.replaceAll('_',' ')||'Standing by'}</small></div><i className={agentState[r]?'live':''}></i></div><p>{agentState[r]?eventText(agentState[r]):'Ready to help the desk resolve this ticket.'}</p></div>)}</div><div className="lower"><div className="summary card"><div className="card-title">Ticket brief <span className={`pill ${ticket.status}`}>{ticket.status}</span></div><p>{ticket.notes}</p><div className="actions"><button className="secondary" onClick={load}>Refresh board</button><button className="approve" onClick={approve}>Approve payment / purchase</button></div></div><div className="activity card"><div className="card-title">Live activity <span>{ticketEvents.length} events</span></div>{ticketEvents.length?ticketEvents.slice().reverse().map((e,i)=><div className="event" key={i}><span style={{background:roleColors[e.agent]||'#6b7a90'}}></span><div><b>{roleNames[e.agent]||e.agent}</b><small>{new Date(e.timestamp).toLocaleTimeString([], {hour:'numeric',minute:'2-digit'})}</small><p>{eventText(e)}</p></div></div>):<p className="muted">Start a run to see the team’s work appear here.</p>}</div></div></>}</section></div></main><footer>Campus Customs <span>Human judgment, thoughtfully assisted.</span></footer></div>
}
function eventText(e:AuditEvent){if(e.step==='mcp_call_start')return `Calling ${e.detail?.tool||'shop data'}…`;if(e.step==='mcp_call_complete')return `Received database-backed facts from ${e.detail?.tool||'MCP'}.`;if(e.step==='run_start')return 'Reading the ticket and planning the handoffs.';if(e.step==='run_complete')return String(e.detail?.decision||'Finished the team review.');return e.step.replaceAll('_',' ')}
createRoot(document.getElementById('root')!).render(<App/>);
