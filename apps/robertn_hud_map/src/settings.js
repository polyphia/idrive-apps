'use strict';
// turnX/turnY: the turn panel's offset from the HUD's bottom-right corner (px); turnSize: its size (%)
const defaults={enabled:false,zoom:100,size:100,mapWidth:100,mapHeight:100,x:0,y:0,horizon:20,distance:135,opacity:85,cameras:true,turnX:0,turnY:0,turnSize:100,currentStreetVisible:true,streetVisible:true,streetX:0,streetY:0,streetSize:100,streetWidth:100,streetHeight:100};
const ranges={zoom:[50,200],size:[30,100],mapWidth:[50,200],mapHeight:[50,200],x:[-200,200],y:[-120,120],horizon:[20,110],distance:[80,180],opacity:[30,100],turnX:[-620,20],turnY:[-300,20],turnSize:[50,200],streetX:[-700,100],streetY:[-400,100],streetSize:[50,200],streetWidth:[25,200],streetHeight:[75,300]};
function validate(value){if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Invalid settings');const out=Object.assign({},defaults);for(const k of Object.keys(value)){if(!Object.prototype.hasOwnProperty.call(defaults,k))throw Error('Unknown setting');const v=value[k];if(typeof defaults[k]==='boolean'){if(typeof v!=='boolean')throw Error('Invalid toggle');}else if(!Number.isInteger(v)||v<ranges[k][0]||v>ranges[k][1])throw Error('Setting outside range');out[k]=v;}return out;}
function view(s){return [s.zoom/100,s.size/100,s.x,s.y];}
function map(s){return [(s.mapWidth===undefined?100:s.mapWidth)/100,(s.mapHeight===undefined?100:s.mapHeight)/100,s.horizon+40770/s.distance,0];}
function mapPoint(p,s){const m=map(s),dy=p[1]-m[2];return [400+(p[0]-400)*m[0],m[2]+Math.min(dy,0)*m[1]+Math.max(dy,0)];}
function camera(s){return [s.horizon,s.distance,40770];}
function worldVS(source){return 'uniform vec4 u_view;uniform vec4 u_map;\n'+source.replace('d=a_position.xy-u_pose.xy','d=(a_position.xy-u_pose.xy)*u_view.x').replace('gl_Position=vec4(x*1.75,(1.-u_camera.x/240.)*w-u_camera.z/240.,0.,w);','gl_Position=vec4(x*1.75,(1.-u_camera.x/240.)*w-u_camera.z/240.,0.,w);float anchor=(1.-u_map.z/240.)*w;gl_Position.x*=u_map.x;gl_Position.y=anchor+max(gl_Position.y-anchor,0.)*u_map.y+min(gl_Position.y-anchor,0.);gl_Position.xy=gl_Position.xy*u_view.y+vec2(u_view.z/400.,-u_view.w/240.)*w;');}
module.exports={defaults,ranges,validate,view,map,mapPoint,camera,worldVS};
