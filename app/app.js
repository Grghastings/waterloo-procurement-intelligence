let rows=[];
const $=x=>document.getElementById(x);
function esc(s){return String(s??"").replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]))}
function contactText(x){
  const c=Array.isArray(x.contacts)?x.contacts[0]:null;
  if(!c)return "";
  return [c.name,c.email,c.phone].filter(Boolean).join(" · ");
}
function render(){
  let q=$("q").value.toLowerCase(),r=$("r").value;
  let a=rows.filter(x=>(!q||JSON.stringify(x).toLowerCase().includes(q))&&(!r||x.recommendation===r));
  $("cards").innerHTML=a.slice(0,100).map(x=>`<article class="card">
    <div class="score">${x.score??0}</div>
    <div>
      <div class="title">${esc(x.title)}</div>
      <div class="meta">${esc(x.organization||"Unknown agency")} · ${esc(x.state||x.country||"")} · ${esc(x.notice_type||"")} · Deadline ${esc(x.deadline||"—")}</div>
      ${x.naics?`<div class="meta">NAICS ${esc(x.naics)}${x.solicitation_number?` · ${esc(x.solicitation_number)}`:""}</div>`:""}
      ${contactText(x)?`<div class="meta">POC: ${esc(contactText(x))}</div>`:""}
      <p>${esc(x.fit_reason)}</p>
      <span class="badge">${esc(x.recommendation)}</span>
    </div>
    <a target="_blank" rel="noopener" href="${esc(x.url||"#")}">Open ↗</a>
  </article>`).join("")||"<p>No matches.</p>"
}
async function init(){
  $("date").textContent=new Date().toLocaleDateString(undefined,{dateStyle:"long"});
  try{
    rows=await (await fetch("data-opportunities.json",{cache:"no-store"})).json();
  }catch(e){
    $("cards").innerHTML="<p>Could not load procurement data. Run the daily collector and refresh.</p>";
    return;
  }
  $("n").textContent=rows.length;
  $("p").textContent=rows.filter(x=>x.recommendation==="PURSUE").length;
  $("i").textContent=rows.filter(x=>x.recommendation==="INVESTIGATE").length;
  $("u").textContent=rows.filter(x=>x.deadline&&((new Date(x.deadline)-new Date())/864e5)<=14).length;
  $("q").oninput=render;
  $("r").onchange=render;
  render();
}
init();
