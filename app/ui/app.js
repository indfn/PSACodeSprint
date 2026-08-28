let currentRunId = null;
let eventSource = null;
const _hitlTimers = {};
let notifCount = 0;

const PROBLEM_LABELS = {
  "pb-12-itt": "PB-12 \u2014 ITT Coordination (Flagship)",
  "pb-01-berth": "PB-01 \u2014 Berth Delay Cascade",
  "pb-02-dtqc": "PB-02 \u2014 DTQC Contamination",
  "pb-04-feeder": "PB-04 \u2014 Feeder Schedule Cascade",
  "pb-09-expressway": "PB-09 \u2014 Expressway Gridlock",
  "pb-10-sea-air": "PB-10 \u2014 Sea-Air Bifurcation",
  "pb-11-customs": "PB-11 \u2014 Customs Clearance Block",
};

const STEPS = ["Ingest","Query PPT","Query Road","Query Sea","Optimize","HITL-1","HITL-2","HITL-3","Dispatch","Tuas Update","HITL-4","Monitor","Re-plan","HITL-5","Delta Dispatch","Final Tuas","Complete"];

function esc(s){const d=document.createElement("div");d.textContent=s==null?"":String(s);return d.innerHTML}

function setStatus(text, tone){
  const el=document.getElementById("agent-status");
  const hint=document.getElementById("ops-step-hint");
  if(el){el.textContent=text;el.className="incident__status"+(tone?" is-"+tone:"")}
  if(hint) hint.textContent=text;
}
function populateProblemSelect(){
  const sel=document.getElementById("problem-select");
  if(!sel) return;
  sel.innerHTML="";
  for(const [id,label] of Object.entries(PROBLEM_LABELS)){
    const o=document.createElement("option");o.value=id;o.textContent=label;sel.appendChild(o);
  }
}
async function loadActiveProblem(){
  try{
    const r=await fetch("/agent/active-problem");
    if(!r.ok) return;
    const d=await r.json();
    const sel=document.getElementById("problem-select");
    if(d.active_problem_id && sel) sel.value=d.active_problem_id;
    if(d.tools) renderToolChips(d.tools);
    if(d.hitl_gates) renderGateChips(d.hitl_gates);
    const plan=document.getElementById("incident-plan");
    if(plan) plan.textContent=(d.tools?d.tools.length:0)+" tools · "+(d.hitl_gates?d.hitl_gates.length:0)+" gates";
    const sub=document.getElementById("incident-plan-sub");
    if(sub) sub.textContent=(d.systems?d.systems.join(" · "):"")||"—";
  }catch(_){}
}
function renderToolChips(tools){
  const el=document.getElementById("tool-chips");
  if(!el) return;
  el.querySelectorAll("[data-chip='gate'],[data-chip='tool']").forEach(n=>n.remove());
  if(!tools||!tools.length) return;
  for(let i=0;i<tools.length;i++){
    const s=document.createElement("span");
    s.dataset.chip="tool";s.className="chip chip--tool";
    s.style.animationDelay=(i*40)+"ms";s.classList.add("in");
    s.textContent=tools[i];el.appendChild(s);
  }
}
function renderGateChips(gates){
  const el=document.getElementById("tool-chips");
  if(!el||!gates) return;
  for(let i=0;i<gates.length;i++){
    const s=document.createElement("span");
    s.dataset.chip="gate";s.className="chip chip--gate";
    s.style.animationDelay=((i+10)*40)+"ms";s.classList.add("in");
    s.textContent=gates[i];el.appendChild(s);
  }
}
function renderProblemBanner(pid, systems, tools, gates){
  const w=document.getElementById("problem-banner");
  const inner=document.getElementById("problem-banner-inner");
  if(!w||!inner) return;
  w.classList.add("is-on");
  const label=PROBLEM_LABELS[pid]||pid;
  inner.textContent="Now running: "+label+" \u00b7 "+(systems?systems.length:0)+" systems · "+(tools?tools.length:0)+" tools · "+(gates?gates.length:0)+" gates";
}
async function switchProblem(id){
  const btn=document.getElementById("switch-problem");
  if(btn){btn.disabled=true;btn.textContent="Switching\u2026"}
  try{
    const r=await fetch("/agent/switch-problem/"+encodeURIComponent(id),{method:"POST"});
    const j=await r.json();
    if(!r.ok){showError(j.detail||"Switch failed");return}
    renderProblemBanner(j.problem_id,j.systems,j.tools,j.hitl_gates);
    renderToolChips(j.tools);renderGateChips(j.hitl_gates);
    const plan=document.getElementById("incident-plan");
    if(plan) plan.textContent=(j.tools?j.tools.length:0)+" tools · "+(j.hitl_gates?j.hitl_gates.length:0)+" gates";
    const sub=document.getElementById("incident-plan-sub");
    if(sub) sub.textContent=(j.systems?j.systems.join(" · "):"")||"—";
    showBanner("Switched to "+(PROBLEM_LABELS[j.problem_id]||j.problem_id),"ok");
  }catch(e){showError(e.message||"Switch failed")}
  finally{if(btn){btn.disabled=false;btn.textContent="Switch"}}
}
function updateProgress(idx,label){
  setStatus("Step "+(idx+1)+"/17 · "+label, idx===0?"run": idx>=5&&idx<=7?"wait":"run");
  const rail=document.getElementById("progress-rail");
  if(!rail) return;
  rail.innerHTML="";
  for(let i=0;i<STEPS.length;i++){
    const s=document.createElement("span");
    const done=i<idx, active=i===idx;
    s.className="rail__step"+(done?" is-done":"")+(active?" is-active":"");
    s.title=STEPS[i];
    s.innerHTML='<span class="rail__dot"></span>'+esc(STEPS[i]);
    rail.appendChild(s);
  }
}
function showToolSkeletons(){
  const log=document.getElementById("tool-log");
  if(!log) return;
  log.innerHTML="";
  for(let i=0;i<3;i++){const sk=document.createElement("div");sk.className="skeleton";sk.style.animationDelay=(i*120)+"ms";log.appendChild(sk)}
}
function appendAgentOutput(data){
  const el=document.getElementById("agent-output");
  if(!el) return;
  let text="";
  if(typeof data==="string") text=data;
  else if(data.content) text=data.content;
  else if(data.text) text=data.text;
  else if(data.thinking) text=data.thinking;
  else {try{text=JSON.stringify(data).slice(0,700)}catch(_){text=String(data).slice(0,700)}}
  if(/^\s*\{[^}]*confidence[^}]*\}\s*$/.test(text)) return;
  if(!text.trim()) return;
  const p=document.createElement("div");
  p.textContent=text+" ";
  p.style.animation="in 200ms both";
  p.style.padding="3px 0";
  el.appendChild(p);
  el.scrollTop=el.scrollHeight;
}
function appendToolCall(data){
  const log=document.getElementById("tool-log");
  if(!log) return;
  if(log.querySelectorAll(".skeleton").length) log.innerHTML="";
  if(log.textContent.includes("Run the demo")) log.innerHTML="";
  const name=data.tool||data.name||data.tool_name||"tool";
  const args=data.args||data.arguments||data.input||{};
  let a="";try{a=JSON.stringify(args).slice(0,140)}catch(_){a=String(args).slice(0,140)}
  const row=document.createElement("div");
  row.className="tool-row in";
  row.innerHTML='<span style="display:inline-flex;align-items:center;gap:6px"><i class="ph ph-wrench" style="color:#0EA5E9"></i><span class="mono" style="color:#E2E8F0;font-size:12px">'+esc(name)+'</span></span><span class="mono" style="color:var(--dim);font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:38ch">'+esc(a)+'</span><span class="mono" style="margin-left:auto;font-size:10.5px;color:var(--faint)">calling</span>';
  log.appendChild(row);
  log.scrollTop=log.scrollHeight;
}
function appendToolResult(data){
  const log=document.getElementById("tool-log");
  if(!log) return;
  const name=data.tool||data.name||data.tool_name||"tool";
  const result=data.result||data.output||data;
  let out="";try{const r=result.output!==undefined?result.output:result;out=JSON.stringify(r).slice(0,220)}catch(_){out=String(result).slice(0,220)}
  const rows=[...log.children];
  let hit=null;
  for(let i=rows.length-1;i>=0;i--){if(rows[i].textContent.includes(name)&&rows[i].textContent.includes("calling")){hit=rows[i];break}}
  if(hit){hit.style.opacity=".72";const last=hit.querySelector("span:last-child");if(last){last.textContent=out.slice(0,88);last.style.color="#22C55E"}}
  else{
    const row=document.createElement("div");
    row.className="tool-row in";
    row.innerHTML='<span style="display:inline-flex;align-items:center;gap:6px"><i class="ph ph-check-circle" style="color:#22C55E"></i><span class="mono" style="color:#E2E8F0;font-size:12px">'+esc(name)+'</span></span><span class="mono" style="color:var(--dim);font-size:11px;max-width:48ch;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(out.slice(0,88))+'</span>';
    log.appendChild(row);
  }
  if(name==="dispatch_road_itt") armEdgeControls();
}
function renderCostSummary(card){
  const split=card.optimal_split||card.approval_card?.optimal_split||{};
  const cb=card.approval_card?.cost_breakdown||card.cost_breakdown||{};
  const vs=cb.cost_vs_baseline||{};
  const roadTrips=split.road_trips??split.roadTrips??"—";
  const sea=split.sea_containers??split.sea??"—";
  const roadC=split.road_containers??split.road??"—";
  const total=split.total_transport_cost??split.totalCost??null;
  const save=vs.savings??vs.direct_transport_savings??null;
  return {roadC, sea, roadTrips, total, save, cb};
}
function attachHITLHandlers(wrap, card){
  const a=wrap.querySelector(".approve"), r=wrap.querySelector(".reject"), m=wrap.querySelector(".modify");
  if(a) a.onclick=(e)=>respondHITL(card.gate_id,"approve",null,null,e);
  if(r) r.onclick=(e)=>{const v=prompt("Reason for rejection (operator comment):");if(v===null) return;respondHITL(card.gate_id,"reject",v||"rejected by operator",null,e)};
  if(m) m.onclick=()=>{const p=document.getElementById("modify-"+card.gate_id);if(p) p.style.display=p.style.display==="none"?"block":"none"};
}
function getModifications(gid){
  const re=document.getElementById("modify-road-"+gid), se=document.getElementById("modify-sea-"+gid);
  return {road:parseInt(re?.value)||0, sea:parseInt(se?.value)||0};
}
function startCountdown(wrap, sec, gid){
  const el=wrap.querySelector(".countdown");
  if(!el) return;
  let rem=sec;const fmt=s=>Math.floor(s/60)+":"+String(s%60).padStart(2,"0");
  el.textContent=fmt(rem);
  const id=setInterval(()=>{rem--;if(rem<=0){clearInterval(id);el.textContent="0:00 — timed out";el.style.color="var(--red)";return}el.textContent=fmt(rem)},1000);
  _hitlTimers[gid]=id;
}
function wrapCountDownCleanup(gid){if(_hitlTimers[gid]){clearInterval(_hitlTimers[gid]);delete _hitlTimers[gid]}}
function renderHITLCard(card){
  const list=document.getElementById("hitl-list"), empty=document.getElementById("hitl-empty");
  if(!list) return;
  if(empty) empty.style.display="none";
  const labels={"HITL-1":"Approve ITT split","HITL-2":"Approve truck dispatch","HITL-3":"Approve feeder hold","HITL-4":"Approve loading sequence","HITL-5":"Escalate to duty manager"};
  const isEsc=card.gate_id==="HITL-5";
  const sec=card.timeout_seconds||card.approval_card?.timeout_seconds||1800;
  const act=card.timeout_action||card.approval_card?.timeout_action||"escalate";
  const conf=card.confidence??card.approval_card?.confidence??0;
  const risk=card.risk_score??card.approval_card?.risk_score??0;
  const cs=renderCostSummary(card);
  const alts=(card.alternatives||card.approval_card?.alternatives||[]).slice(0,2);
  const wrap=document.createElement("div");
  wrap.dataset.gateId=card.gate_id;wrap.className="hitl-card"+(isEsc?" is-esc":"");
  const confCls=conf<0.85?" is-low":" is-ok";
  const confIcon=conf<0.85?"ph-warning-circle":"ph-check-circle";
  wrap.innerHTML=
    '<div class="hitl-card__top">'+
      '<div><div class="hitl-card__title">'+esc(labels[card.gate_id]||card.gate_name||card.gate_id)+ (isEsc?' <span class="chip" style="margin-left:8px;border-color:rgba(239,68,68,.22);background:rgba(239,68,68,.08);color:#FECACA"><i class="ph ph-warning"></i> Escalation</span>':"") +'</div>'+
      '<div class="mono faint" style="font-size:11px;margin-top:2px">'+esc(card.gate_name||"")+' · margin '+(card.margin_minutes??card.approval_card?.margin_minutes??"—")+' min</div></div>'+
      '<div style="text-align:right"><div class="hitl-card__id">'+esc(card.gate_id)+'</div><div class="countdown mono">'+Math.floor(sec/60)+":"+String(sec%60).padStart(2,"0")+'</div><div class="mono faint" style="font-size:10px">'+esc(act)+'</div></div>'+
    '</div>'+
    '<div class="hitl-card__grid">'+
      '<div>'+
        '<table class="cost-table"><thead><tr><th>Option</th><th class="num">Road</th><th class="num">Sea</th><th class="num">Cost</th></tr></thead><tbody>'+
          '<tr><td style="font-weight:600">Recommended</td><td class="mono num">'+esc(String(cs.roadC))+'</td><td class="mono num">'+esc(String(cs.sea))+'</td><td class="mono num accent">'+(cs.total!=null?"$"+Number(cs.total).toLocaleString():"—")+'</td></tr>'+
          alts.map(a=>'<tr><td class="faint">'+esc(a.label||"Alternative")+'</td><td class="mono num">'+esc(String(a.road_containers??a.road??"—"))+'</td><td class="mono num">'+esc(String(a.sea_containers??a.sea??"—"))+'</td><td class="mono num">'+(a.total_transport_cost!=null?"$"+Number(a.total_transport_cost).toLocaleString():"—")+'</td></tr>').join("")+
        '</tbody></table>'+
        (cs.save!=null?'<div class="mono" style="margin-top:8px;font-size:11px;color:var(--muted)">Save <span style="color:var(--accent);font-weight:650">$'+Number(cs.save).toLocaleString()+'</span> vs all-road baseline · '+esc(String(cs.roadTrips))+' truck trips</div>':"")+
        '<div class="trust'+confCls+'" style="margin-top:10px"><i class="ph '+confIcon+'"></i> Confidence '+(conf*100).toFixed(0)+'% '+(conf<0.85?'<span class="faint">· below 0.85 — escalation risk</span>':"")+' <span class="faint">· risk '+Number(risk).toFixed(2)+'</span></div>'+
      '</div>'+
      '<div class="actions">'+
        '<button class="btn btn--primary approve"><i class="ph ph-check"></i> Approve</button>'+
        '<button class="btn btn--ghost reject">Reject</button>'+
        '<button class="btn btn--ghost modify">Modify split</button>'+
        '<div class="mono faint" style="font-size:11px;text-align:center">Timeout '+Math.round(sec/60)+' min → '+esc(act)+'</div>'+
      '</div>'+
    '</div>'+
    '<div id="modify-'+esc(card.gate_id)+'" style="display:none;margin-top:12px;padding:12px;border-radius:14px;border:1px solid var(--line);background:rgba(0,0,0,.18)">'+
      '<div class="mono" style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)">Adjust split — road / sea containers</div>'+
      '<div style="margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:8px"><input id="modify-road-'+esc(card.gate_id)+'" type="number" placeholder="Road" class="field" /><input id="modify-sea-'+esc(card.gate_id)+'" type="number" placeholder="Sea" class="field" /></div>'+
      '<button class="btn btn--primary modify-submit" data-gate="'+esc(card.gate_id)+'" style="margin-top:8px;padding:7px 14px;font-size:12.5px">Submit modification</button>'+
    '</div>';
  list.appendChild(wrap);
  wrap.querySelector(".modify-submit")?.addEventListener("click",e=>{const gid=e.currentTarget.dataset.gate;respondHITL(gid,"modify",null,getModifications(gid),e)});
  attachHITLHandlers(wrap,card);
  startCountdown(wrap,sec,card.gate_id);
  wrap.scrollIntoView({behavior:"smooth",block:"nearest"});
}
async function respondHITL(gid, decision, reason, mods, evt){
  const btn=evt?evt.currentTarget:document.querySelector('[data-gate-id="'+gid+'"] .approve');
  let orig="";if(btn){orig=btn.textContent;btn.disabled=true;btn.innerHTML='<span style="display:inline-block;width:14px;height:14px;border:2px solid currentColor;border-top-color:transparent;border-radius:50%;animation:spin .6s linear infinite"></span> Sending'}
  try{
    const body={run_id:currentRunId,gate_id:gid,decision};
    if(reason) body.reason=reason;
    if(mods) body.modifications=mods;
    const r=await fetch("/agent/hitl/respond",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const j=await r.json().catch(()=>({}));
    if(!r.ok && r.status===422){showError(j.detail||"Approval window closed — already timed out","err");wrapCountDownCleanup(gid);return}
    if(!r.ok){showError(j.detail||"Action failed","err");if(btn){btn.disabled=false;btn.textContent=orig}return}
    wrapCountDownCleanup(gid);
    const el=document.querySelector('[data-gate-id="'+gid+'"]');
    if(el){el.style.opacity=".55";el.style.pointerEvents="none"}
    if(j.status==="waiting_hitl" && j.hitl_card){renderHITLCard(j.hitl_card);showBanner("Next decision required: "+(j.hitl_card.gate_id||""),"warn")}
    else if(j.status==="completed"||j.status==="complete"){renderCompletion(j.result||j.state||j);showBanner("Run complete — all gates cleared","ok")}
    else if(j.hitl_card) renderHITLCard(j.hitl_card);
  }catch(e){if(btn){btn.disabled=false;btn.textContent=orig}showError(e.message||"Network error","err")}
}
function renderCompletion(result){
  setStatus("Complete","run");
  const out=document.getElementById("agent-output");
  if(out){
    const ok=document.createElement("div");
    ok.className="banner banner--ok";ok.style.marginTop="10px";
    ok.innerHTML='<i class="ph ph-check-circle"></i> All steps cleared — dispatch and loading updates issued.';
    out.appendChild(ok);
    const pre=document.createElement("pre");
    pre.className="mono";pre.style.cssText="margin-top:10px;font-size:11px;color:var(--muted);overflow:auto;white-space:pre-wrap;word-break:break-all;background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:14px;padding:12px;max-height:220px";
    try{pre.textContent=JSON.stringify(result,null,2).slice(0,2200)}catch(_){pre.textContent=String(result).slice(0,2200)}
    out.appendChild(pre);
  }
  updateProgress(STEPS.length-1,"Complete");
}
function showError(msg){const b=document.getElementById("error-banner");if(!b) return;b.textContent=msg;b.style.display="flex";setTimeout(()=>b.style.display="none",7000)}
function showBanner(msg, kind){
  const host=document.getElementById("hitl-cards");
  if(!host) return;
  const d=document.createElement("div");
  d.className="banner "+(kind==="warn"?"banner--warn":kind==="err"?"banner--err":"banner--ok");
  d.innerHTML='<i class="ph '+(kind==="warn"?"ph-warning":kind==="err"?"ph-warning-circle":"ph-check-circle")+'"></i> '+esc(msg);
  host.prepend(d);setTimeout(()=>d.remove(),6000);
}
function armEdgeControls(){
  const c=document.getElementById("inject-conflict"), s=document.getElementById("inject-stale"), h=document.getElementById("edge-hint");
  if(c){c.style.borderColor="rgba(245,158,11,.22)";c.style.background="rgba(245,158,11,.08)";c.style.color="#FDE68A"}
  if(s){s.style.borderColor="rgba(245,158,11,.14)";s.style.background="rgba(245,158,11,.06)"}
  if(h) h.style.display="inline";
}
function pulseDeviation(){setStatus("Deviation detected","wait");setTimeout(()=>setStatus("Monitoring","run"),1800)}
function renderTraceEntry(entry){
  const host=document.getElementById("trace-sidebar"), cnt=document.getElementById("trace-count");
  if(!host) return;
  const dot={agent:"#22C55E",tool:"#0EA5E9",hitl:"#F59E0B",escalation:"#EF4444",monitor:"#8B5CF6",deviation:"#F97316",notification:"#E879F9"}[entry.node]||"rgba(255,255,255,.2)";
  const row=document.createElement("div");
  row.className="trace__row in";row.style.borderTop="1px solid rgba(255,255,255,.05)";
  const ts=entry.timestamp?entry.timestamp.slice(11,19):"";
  const risk=entry.risk_score??entry.result?.risk_score??0;
  const dur=entry.duration_ms??0;
  row.innerHTML='<span class="trace__dot" style="background:'+dot+(entry.node==="agent"?";animation:pulse-live 1.2s infinite":"")+'"></span><span class="mono" style="color:#CBD5E1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+esc(entry.node||"")+' · '+esc(entry.action||"")+'</span><span class="mono" style="color:var(--dim);white-space:nowrap">'+esc(ts)+' · '+Number(dur).toFixed(0)+'ms · '+Number(risk).toFixed(2)+'</span>';
  try{row.title=JSON.stringify(entry.result??entry,null,2)}catch(_){}
  host.appendChild(row);host.scrollTop=host.scrollHeight;
  if(cnt) cnt.textContent=host.children.length+" entries";
}
function renderEscalation(d){showBanner("Escalation: "+(d.message||d.reason||JSON.stringify(d).slice(0,180)),"warn");pulseDeviation()}
function renderDeviation(d){showBanner("Deviation: "+(d.message||d.deviation||JSON.stringify(d).slice(0,180)),"warn");pulseDeviation()}
function updateConfidence(data){
  const s=document.getElementById("confidence-score"), b=document.getElementById("confidence-bar"), det=document.getElementById("confidence-detail");
  let c=0;
  if(typeof data==="number") c=data;
  else if(data.confidence!==undefined) c=data.confidence;
  else if(data.score!==undefined) c=data.score;
  else if(data.value!==undefined) c=data.value;
  c=Number(c)||0;
  if(s) s.textContent=c.toFixed(2);
  if(b){b.style.width=(c*100).toFixed(0)+"%";b.className="meter__fill"+(c<0.85?" is-low":"")}
  if(det) det.textContent=c<0.85?"Below 0.85 — review needed":"Above threshold";
}
function onNotification(data){
  notifCount++;
  const panel=document.getElementById("notification-panel"), list=document.getElementById("notification-list"), empty=document.getElementById("notification-empty");
  if(panel) panel.style.display="block";
  if(empty) empty.style.display="none";
  const badge=document.getElementById("notif-badge");
  if(badge){badge.textContent=String(notifCount);badge.style.display="grid";badge.animate([{transform:"scale(0)"},{transform:"scale(1.18)"},{transform:"scale(1)"}],{duration:320,easing:"cubic-bezier(.16,1,.3,1)"})}
  if(!list) return;
  const li=document.createElement("li");
  li.className="banner banner--ok in";li.style.justifyContent="space-between";li.style.gap="10px";
  const parties=Array.isArray(data.parties)?data.parties:[];
  const pills=parties.map(p=>'<span class="chip" style="padding:3px 8px;font-size:11px">'+esc(p)+'</span>').join("");
  const ts=data.timestamp?data.timestamp.slice(11,19):"";
  const msg=data.message||"";
  li.innerHTML='<span style="display:flex;flex-wrap:wrap;gap:4px">'+pills+'</span><span class="mono faint" style="font-size:11px">'+esc(ts)+'</span><span style="font-size:12.5px;flex:1;text-align:right">'+esc(msg)+'</span>';
  list.prepend(li);
}
function connectSSE(runId){
  if(eventSource){try{eventSource.close()}catch(_){}}
  const es=new EventSource("/agent/stream/"+encodeURIComponent(runId));
  eventSource=es;
  es.addEventListener("agent_thinking",e=>{try{appendAgentOutput(JSON.parse(e.data))}catch(_){appendAgentOutput(e.data)}});
  es.addEventListener("tool_call",e=>{try{appendToolCall(JSON.parse(e.data))}catch(_){}});
  es.addEventListener("tool_result",e=>{try{const d=JSON.parse(e.data);appendToolResult(d);if((d.tool||d.name)==="dispatch_road_itt") armEdgeControls()}catch(_){}});
  es.addEventListener("hitl_card",e=>{try{renderHITLCard(JSON.parse(e.data))}catch(_){}});
  es.addEventListener("escalation",e=>{try{renderEscalation(JSON.parse(e.data))}catch(_){}});
  es.addEventListener("trace_entry",e=>{try{renderTraceEntry(JSON.parse(e.data))}catch(_){}});
  es.addEventListener("deviation",e=>{try{renderDeviation(JSON.parse(e.data));pulseDeviation()}catch(_){}});
  es.addEventListener("confidence_update",e=>{try{updateConfidence(JSON.parse(e.data))}catch(_){}});
  es.addEventListener("notification",e=>{try{onNotification(JSON.parse(e.data))}catch(_){}});
  es.onerror=()=>{/* EventSource auto-retries; avoid spam */};
}
document.getElementById("run-demo")?.addEventListener("click", async()=>{
  const btn=document.getElementById("run-demo");
  if(btn){btn.disabled=true;btn.innerHTML='<span class="pulse-live">Launching</span>'}
  showToolSkeletons();
  const out=document.getElementById("agent-output");
  if(out) out.innerHTML='<div class="faint mono" style="font-size:12px">Orchestrator starting — querying CITOS, OptETruck, PORTNET…</div>';
  const hl=document.getElementById("hitl-list");
  if(hl) hl.innerHTML="";
  const he=document.getElementById("hitl-empty");
  if(he) he.style.display="flex";
  const eb=document.getElementById("error-banner");
  if(eb) eb.style.display="none";
  updateProgress(0,"Starting");
  try{
    const r=await fetch("/agent/run-demo",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});
    const j=await r.json().catch(()=>({}));
    if(!r.ok){showError(j.detail||"Run failed");if(btn){btn.disabled=false;btn.innerHTML='<i class="ph ph-play"></i> Run demo'}return}
    currentRunId=j.run_id;
    connectSSE(j.run_id);
    if(j.status==="waiting_hitl" && j.hitl_card) renderHITLCard(j.hitl_card);
    updateProgress(1, j.status==="waiting_hitl"?"Awaiting approval — "+(j.hitl_card?.gate_id||"HITL"):"Running");
    setStatus(j.status==="waiting_hitl"?"Awaiting approval":"Running", j.status==="waiting_hitl"?"wait":"run");
  }catch(e){showError(e.message||"Run failed")}
  finally{if(btn) setTimeout(()=>{btn.disabled=false;btn.innerHTML='<i class="ph ph-play"></i> Run demo'},900)}
});
document.getElementById("reset")?.addEventListener("click", async()=>{
  if(currentRunId){try{await fetch("/agent/reset/"+encodeURIComponent(currentRunId),{method:"POST"})}catch(_){}try{if(eventSource) eventSource.close()}catch(_){}}
  try{await fetch("/agent/reset-mocks",{method:"POST"})}catch(_){}
  currentRunId=null;notifCount=0;
  const b=document.getElementById("notif-badge");if(b){b.textContent="0";b.style.display="none"}
  const p=document.getElementById("notification-panel");if(p) p.style.display="none";
  const en=document.getElementById("notification-empty");if(en) en.style.display="block";
  const nl=document.getElementById("notification-list");if(nl) nl.innerHTML="";
  const tl=document.getElementById("tool-log");if(tl) tl.innerHTML='<div class="faint" style="font-size:12.5px;padding:10px 0">Run the demo to see live tool coordination.</div>';
  const ts=document.getElementById("trace-sidebar");if(ts) ts.innerHTML="";
  const tc=document.getElementById("trace-count");if(tc) tc.textContent="0 entries";
  const hl=document.getElementById("hitl-list");if(hl) hl.innerHTML="";
  const he=document.getElementById("hitl-empty");if(he) he.style.display="flex";
  const out=document.getElementById("agent-output");if(out) out.innerHTML="";
  setStatus("Idle","");document.getElementById("ops-step-hint").textContent="Idle";
  const rail=document.getElementById("progress-rail");if(rail) rail.innerHTML="";
  const cs=document.getElementById("confidence-score");if(cs) cs.textContent="—";
  const cb=document.getElementById("confidence-bar");if(cb){cb.style.width="0";cb.className="meter__fill"}
  const cd=document.getElementById("confidence-detail");if(cd) cd.textContent="";
  const cbtn=document.getElementById("inject-conflict");if(cbtn){cbtn.disabled=false;cbtn.style.borderColor="";cbtn.style.background="";cbtn.style.color=""}
  const sbtn=document.getElementById("inject-stale");if(sbtn){sbtn.disabled=false;sbtn.style.borderColor="";sbtn.style.background="";sbtn.style.color=""}
  const hint=document.getElementById("edge-hint");if(hint) hint.style.display="none";
  for(const k of Object.keys(_hitlTimers)) wrapCountDownCleanup(k);
  const eb=document.getElementById("error-banner");if(eb) eb.style.display="none";
  showBanner("Console reset — ready for next incident","ok");
});
document.getElementById("inject-conflict")?.addEventListener("click", async()=>{
  if(!currentRunId){showError("Start a run first");return}
  try{
    const r=await fetch("/agent/inject-edge-case",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({run_id:currentRunId,type:"feeder_conflict",feeder_id:"FEEDER ATLANTIC-03",new_departure:"2026-08-19T16:00:00+08:00"})});
    const j=await r.json().catch(()=>({}));if(!r.ok){showError(j.detail||"Inject failed");return}
    showBanner("Berth conflict injected — monitor will flag it on next check","warn");
    document.getElementById("inject-conflict").disabled=true;
  }catch(e){showError(e.message)}
});
document.getElementById("inject-stale")?.addEventListener("click", async()=>{
  if(!currentRunId){showError("Start a run first");return}
  try{
    const r=await fetch("/agent/inject-edge-case",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({run_id:currentRunId,type:"stale_data",minutes:35})});
    const j=await r.json().catch(()=>({}));if(!r.ok){showError(j.detail||"Inject failed");return}
    showBanner("Stale-data flag set — next query will report aged data","warn");
    document.getElementById("inject-stale").disabled=true;
  }catch(e){showError(e.message)}
});
document.getElementById("switch-problem")?.addEventListener("click",()=>{
  const sel=document.getElementById("problem-select");
  if(sel) switchProblem(sel.value);
});
populateProblemSelect();
loadActiveProblem();
setStatus("Idle","");
const _spin=document.createElement("style");
_spin.textContent="@keyframes spin{to{transform:rotate(360deg)}}";
document.head.appendChild(_spin);
