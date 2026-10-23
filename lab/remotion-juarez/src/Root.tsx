import React from 'react';
import {Composition} from 'remotion';
import {WeatherCast, type WeatherCastProps} from './WeatherCast';

const defaults: WeatherCastProps = {
 durationFrames: 750,
 data: '2026-09-08',
 cidades: [{nome:'Quatis',min:15,max:27,cond:'sol',chuva_mm:0}],
 batidas: [],
};
export const Root: React.FC = () =>
 <Composition id="BoletimSulFlu" component={WeatherCast}
  width={1080} height={1920} fps={30} durationInFrames={750}
  defaultProps={defaults}
  calculateMetadata={({props}) => ({durationInFrames:Math.max(30,Math.round(props.durationFrames))})}/>;
