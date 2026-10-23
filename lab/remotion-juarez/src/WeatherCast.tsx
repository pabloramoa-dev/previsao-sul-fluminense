import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export type WeatherCity={nome:string;min:number;max:number;cond:string;chuva_mm?:number};
export type WeatherBeat={tipo:string;ini:number;fim:number;legenda?:string};
export type WeatherCastProps={durationFrames:number;data:string;cidades:WeatherCity[];batidas:WeatherBeat[];demo?:boolean};
const clamp=(x:number,a:number,b:number)=>Math.max(a,Math.min(b,x));
const condition=(cond:string)=>({sol:'SOL',calor:'CALOR',abafado:'ABAFADO',ameno:'AMENO',nublado:'NUBLADO',chuva:'CHUVA',tempestade:'TEMPORAL',frio:'FRIO'} as Record<string,string>)[cond]||'TEMPO';
const tint=(cond:string)=>cond.includes('chuva')||cond==='tempestade'?'#6bd1f2':cond==='sol'||cond==='calor'?'#ffd453':'#cae2e3';
const SunCloud:React.FC<{cond:string}>=({cond})=><div style={{width:75,height:75,position:'relative',flexShrink:0}}>
  {cond==='sol'||cond==='calor'?
   <div style={{width:52,height:52,borderRadius:'50%',background:'#ffc533',border:'5px solid #23374a',boxShadow:'0 0 0 9px #ffd75a39',position:'absolute',left:13,top:11}}/>:
   <><div style={{position:'absolute',width:67,height:30,background:'#e1e8ee',border:'4px solid #263d4b',borderRadius:25,top:32,left:4}}/>
   <div style={{position:'absolute',width:39,height:39,background:'#e1e8ee',border:'4px solid #263d4b',borderBottom:0,borderRadius:'50%',top:15,left:18}}/>
   {(cond==='chuva'||cond==='tempestade')&&<div style={{position:'absolute',left:22,top:59,fontWeight:900,color:'#146cca',fontSize:30}}>•••</div>}</>}
 </div>;

