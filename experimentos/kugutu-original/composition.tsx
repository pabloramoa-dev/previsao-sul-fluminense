import React,{useEffect,useRef,useState,useMemo} from 'react';
import {AbsoluteFill,Audio,Composition,delayRender,continueRender,staticFile,useCurrentFrame,registerRoot} from 'remotion';
import {Kugutu} from '@kugutu/runtime-web';
type Linha={personagem:string;fala:string;ilustracao:string;ini:number;fim:number};
type Data={fps:number;values:number[];timeline:Linha[];duration:number};
const FPS=15;
const allTime=2420;
const photoLabels:Record<string,string>={
  "O HOMEM MISTERIOSO":"MISTÉRIO NO PRÉDIO","GRUPO AGITADO":"GRUPO DO CONDOMÍNIO",
  "MANEQUIM":"O HOMEM MISTERIOSO","REVELACAO":"UM MANEQUIM!",
  "BAZAR BENEFICENTE":"BAZAR SOLIDÁRIO","BRINQUEDOTECA":"DOAÇÕES",
};
const BG='#172437', BORDER='#e1be78';
const VFXCard:React.FC<{label:string;top:boolean;time:number}> = ({label,top,time})=>{
  const phase=Math.sin(time*0.5);
  const isPhone=/GRUPO|AUDIO|MENSAGEM|CELULAR|CONVITE|COMUNICADO/i.test(label);
  const isMannequin=/HOMEM|MANEQUIM|CHAPEU|SALA|ROUPA|NAMORAD/i.test(label);
  const bazar=/BAZAR|DOAC|SOLIDAR|BRINQUEDOTECA/i.test(label);
  return <div style={{position:'absolute',left:263,top:top?106:532,width:255,height:315,
      border:'2px solid #d5af70',background:'#23364a',borderRadius:14,overflow:'hidden',
      boxShadow:'0 12px 30px #0007'}}>
    <div style={{position:'absolute',inset:0,background:'radial-gradient(circle at 55% 35%,#45647d 0%,#213145 75%)',opacity:.75}}/>
    <svg viewBox="0 0 240 250" style={{position:'absolute',left:0,top:0,width:255,height:260,transform:"translateY("+phase*2+"px)"}}>
       {isPhone?<><rect x="65" y="14" width="112" height="225" rx="17" fill="#101720" stroke="#d9bb85" strokeWidth="6"/><rect x="78" y="35" width="85" height="174" rx="9" fill="#dce6de"/><rect x="88" y="62" width="72" height="35" rx="13" fill="#8ac9a8"/><polygon points="99,68 99,89 118,78" fill="#256e4e"/><path d="M100 119h55 M100 130h40 M100 144h52 M100 158h37" stroke="#6c878b" strokeWidth="5"/><circle cx="120" cy="222" r="6" fill="#d4ba82"/></>:
       isMannequin?<><path d="M109 48 Q116 25 124 48 M118 48V71" fill="none" stroke="#c7ab80" strokeWidth="10"/><circle cx="118" cy="60" r="20" fill="#d8c293"/><path d="M100 78H136L163 185H73Z" fill="#d7ac74"/><path d="M90 98L57 167 M144 98L174 166" stroke="#d7ac74" strokeWidth="14"/><path d="M100 185L92 232 M135 185L144 232" stroke="#d7ac74" strokeWidth="14"/><path d="M80 232H110 M128 232H160" stroke="#c6ac80" strokeWidth="7"/></>:
       bazar?<><rect x="44" y="95" width="153" height="108" rx="8" fill="#ecd2a5"/><path d="M44 94L54 50H187L197 94Z" fill="#e48583"/><path d="M75 50L66 94M113 50V94M151 50L165 94" stroke="#fff4e0" strokeWidth="11"/><rect x="70" y="119" width="54" height="56" fill="#9ed1bb"/><rect x="140" y="115" width="39" height="71" fill="#b6a2cc"/><path d="M80 150L102 135L118 150 M145 145L160 135L177 145" fill="none" stroke="#678" strokeWidth="5"/><path d="M66 207h115" stroke="#d8af6e" strokeWidth="6"/></>:
       <><path d="M10 220 L10 76 L105 26 L230 65 L230 220" stroke="#b6bba2" strokeWidth="3" fill="#314455"/>{[0,1,2,3,4].map(x=><rect key={x} x={32+x*39} y={86+(x%2)*25} width="18" height="33" fill="#eacb87"/>)}<path d="M24 220V180L210 178V220" stroke="#c6a882" strokeWidth="6"/></>}
    </svg>
    <div style={{position:'absolute',bottom:0,height:55,display:'flex',alignItems:'center',justifyContent:'center',width:'100%',background:'#132132',borderTop:'2px solid #cba769',padding:'0 8px',textAlign:'center',fontFamily:'Arial',fontSize:16,fontWeight:700,color:'#fff7d8'}}>
      {photoLabels[label]??label.replaceAll("_"," ").slice(0,27)}
    </div>
  </div>
};
const Character:React.FC<{kind:'nina'|'maria';data:Data;top:boolean}>=({kind,data,top})=>{
  const frame=useCurrentFrame(),ref=useRef<HTMLDivElement>(null);
  const playerRef=useRef<any>(null),last=useRef<number>(-1),prevIdx=useRef<number>(-1);
  const [ready,setReady]=useState(false);
  const [handle]=useState(()=>delayRender('Carregando ator Kugutu original '+kind));
  useEffect(()=>{
    let alive=true;
    fetch(staticFile(kind+'.charpack')).then(r=>r.json()).then(async pack=>{
      if(!alive||!ref.current)return;
      const actor=await Kugutu.load(pack,ref.current);
      if(!alive){actor.destroy();return;}
      actor.stop();playerRef.current=actor;setReady(true);continueRender(handle);
    }).catch(err=>{console.error('Erro Kugutu',kind,err);continueRender(handle);});
    return ()=>{alive=false;playerRef.current?.destroy();};
  },[]);
  useEffect(()=>{
    const actor=playerRef.current;
    if(!actor||!ready)return;
    const t=frame/FPS;
    let i=data.timeline.findIndex(x=>x.ini<=t&&t<x.fim);
    if(i<0)i=data.timeline.findLastIndex(x=>x.ini<=t);
    const line=i>=0?data.timeline[i]:null;
    const speaking=line?.personagem===kind&&t<line.fim;
    if(frame<last.current){last.current=-1;}
    actor.step((frame-last.current)*1000/FPS);
    last.current=frame;
    const strength=(data.values[frame]??0);
    actor.setMouthOpen(speaking ? Math.min(1,0.05+strength*.88):0);
    if(i!==prevIdx.current){
      prevIdx.current=i;
      actor.setEmotion(speaking?(i%4===0?'surprised':'happy'):(i%5===0?'surprised':'neutral'),speaking?0.50:0.18);
      if(speaking && i%4===0)actor.playGesture('nod');
      actor.lookAt({x:speaking?0.12:-0.18,y:i%3===0?-.08:0});
    }
  },[frame,ready]);
  return <div ref={ref} style={{position:'absolute',left:9,top:top?106:535,
      width:248,height:307,overflow:'hidden',filter:'drop-shadow(0 2px 2px #0003)'}}/>;
};
const Video:React.FC=()=>{
 const frame=useCurrentFrame();
 const [data,setData]=useState<Data|null>(null);
 const [handle]=useState(()=>delayRender('Carregando RMS original'));
 useEffect(()=>{fetch(staticFile('envelope.json')).then(r=>r.json()).then(d=>{setData(d);continueRender(handle);}).catch(e=>{console.error(e);continueRender(handle);});},[]);
 const t=frame/FPS;
 let i=data?.timeline.findIndex(x=>x.ini<=t&&t<x.fim)??0;
 if(i<0)i=data?.timeline.findLastIndex(x=>x.ini<=t)??0;
 const label=data?.timeline[Math.max(0,i)]?.ilustracao??'CENA';
 return <AbsoluteFill style={{background:'#0d1727',color:'#f5e8c9',fontFamily:'Arial,sans-serif'}}>
  <div style={{position:'absolute',inset:0,background:'linear-gradient(#10192c,#29405d)'}}/>
  {[0,1].map((idx)=><div key={idx} style={{position:'absolute',top:idx?510:52,left:4,right:4,height:423,background:BG,borderTop:'3px solid '+BORDER,borderBottom:'3px solid '+BORDER,borderRadius:5}}>
    <div style={{height:38,marginLeft:idx?4:55,fontSize:26,fontWeight:900,letterSpacing:1,textShadow:'1px 1px #000'}}>{idx?'DONA ZULEIDE':'NINA'}</div>
    <div style={{position:'absolute',left:3,top:59,width:252,height:303,background:idx?'linear-gradient(#46404b,#2b4d57)':'linear-gradient(#4a4052,#334c58)',borderRadius:8}}/>
  </div>)}
  {data&&<><Character kind="nina" data={data} top/><Character kind="maria" data={data} top={false}/><VFXCard label={label} top time={t}/><VFXCard label={label} top={false} time={t}/></>}
  <div style={{position:'absolute',bottom:0,left:0,right:0,height:68,display:'flex',flexDirection:'column',justifyContent:'center',alignItems:'center',gap:4,
     background:'#142233',borderTop:'2px solid '+BORDER,borderRadius:8}}>
    <div style={{fontSize:22,fontWeight:900,color:'#edd19b'}}>TÁ SABENDO, ZULEIDE?</div>
    <div style={{fontSize:12,color:'#abb9ce',letterSpacing:1}}>EP. 01  ·  O ÁUDIO NO GRUPO ERRADO  ·  KUGUTU</div>
  </div>
  <Audio src={staticFile('audio.mp3')}/>
 </AbsoluteFill>;
};
export const Root=()=> <Composition id="NinaZuleideKugutu" component={Video} fps={FPS} durationInFrames={allTime} width={540} height={960}/>;
registerRoot(Root);
