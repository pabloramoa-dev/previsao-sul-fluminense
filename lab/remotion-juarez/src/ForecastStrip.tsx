import React from 'react';

/**
 * Painel editorial do SulFlu, inspirado nas técnicas de Data Storytelling e
 * Broadcast News Package do Lemo Opuscar. Exibe exclusivamente os números
 * recebidos do pacote meteorológico do próprio vídeo. Não gera previsão.
 */
type Cidade = {nome:string;min:number;max:number;cond:string;chuva_mm?:number};
const clamp=(v:number,a:number,b:number)=>Math.max(a,Math.min(b,v));
const value=(v:unknown)=>typeof v==='number'&&Number.isFinite(v)?Math.max(0,v):null;

export const ForecastStrip:React.FC<{cidades:Cidade[];t:number;dur:number;cta:boolean;data:string}>=({cidades,t,dur,cta,data})=>{
  const pages=Math.max(1,Math.ceil(cidades.length/5));
  const totalTime=Math.max(4,dur-6);
  const length=totalTime/pages;
  const page=clamp(Math.floor(Math.max(0,t-2.7)/length),0,pages-1);
  const rows=cidades.slice(page*5,page*5+5);
  const rainfall=cidades.some(c=>value(c.chuva_mm)!==null);
  const maxRain=Math.max(1,...cidades.map(c=>value(c.chuva_mm)??0));
  const dateFmt=/^\d{4}-\d{2}-\d{2}$/.test(data)?data.slice(8,10)+'/'+data.slice(5,7)+'/'+data.slice(0,4):'BOLETIM REGIONAL';
  const opacity=clamp((t-.1)*3,0,1)*clamp((dur-t)*2.5,0,1);
  return <>
    <div style={{position:'absolute',left:30,top:1640,width:1020,height:250,zIndex:19,opacity,
      borderRadius:13,overflow:'hidden',border:'2px solid #466981',
      background:'linear-gradient(130deg,rgba(9,27,43,.97),rgba(21,53,77,.97))',
      boxShadow:'0 15px 45px #061320aa',color:'#fff'}}>
      <div style={{height:44,display:'flex',alignItems:'center',padding:'0 17px',
        background:'linear-gradient(90deg,#d84a3b 0%,#b82b2c 42%,#183b59 42%)',
        fontSize:20,fontWeight:900,letterSpacing:1}}>
        <span>PLANTÃO SULFLU</span>
        <span style={{marginLeft:'auto',fontSize:18,fontWeight:700}}>BOLETIM {dateFmt}</span>
      </div>
      {cta?<div style={{padding:'31px 35px'}}>
          <div style={{fontSize:34,fontWeight:900,color:'#ffdb69'}}>PREVISÃO NO SEU BAIRRO</div>
          <div style={{fontSize:27,fontWeight:800,marginTop:10}}>Mande o nome por mensagem.</div>
        </div>:t<2.7?<div style={{padding:'36px'}}>
          <div style={{fontSize:43,fontWeight:950,color:'#ffd253'}}>GIRO METEOROLÓGICO</div>
          <div style={{fontSize:28,marginTop:10,color:'#cce3ee'}}>Cidades do Sul Fluminense • Dados do dia</div>
        </div>:<>
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'8px 28px 4px'}}>
          <span style={{fontSize:23,fontWeight:900,color:'#ffe078'}}>{rainfall?'CHUVA PREVISTA NAS CIDADES':'TEMPERATURA NAS CIDADES'}</span>
          <span style={{fontSize:17,color:'#add5e8',fontWeight:800}}>PAINEL {page+1}/{pages}</span>
        </div>
        <div style={{padding:'0 30px'}}>
          {rows.map((c,i)=>{
            const mm=value(c.chuva_mm);
            const reveal=clamp((t-(2.7+page*length+i*.12))/.5,0,1);
            const fraction=rainfall?(mm??0)/maxRain:clamp((c.max-c.min)/20,0,1);
            return <div key={page+'-'+i+'-'+c.nome} style={{height:33,display:'flex',gap:14,alignItems:'center',borderBottom:'1px solid #38576a',
              opacity:reveal,transform:'translateX('+((1-reveal)*30)+'px)'}}>
              <span style={{width:220,fontSize:17,fontWeight:800,overflow:'hidden',whiteSpace:'nowrap',textOverflow:'ellipsis'}}>{c.nome.toUpperCase()}</span>
              <div style={{height:11,flex:1,background:'#31556a',borderRadius:8,overflow:'hidden'}}>
                <div style={{height:'100%',width:(100*fraction*reveal)+'%',background:rainfall&&mm!==null&&mm>=10?'#f4b750':'#62cce3',borderRadius:8}}/>
              </div>
              <span style={{fontSize:19,fontWeight:900,width:117,textAlign:'right',color:'#ffdf82'}}>
                {rainfall?(mm===null?'—':mm.toFixed(1).replace('.',',')+' mm'):Math.round(c.min)+'°/'+Math.round(c.max)+'°'}
              </span>
            </div>;
          })}
        </div>
        </>}
      <div style={{position:'absolute',bottom:0,left:0,height:5,background:'#f7d64c',width:(100*clamp(t/Math.max(dur,1),0,1))+'%'}}/>
    </div>
    <div style={{position:'absolute',left:865,top:51,width:169,height:42,zIndex:19,borderRadius:7,
      background:'#112a40e8',border:'1px solid #43647b',display:'flex',alignItems:'center',justifyContent:'center',
      fontSize:18,fontWeight:900,letterSpacing:1,color:'#ffda6e'}}>
      <span style={{color:'#ed6253',marginRight:8}}>●</span>SULFLU NEWS
    </div>
  </>;
};