export const WeatherCast:React.FC<WeatherCastProps>=({cidades,data,batidas,demo=true})=>{
 const frame=useCurrentFrame(),{fps,durationInFrames}=useVideoConfig(),t=frame/fps;
 const cityList=cidades.length?cidades:[{nome:'Sul Fluminense',min:0,max:0,cond:'sol'}];
 const firstTime=2.0,period=4.2;
 const sequence=Math.floor(Math.max(0,t-firstTime)/period);
 const active=cityList[sequence%cityList.length];
 const phase=t<firstTime?0:Math.max(0,t-firstTime)%period;
 const enter=spring({frame:(phase-.1)*fps,fps,config:{damping:17,stiffness:150}});
 const exit=clamp((period-phase)*2.1,0,1);
 // O cartão some no CTA, preservando a chamada original do programa.
 const cta=batidas.some(b=>b.tipo==='cta'&&t>=b.ini-.2&&t<=b.fim+.4);
 const cardOpacity=t<firstTime||cta?0:Math.min(1,Math.max(0,enter),exit*3);
 const color=tint(active.cond||'sol');
 const pulse=0.4+Math.abs(Math.sin(t*3))*0.6;
 const barWidth=interpolate(frame,[0,durationInFrames],[0,100],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const transition=batidas.reduce((max,b)=>{
   const delta=Math.abs(t-b.ini);
   return Math.max(max,clamp((.25-delta)/.25,0,1));
 },0);
 return <AbsoluteFill style={{backgroundColor:'#10263b',fontFamily:'Arial,Helvetica,sans-serif',overflow:'hidden'}}>
  {/* Vídeo principal original do Juarez e TODOS os dados/lip-sync do HyperFrames intactos */}
  <OffthreadVideo muted src={staticFile('juarez-original.mp4')} style={{height:'100%',width:'100%',objectFit:'cover'}}/>
  <Audio src={staticFile('voz-original.wav')}/>
  {/* As margens animadas usam Remotion sem cortar nenhum número da previsão */}
  <div style={{position:'absolute',left:0,top:0,width:11,height:1920,background:'#e94536',boxShadow:'3px 0 18px #ed453177'}} />
  <div style={{position:'absolute',right:0,top:0,width:11,height:1920,background:'#ffd452',boxShadow:'-3px 0 18px #ffc44766'}} />
  <div style={{position:'absolute',top:9,left:0,right:0,height:6,background:'#eff7ff66'}}>
    <div style={{height:'100%',width:barWidth+'%',background:'#f9cc46'}}/>
  </div>
  {/* Identificação obrigatória: os valores deste vídeo vêm do DEMO do próprio repositório */}
  <div style={{position:'absolute',right:28,top:24,display:demo?'block':'none',padding:'10px 17px',border:'3px solid #f5cf59',borderRadius:10,
   background:'rgba(9,26,42,.94)',color:'#ffdc67',fontSize:22,fontWeight:900,letterSpacing:2,zIndex:20}}>
   DEMONSTRAÇÃO • NÃO PUBLICAR
  </div>
  {/* Sinalizador de capítulos: estreito, no canto, sem interferir no telão e nas legendas */}
  <div style={{position:'absolute',left:35,top:265,width:13,height:110,background:'#ffc841',
   borderRadius:8,transform:`scaleY(${.88+.12*Math.sin(t*4)})`,boxShadow:'0 0 18px #ffd452aa'}}/>
  {/* Cartões Remotion: somente área à direita do Juarez, sob as legendas, acima da bancada. */}
  <div style={{position:'absolute',left:544,top:1102,width:500,height:208,zIndex:18,
   opacity:cardOpacity,transform:`translateX(${interpolate(clamp(enter,0,1),[0,1],[65,0])}px) scale(${.93+.07*clamp(enter,0,1)})`}}>
   <div style={{background:'rgba(11,30,48,.97)',border:'5px solid #0b1520',borderRadius:24,overflow:'hidden',
   height:'100%',boxShadow:'13px 13px 0 #10182755'}}>
    <div style={{height:35,background:color,color:'#162f42',fontSize:21,fontWeight:900,letterSpacing:2,
     padding:'5px 20px',display:'flex',justifyContent:'space-between',alignItems:'center'}}>
     <span>GIRO DA REGIÃO</span><span>{sequence%cityList.length+1}/{cityList.length}</span>
    </div>
    <div style={{padding:'12px 17px',display:'flex',alignItems:'center',gap:13}}>
      <SunCloud cond={active.cond}/>
      <div style={{minWidth:0,flex:1}}>
       <div style={{fontSize:29,fontWeight:900,color:'#ffffff',lineHeight:1.1,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{active.nome.toUpperCase()}</div>
       <div style={{fontSize:23,color:color,fontWeight:800,marginTop:7}}>{condition(active.cond)}</div>
      </div>
      <div style={{textAlign:'right',minWidth:118}}>
       <div style={{fontSize:43,fontWeight:950,color:'#fff',lineHeight:1}}>{active.max}°</div>
       <div style={{fontSize:25,color:'#b5d1e3',marginTop:8}}>mín {active.min}°</div>
      </div>
    </div>
   </div>
  </div>
  {/* Flash técnico mínimo nos cortes do roteiro, sem ocultar o apresentador */}
  <div style={{position:'absolute',left:12,right:12,top:11,height:14,background:'#fff',opacity:transition*.22,pointerEvents:'none'}}/>
  <div style={{position:'absolute',right:23,bottom:20,display:demo?'block':'none',fontSize:18,fontWeight:900,letterSpacing:1,
   color:'#ffe7a5',opacity:pulse*.9,textShadow:'1px 1px 6px #142a3f'}}>REMOTION • TESTE ISOLADO</div>
 </AbsoluteFill>;
};
