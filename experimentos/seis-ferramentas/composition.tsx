import React from 'react';
import {AbsoluteFill, Audio, Composition, OffthreadVideo, Sequence, staticFile, useCurrentFrame, interpolate, registerRoot} from 'remotion';
import {AnimatedText} from '../../third_party/remotion-bits/src/components/AnimatedText';
import {ColorGrade} from '../../third_party/react-video-toolkit/src/effects/ColorGrade';
import {Vignette} from '../../third_party/react-video-toolkit/src/effects/Vignette';
import {FilmGrain} from '../../third_party/react-video-toolkit/src/effects/FilmGrain';
import {ParallaxContainer, ParallaxLayer} from '../../third_party/react-video-toolkit/src/effects/Parallax';
const fps=15, duration=Math.ceil(161.14*fps);
const bangers=[
  {sec:0, text:'O HOMEM MISTERIOSO!',color:'#FFE3A1'},
  {sec:15,text:'FOFOCA NO GRUPO ERRADO!',color:'#FFB6CA'},
  {sec:67,text:'UM MANEQUIM?!',color:'#FFDE86'},
  {sec:117,text:'QUASE PEDIU LICENÇA!',color:'#FFB6CA'},
  {sec:148,text:'ELE ESTÁ SOLTEIRO?!',color:'#FFE3A1'},
];
const Video=()=> {
  const frame=useCurrentFrame();
  return <AbsoluteFill style={{backgroundColor:'#0b1220',overflow:'hidden'}}>
    <ColorGrade preset="warm" intensity={0.24}>
      <ParallaxContainer>
        <ParallaxLayer depth={0.2} amplitude={4}>
          <AbsoluteFill style={{transform:'scale(1.019)'}}>
            <OffthreadVideo src={staticFile('base.mp4')} muted style={{width:'100%',height:'100%',objectFit:'cover'}}/>
          </AbsoluteFill>
        </ParallaxLayer>
      </ParallaxContainer>
      <FilmGrain intensity={0.016} speed={0.15} size={25}/>
      <Vignette intensity={0.18} size={0.21}/>
    </ColorGrade>
    <Audio src={staticFile('base.mp4')} volume={1}/>
    {bangers.map((x,i)=>{
      const start=Math.round(x.sec*fps);
      return <Sequence from={start} durationInFrames={Math.round(1.8*fps)} key={i}>
        <AbsoluteFill style={{alignItems:'center',justifyContent:'center',pointerEvents:'none'}}>
          <div style={{position:'absolute',top:'49%',left:0,right:0,textAlign:'center',
              fontFamily:'Arial Black, sans-serif',fontWeight:900,fontSize:39,
              color:x.color,textShadow:'2px 3px 2px #0b1220, -2px -2px 2px #0b1220',
              letterSpacing:'0.2px',lineHeight:1.08}}>
            <AnimatedText transition={{duration:Math.round(0.55*fps),opacity:[0,1],y:[18,0],scale:[0.88,1]}}>{x.text}</AnimatedText>
          </div>
        </AbsoluteFill>
      </Sequence>
    })}
    <div style={{position:'absolute',bottom:0,left:0,height:3,width:(frame/duration*100)+'%',background:'#e9c77b'}}/>
  </AbsoluteFill>;
};
export const Root=()=> <Composition id="NinaZuleideSeisFerramentas" component={Video} fps={fps} durationInFrames={duration} width={540} height={960}/>;
registerRoot(Root);
