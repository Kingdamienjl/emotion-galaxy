#!/usr/bin/env python3
"""Build the Living Emotion Galaxy as a single self-contained HTML file.
Clean rebuild (v6): all lessons integrated, no patch layers.
Output: ~/workspace/galaxy_viz/galaxy.html
"""
import json
import re
import sys

sys.path.insert(0, '/home/hatch/workspace')
from galaxy_emotions_combined import GALAXY


def extract_emotions():
    out = []
    for ev in GALAXY:
        c = ev.coords
        out.append([
            ev.name,
            round(c.valence, 3), round(c.intensity, 3), round(c.turbulence, 3),
            round(c.luminosity, 3), round(c.temperature, 3), round(c.gravity, 3),
            "".join(ev.behavior.hikari_emoji) if ev.behavior.hikari_emoji else "",
            ev.visual.nebula_hue,
            ev.behavior.hikari_style, ev.behavior.athena_style,
        ])
    return out


EMOTIONS = extract_emotions()
print(f"Extracted {len(EMOTIONS)} emotions", file=sys.stderr)
EMO_JSON = json.dumps(EMOTIONS, separators=(',', ':'))

HTML = """<div id="gx-wrap" style="box-sizing:border-box;max-width:100%;position:relative">
<div style="font-size:18px;font-weight:700;margin-bottom:2px">Living Emotion Galaxy</div>
<div style="font-size:12px;opacity:.6;margin-bottom:8px">True 3D &middot; volumetric &middot; click an emotion or let it drift</div>
<canvas id="gx" style="width:100%;height:520px;border-radius:12px;display:block;background:#010103"></canvas>
<div style="display:flex;gap:8px;margin:10px 0;align-items:center;flex-wrap:wrap">
<input id="gxs" placeholder="Search 140 emotions..." style="flex:1;min-width:180px;padding:8px;border-radius:8px;border:1px solid var(--hatch-widget-border);background:var(--hatch-widget-surface);color:var(--hatch-widget-text);box-sizing:border-box">
<button id="gxstorm" title="Ion storm frustration" style="padding:8px 10px;border-radius:8px;border:1px solid var(--hatch-widget-accent);background:transparent;cursor:pointer;font-size:14px">&#9889;</button><button id="gxflare" title="Solar flare joy" style="padding:8px 10px;border-radius:8px;border:1px solid var(--hatch-widget-accent);background:transparent;cursor:pointer;font-size:14px">&#9728;&#65039;</button><button id="gxsn" title="Supernova delight" style="padding:8px 10px;border-radius:8px;border:1px solid var(--hatch-widget-accent);background:transparent;cursor:pointer;font-size:14px">&#128165;</button><button id="gxorbs" title="Toggle lightning orb glow" style="padding:8px 10px;border-radius:8px;border:1px solid var(--hatch-widget-border);background:transparent;color:var(--hatch-widget-text);cursor:pointer;font-size:11px;white-space:nowrap">Orbs: OFF</button><button id="gxdrift" style="padding:8px 14px;border-radius:8px;border:1px solid var(--hatch-widget-accent);background:transparent;color:var(--hatch-widget-accent);cursor:pointer;white-space:nowrap">Drift: ON</button>
</div>
<div id="gxcur" style="font-size:14px;margin-bottom:6px;min-height:22px;color:var(--hatch-widget-text)"></div>
<div id="gxlist" style="display:flex;gap:6px;overflow-x:auto;padding-bottom:6px;max-width:100%"></div>
<script>
(function(){"use strict";
var E=__EMO_JSON__;

/* ================= THEMES ================= */
function getTheme(name){
  var n=String(name||"").toLowerCase();
  if(/fire|flame|ember|inferno|pyre|volcan|blaze|burn/.test(n))return "fire";
  if(/frost|ice|glacier|crystal|winter|snow|frozen/.test(n))return "ice";
  if(/solar|sun|dawn|daybreak/.test(n))return "solar";
  if(/supernova/.test(n))return "supernova";
  if(/ion|electric|thunder|lightning|storm|tempest|static/.test(n))return "storm";
  if(/void|abyss|shadow|eclipse|dark|night/.test(n))return "void";
  if(/ocean|tide|wave|sea|rain|river|monsoon/.test(n))return "water";
  if(/molten|lava|magma/.test(n))return "magma";
  if(/aurora|rainbow|prism/.test(n))return "aurora";
  if(/nebula|cosmic|star|galaxy|quasar|nova/.test(n))return "nebula";
  return null;
}

/* ================= WEBGL ================= */
var canvas=document.getElementById('gx');
var gl=canvas.getContext('webgl',{antialias:true,alpha:false});
if(!gl){canvas.outerHTML='<div style="color:#888;padding:40px;text-align:center">WebGL not available</div>';return;}
var PR=Math.min(2.5,window.devicePixelRatio||1);
function resize(){
  var w=canvas.clientWidth||900,h=520;
  canvas.width=w*PR; canvas.height=h*PR;
  gl.viewport(0,0,canvas.width,canvas.height);
}
window.addEventListener('resize',resize);

var glErrors=[];
function sh(t,s,label){
  var h=gl.createShader(t);gl.shaderSource(h,s);gl.compileShader(h);
  if(!gl.getShaderParameter(h,gl.COMPILE_STATUS))glErrors.push(label+": "+gl.getShaderInfoLog(h));
  return h;
}
function prog(vs,fs,label){
  var p=gl.createProgram();
  gl.attachShader(p,sh(gl.VERTEX_SHADER,vs,label+" VS"));
  gl.attachShader(p,sh(gl.FRAGMENT_SHADER,fs,label+" FS"));
  gl.linkProgram(p);
  if(!gl.getProgramParameter(p,gl.LINK_STATUS))glErrors.push(label+" LINK: "+gl.getProgramInfoLog(p));
  return p;
}

/* Point sprite shader (the beautiful one) */
var VS_P=[
"attribute vec3 aPos;",
"attribute vec3 aCol;",
"attribute float aSize;",
"attribute float aSeed;",
"uniform mat4 uProj;",
"uniform mat4 uView;",
"uniform float uTime;",
"uniform float uPR;",
"varying vec3 vCol;",
"varying float vAlpha;",
"void main(){",
"  vCol=aCol;",
"  vec4 vp=uView*vec4(aPos,1.0);",
"  float tw=0.65+0.35*sin(uTime*(0.8+aSeed*2.5)+aSeed*40.0);",
"  vAlpha=tw;",
"  gl_PointSize=aSize*uPR*(280.0/max(1.0,-vp.z))*(0.7+0.3*tw);",
"  gl_PointSize=min(gl_PointSize,64.0*uPR);",
"  gl_Position=uProj*vp;",
"}"].join("\\n");
var FS_P=[
"precision highp float;",
"varying vec3 vCol;",
"varying float vAlpha;",
"void main(){",
"  vec2 uv=gl_PointCoord-0.5;",
"  float d=length(uv)*2.0;",
"  float core=smoothstep(0.35,0.0,d);",
"  float halo=smoothstep(1.0,0.15,d)*0.35;",
"  float a=(core+halo)*vAlpha;",
"  vec3 col=vCol*(0.75+core*0.6);",
"  col.b+=halo*0.12;",
"  if(a<0.004)discard;",
"  gl_FragColor=vec4(col*a,a);",
"}"].join("\\n");

/* Billboard shader (clouds, planets) */
var VS_B=[
"attribute vec3 aCenter;",
"attribute vec2 aCorner;",
"attribute vec3 aCol;",
"attribute float aRadius;",
"attribute float aAlpha;",
"attribute float aSeed;",
"uniform mat4 uProj;",
"uniform mat4 uView;",
"uniform float uTime;",
"varying vec2 vUv;",
"varying vec3 vCol;",
"varying float vAlpha;",
"varying float vSeed;",
"void main(){",
"  vUv=aCorner; vCol=aCol; vSeed=aSeed;",
"  float breathe=1.0+sin(uTime*0.4+aSeed*20.0)*0.08;",
"  vec4 vc=uView*vec4(aCenter,1.0);",
"  vc.xy+=aCorner*aRadius*breathe;",
"  vAlpha=aAlpha*(0.85+0.15*sin(uTime*0.6+aSeed*30.0));",
"  gl_Position=uProj*vc;",
"}"].join("\\n");
var FS_B=[
"precision highp float;",
"varying vec2 vUv;",
"varying vec3 vCol;",
"varying float vAlpha;",
"varying float vSeed;",
"void main(){",
"  float d=length(vUv);",
"  float n1=sin(vUv.x*7.0+vSeed*17.0)*sin(vUv.y*6.0-vSeed*13.0);",
"  float n2=sin(vUv.x*13.0-vSeed*29.0)*sin(vUv.y*11.0+vSeed*7.0);",
"  float n=n1*0.6+n2*0.4;",
"  float gaps=smoothstep(-0.25,0.45,n);",
"  float a=smoothstep(1.0,0.1,d)*(0.25+0.75*gaps)*vAlpha;",
"  vec3 col=vCol*(0.6+smoothstep(0.6,0.0,d)*0.8);",
"  if(a<0.003)discard;",
"  gl_FragColor=vec4(col*a,a);",
"}"].join("\\n");

/* Line shader (lightning cores, flare arcs) */
var VS_L=[
"attribute vec3 aPos;",
"attribute vec3 aCol;",
"uniform mat4 uProj;",
"uniform mat4 uView;",
"varying vec3 vCol;",
"void main(){vCol=aCol;gl_Position=uProj*uView*vec4(aPos,1.0);}"
].join("\\n");
var FS_L=[
"precision highp float;",
"varying vec3 vCol;",
"void main(){gl_FragColor=vec4(vCol,1.0);}"
].join("\\n");

var prP=prog(VS_P,FS_P,"points");
var prB=prog(VS_B,FS_B,"billboard");
var prL=prog(VS_L,FS_L,"lines");

/* Matrices */
function persp(fovy,asp,n,f){
  var t=1/Math.tan(fovy/2),o=new Float32Array(16);
  o[0]=t/asp;o[5]=t;o[10]=(f+n)/(n-f);o[11]=-1;o[14]=2*f*n/(n-f);return o;
}
function lookAt(e,c,u){
  var zx=e[0]-c[0],zy=e[1]-c[1],zz=e[2]-c[2];
  var l=Math.hypot(zx,zy,zz);zx/=l;zy/=l;zz/=l;
  var xx=u[1]*zz-u[2]*zy,xy=u[2]*zx-u[0]*zz,xz=u[0]*zy-u[1]*zx;
  l=Math.hypot(xx,xy,xz);xx/=l;xy/=l;xz/=l;
  var yx=zy*xz-zz*xy,yy=zz*xx-zx*xz,yz=zx*xy-zy*xx;
  return new Float32Array([xx,yx,zx,0,xy,yy,zy,0,xz,yz,zz,0,
    -(xx*e[0]+xy*e[1]+xz*e[2]),-(yx*e[0]+yy*e[1]+yz*e[2]),-(zx*e[0]+zy*e[1]+zz*e[2]),1]);
}
function bindProg(p,proj,view,time){
  gl.useProgram(p);
  gl.uniformMatrix4fv(gl.getUniformLocation(p,"uProj"),false,proj);
  gl.uniformMatrix4fv(gl.getUniformLocation(p,"uView"),false,view);
  if(time!==undefined)gl.uniform1f(gl.getUniformLocation(p,"uTime"),time);
  var locPR=gl.getUniformLocation(p,"uPR");
  if(locPR)gl.uniform1f(locPR,PR);
}
function attr(p,buf,name,sz){
  gl.bindBuffer(gl.ARRAY_BUFFER,buf);
  var l=gl.getAttribLocation(p,name);
  if(l>=0){gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,sz,gl.FLOAT,false,0,0);}
}

/* ================= STATE ================= */
var cur={v:-0.6,i:0.8,tb:0.7,l:0.5,tp:0.4,g:0.5,hue:"storm-teal",name:"ion storm frustration",theme:"storm"};
var lightningOrbs=false;
var tgt=JSON.parse(JSON.stringify(cur));
var drifting=true,driftTimer=null,flashA=0;
var gSpread=10;

var hueMap={"gold":[1,0.75,0.2],"white-gold":[1,0.94,0.78],"electric-blue":[0.2,0.51,1],"cyan":[0.2,0.9,1],"amber":[1,0.65,0.24],"lavender":[0.65,0.51,1],"silver-blue":[0.59,0.7,1],"honey-gold":[1,0.8,0.39],"deep-violet":[0.39,0.2,0.9],"ice-blue":[0.51,0.8,1],"forge-orange":[1,0.45,0.1],"storm-teal":[0.2,0.8,0.75],"blood-orange":[1,0.25,0.06],"void-black":[0.06,0.06,0.11],"rose-nebula":[1,0.39,0.61],"magma":[1,0.29,0.06],"crimson":[0.9,0.1,0.2],"dark-matter":[0.11,0.05,0.2],"slate":[0.39,0.45,0.55],"quasar-white":[0.95,0.97,1],"dusty-brown":[0.5,0.35,0.2],"midnight-blue":[0.1,0.15,0.45],"aurora-green":[0.29,1,0.61],"eclipse-grey":[0.35,0.35,0.4]};
function hueRGB(h){h=String(h||"lavender").toLowerCase();for(var k in hueMap){if(h.indexOf(k)>=0)return hueMap[k];}return hueMap["lavender"];}

/* ================= MAIN STAR SWARM ================= */
var NS=2970;
var sPos=new Float32Array(NS*3),sCol=new Float32Array(NS*3),sSize=new Float32Array(NS),sSeed=new Float32Array(NS);
var sBase=[];
for(var si=0;si<NS;si++){
  var sb={a:Math.random()*6.283,r:Math.pow(Math.random(),0.55),y:(Math.random()-0.5),
    sp:0.3+Math.random()*0.7,arm:Math.floor(Math.random()*5),sz:0.6+Math.random()*2.4,sd:Math.random()};
  sBase.push(sb);sSeed[si]=sb.sd;
}
var sBuf=gl.createBuffer(),sColBuf=gl.createBuffer(),sSizeBuf=gl.createBuffer(),sSeedBuf=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,sSeedBuf);gl.bufferData(gl.ARRAY_BUFFER,sSeed,gl.STATIC_DRAW);

function updateStars(time){
  var base=hueRGB(cur.hue);
  var spread=5+cur.i*9;gSpread=spread;
  var spinS=0.06+cur.i*0.4+cur.tb*0.3;
  var ySq=1-cur.g*0.6;
  var bright=0.35+cur.l*0.65;
  var arms=2+Math.floor(cur.tb*4);
  var breathe=1+Math.sin(time*1.1)*0.04*(1+cur.i);
  var th=cur.theme;
  for(var k=0;k<NS;k++){
    var b=sBase[k];
    b.a+=spinS*0.016*b.sp*(1.3-b.r*0.5);
    var armA=(b.arm%arms)/arms*Math.PI*2;
    var ang=armA+b.r*2.4+b.a*0.12+Math.sin(time*0.4+b.sd*6.28)*cur.tb*0.6;
    var rr=b.r*spread*breathe*(0.7+(cur.v*0.5+0.5)*0.6);
    var x=Math.cos(ang)*rr;
    var z=Math.sin(ang)*rr*0.8-4;
    var y=b.y*spread*0.3*ySq+Math.sin(time*0.7+b.sd*6.28)*cur.tb*1.8;
    if(th==="fire"||th==="magma")y+=Math.sin(time*2+b.sd*6.28)*1.2+(1-b.r)*3*cur.i;
    sPos[k*3]=x;sPos[k*3+1]=y;sPos[k*3+2]=z;
    var coreF=1-b.r;
    var cr=Math.min(1,base[0]*(0.3+coreF)*bright);
    var cg=Math.min(1,base[1]*(0.3+coreF)*bright);
    var cb=Math.min(1,base[2]*(0.3+coreF)*bright);
    if(cur.v<0){cr=Math.min(1,cr+(-cur.v)*0.25);cb=Math.min(1,cb+(-cur.v)*0.12);}
    if(th==="fire"||th==="magma"){
      var fm=0.75;
      cr=cr*(1-fm)+Math.min(1,0.6+coreF*0.9)*fm;
      cg=cg*(1-fm)+Math.min(1,0.25+coreF*0.35)*fm;
      cb=cb*(1-fm)+Math.min(1,coreF*0.12)*fm;
    }else if(th==="ice"){
      var im=0.7;
      cr=cr*(1-im)+Math.min(1,0.5+coreF*0.4)*im;
      cg=cg*(1-im)+Math.min(1,0.7+coreF*0.3)*im;
      cb=cb*(1-im)+1.0*im;
    }else if(th==="water"){
      var wm=0.6;
      cr=cr*(1-wm)+0.15*wm;cg=cg*(1-wm)+0.45*wm;cb=cb*(1-wm)+0.95*wm;
    }
    var hdr=1+coreF*cur.i*0.35;
    sCol[k*3]=cr*hdr;sCol[k*3+1]=cg*hdr;sCol[k*3+2]=cb*hdr;
    sSize[k]=b.sz*(0.7+coreF*0.6)*(0.8+cur.l*0.4);
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,sBuf);gl.bufferData(gl.ARRAY_BUFFER,sPos,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,sColBuf);gl.bufferData(gl.ARRAY_BUFFER,sCol,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,sSizeBuf);gl.bufferData(gl.ARRAY_BUFFER,sSize,gl.DYNAMIC_DRAW);
}
function drawPointsP(prog,time,proj,view,buf,colB,szB,sdB,count){
  bindProg(prog,proj,view,time);
  attr(prog,buf,"aPos",3);attr(prog,colB,"aCol",3);attr(prog,szB,"aSize",1);attr(prog,sdB,"aSeed",1);
  gl.drawArrays(gl.POINTS,0,count);
}

/* ================= ELEMENTAL LAYER ================= */
var NE=900;
var ePos=new Float32Array(NE*3),eCol=new Float32Array(NE*3),eSize=new Float32Array(NE),eSeed=new Float32Array(NE);
var eBase=[];
for(var ei=0;ei<NE;ei++){
  var eb={a:Math.random()*6.283,r:Math.random(),y:(Math.random()-0.5),sp:0.5+Math.random(),sd:Math.random(),sz:0.8+Math.random()*2.0};
  eBase.push(eb);eSeed[ei]=eb.sd;
}
var eBuf=gl.createBuffer(),eColBuf=gl.createBuffer(),eSizeBuf=gl.createBuffer(),eSeedBuf=gl.createBuffer();
/* ---- Snow: cold particle buildup for sadness ---- */
var NSW2=450;
var snPos=new Float32Array(NSW2*3),snCol=new Float32Array(NSW2*3),snSize=new Float32Array(NSW2),snSeed=new Float32Array(NSW2);
var snBase=[];
for(var sni=0;sni<NSW2;sni++){
  snBase.push({x:(Math.random()-0.5)*2,y:Math.random(),z:(Math.random()-0.5)*2,
    sp:0.3+Math.random()*0.7,ph:Math.random()*6.28,sd:Math.random(),sz:0.7+Math.random()*1.8});
  snSeed[sni]=snBase[sni].sd;
}
var snBuf=gl.createBuffer(),snColB=gl.createBuffer(),snSizeB=gl.createBuffer(),snSdB=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,snSdB);gl.bufferData(gl.ARRAY_BUFFER,snSeed,gl.STATIC_DRAW);
function updateSnow(time){
  var spread=gSpread;
  var snowA=Math.max(0,(-cur.v-0.1))*1.8;
  snowA=Math.min(1,snowA);
  for(var k=0;k<NSW2;k++){
    var b=snBase[k];
    if(snowA<0.02){snPos[k*3+1]=-100;snCol[k*3]=snCol[k*3+1]=snCol[k*3+2]=0;snSize[k]=0.01;continue;}
    // Slow fall with sway, swirl buildup near bottom
    b.y-=0.0035*b.sp*(0.4+snowA);
    if(b.y<-0.9){b.y=0.9;b.x=(Math.random()-0.5)*2;b.z=(Math.random()-0.5)*2;}
    var sway=Math.sin(time*1.2+b.ph)*0.15;
    // Gentle vortex accumulation
    var ang=Math.atan2(b.z,b.x)+0.002*(0.5+snowA);
    var rad=Math.hypot(b.x,b.z);
    rad=Math.max(0.15,rad-0.0008*snowA);
    var x=Math.cos(ang)*rad*spread*0.8+sway;
    var z=Math.sin(ang)*rad*spread*0.7-4;
    var y=b.y*spread*0.55;
    snPos[k*3]=x;snPos[k*3+1]=y;snPos[k*3+2]=z;
    var tw2=0.6+0.4*Math.sin(time*2+b.ph*3);
    snCol[k*3]=0.82*tw2*snowA;snCol[k*3+1]=0.88*tw2*snowA;snCol[k*3+2]=1.0*tw2*snowA;
    snSize[k]=b.sz;
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,snBuf);gl.bufferData(gl.ARRAY_BUFFER,snPos,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,snColB);gl.bufferData(gl.ARRAY_BUFFER,snCol,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,snSizeB);gl.bufferData(gl.ARRAY_BUFFER,snSize,gl.DYNAMIC_DRAW);
}
gl.bindBuffer(gl.ARRAY_BUFFER,eSeedBuf);gl.bufferData(gl.ARRAY_BUFFER,eSeed,gl.STATIC_DRAW);

function updateElements(time){
  var th=cur.theme,spread=gSpread;
  for(var k=0;k<NE;k++){
    var b=eBase[k],x=0,y=-100,z=0,cr=0,cg=0,cb=0;
    if(th==="fire"||th==="magma"){
      b.a+=0.045*b.sp*(1+cur.i*1.5);
      b.y+=0.008*b.sp*(0.5+cur.i);
      if(b.y>1)b.y=-1;
      var r=b.r*spread*0.45;
      x=Math.cos(b.a)*r+Math.sin(time*7+b.sd*30)*0.5*cur.i;
      z=Math.sin(b.a)*r*0.8-4+Math.cos(time*6+b.sd*25)*0.5*cur.i;
      y=b.y*spread*0.5;
      var heat=1-Math.abs(b.y);
      cr=1.0;cg=0.25+heat*0.45;cb=0.05+heat*0.1;
    }else if(th==="ice"){
      b.a+=0.004*b.sp;
      var r2=(0.3+b.r*0.7)*spread*0.8;
      x=Math.cos(b.a)*r2;z=Math.sin(b.a)*r2*0.8-4;
      y=b.y*spread*0.4+Math.sin(time*0.5+b.sd*6.28)*0.8;
      cr=0.6;cg=0.85;cb=1.0;
    }else if(th==="storm"){
      b.a+=0.02*b.sp*(0.5+cur.tb);
      var r3=b.r*spread*0.9;
      x=Math.cos(b.a)*r3+(Math.random()-0.5)*0.6;
      z=Math.sin(b.a)*r3*0.8-4+(Math.random()-0.5)*0.6;
      y=b.y*spread*0.4+(Math.random()-0.5)*0.6;
      var fl=0.6+0.4*Math.sin(time*20+b.sd*40);
      cr=0.7*fl;cg=0.85*fl;cb=1.0*fl;
    }else if(th==="solar"){
      b.r+=0.006*b.sp*(0.5+cur.i);
      if(b.r>1)b.r=0.1;
      var r4=b.r*spread*1.1;
      x=Math.cos(b.a)*r4;z=Math.sin(b.a)*r4*0.8-4;y=Math.sin(b.a*2)*r4*0.3;
      cr=1.0;cg=0.8;cb=0.4;
    }else if(th==="water"){
      b.a+=0.008*b.sp;
      var r5=(0.2+b.r*0.8)*spread;
      x=Math.cos(b.a)*r5;z=Math.sin(b.a)*r5*0.8-4;
      y=Math.sin(b.a*3+time*1.5)*spread*0.25;
      cr=0.2;cg=0.5;cb=1.0;
    }else if(th==="void"){
      b.r-=0.002*b.sp;
      if(b.r<0.05)b.r=1;
      var r6=b.r*spread;
      x=Math.cos(b.a)*r6;z=Math.sin(b.a)*r6*0.8-4;y=b.y*spread*0.3;
      cr=0.25;cg=0.2;cb=0.4;
    }else if(th){
      b.a+=0.01*b.sp;
      var r7=b.r*spread*0.7;
      x=Math.cos(b.a)*r7;z=Math.sin(b.a)*r7*0.8-4;
      y=Math.sin(time+b.sd*6.28)*spread*0.3;
      var hue2=(time*0.2+b.sd)%1;
      cr=Math.abs(Math.sin(hue2*6.28));cg=Math.abs(Math.sin(hue2*6.28+2));cb=Math.abs(Math.sin(hue2*6.28+4));
    }
    ePos[k*3]=x;ePos[k*3+1]=y;ePos[k*3+2]=z;
    var br2=(0.5+cur.l*0.7)*(0.7+0.6*Math.sin(time*3+b.sd*20));
    eCol[k*3]=cr*br2;eCol[k*3+1]=cg*br2;eCol[k*3+2]=cb*br2;
    eSize[k]=b.sz*(0.8+cur.i*0.5);
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,eBuf);gl.bufferData(gl.ARRAY_BUFFER,ePos,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,eColBuf);gl.bufferData(gl.ARRAY_BUFFER,eCol,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,eSizeBuf);gl.bufferData(gl.ARRAY_BUFFER,eSize,gl.DYNAMIC_DRAW);
}

/* ================= BACKGROUND DUST + MILKY WAY ================= */
var ND=3000;
var dPos=new Float32Array(ND*3),dCol=new Float32Array(ND*3),dSize=new Float32Array(ND),dSeed=new Float32Array(ND);
for(var di=0;di<ND;di++){
  var bb=0.35+Math.random()*0.55,tint=Math.random();
  if(di%3===0){
    var ba=Math.random()*6.283,brad=70+Math.random()*25;
    dPos[di*3]=Math.cos(ba)*brad;
    dPos[di*3+1]=(Math.random()-0.5)*12+Math.sin(ba)*20;
    dPos[di*3+2]=Math.sin(ba)*brad*0.7-20;
    bb*=1.3;
  }else{
    var th2=Math.random()*6.283,ph2=Math.acos(2*Math.random()-1),rr=60+Math.random()*40;
    dPos[di*3]=rr*Math.sin(ph2)*Math.cos(th2);
    dPos[di*3+1]=rr*Math.cos(ph2)*0.6;
    dPos[di*3+2]=rr*Math.sin(ph2)*Math.sin(th2)-20;
  }
  dCol[di*3]=bb*(0.8+tint*0.2);dCol[di*3+1]=bb*0.9;dCol[di*3+2]=bb*(1-tint*0.2);
  dSize[di]=0.8+Math.random()*1.6;dSeed[di]=Math.random();
}
/* ---- Smoke: lifelike wisps ---- */
var NSM=600;
var smPos=new Float32Array(NSM*3),smCol=new Float32Array(NSM*3),smSize=new Float32Array(NSM),smSeed=new Float32Array(NSM);
var smBase=[];
for(var smi=0;smi<NSM;smi++){
  smBase.push({a:Math.random()*6.283,r:0.2+Math.random()*0.8,y:Math.random(),
    sp:0.2+Math.random()*0.5,ph:Math.random()*6.28,sd:Math.random(),sz:3+Math.random()*5,life:Math.random()});
  smSeed[smi]=smBase[smi].sd;
}
var smBuf=gl.createBuffer(),smColB=gl.createBuffer(),smSizeB=gl.createBuffer(),smSdB=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,smSdB);gl.bufferData(gl.ARRAY_BUFFER,smSeed,gl.STATIC_DRAW);
function updateSmoke(time){
  var spread=gSpread;
  var smokeA=Math.max(0,(0.62-cur.l))*1.4+cur.tb*0.25;
  smokeA=Math.min(1,smokeA);
  for(var k=0;k<NSM;k++){
    var b=smBase[k];
    if(smokeA<0.03){smPos[k*3+1]=-100;smCol[k*3]=smCol[k*3+1]=smCol[k*3+2]=0;smSize[k]=0.01;continue;}
    // Rise + curl: lifelike wisp motion
    b.life+=0.004*b.sp*(0.5+cur.tb);
    if(b.life>1){b.life=0;b.a=Math.random()*6.283;b.r=0.2+Math.random()*0.6;}
    b.a+=0.006*(0.5+cur.tb);
    var r=b.r*spread*(0.5+b.life*0.7);
    var curl=Math.sin(time*0.8+b.ph+b.life*5)*0.8;
    var x=Math.cos(b.a)*r+curl;
    var z=Math.sin(b.a)*r*0.75-4+Math.cos(time*0.6+b.ph)*0.6;
    var y=(b.y-0.5)*spread*0.4+b.life*spread*0.35;
    smPos[k*3]=x;smPos[k*3+1]=y;smPos[k*3+2]=z;
    var fade=Math.sin(b.life*Math.PI);
    var g=0.32+0.1*Math.sin(time+b.ph);
    smCol[k*3]=g*0.9*smokeA*fade;smCol[k*3+1]=g*0.95*smokeA*fade;smCol[k*3+2]=g*1.1*smokeA*fade;
    smSize[k]=b.sz*(0.7+b.life*0.9);
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,smBuf);gl.bufferData(gl.ARRAY_BUFFER,smPos,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,smColB);gl.bufferData(gl.ARRAY_BUFFER,smCol,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,smSizeB);gl.bufferData(gl.ARRAY_BUFFER,smSize,gl.DYNAMIC_DRAW);
}
var dBuf=gl.createBuffer(),dColB=gl.createBuffer(),dSizeB=gl.createBuffer(),dSeedB=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,dBuf);gl.bufferData(gl.ARRAY_BUFFER,dPos,gl.STATIC_DRAW);
gl.bindBuffer(gl.ARRAY_BUFFER,dColB);gl.bufferData(gl.ARRAY_BUFFER,dCol,gl.STATIC_DRAW);
gl.bindBuffer(gl.ARRAY_BUFFER,dSizeB);gl.bufferData(gl.ARRAY_BUFFER,dSize,gl.STATIC_DRAW);
gl.bindBuffer(gl.ARRAY_BUFFER,dSeedB);gl.bufferData(gl.ARRAY_BUFFER,dSeed,gl.STATIC_DRAW);

/* ================= NEBULA CLOUDS ================= */
var NB=96;
var bCX=new Float32Array(NB*6*3),bCC=new Float32Array(NB*6*3),bRD=new Float32Array(NB*6),
    bAL=new Float32Array(NB*6),bCOR=new Float32Array(NB*6*2);
var bBase=[];
for(var bi=0;bi<NB;bi++){
  bBase.push({a:Math.random()*6.283,r:0.15+Math.random()*0.85,y:(Math.random()-0.5)*0.7,
    rad:6+Math.random()*14,al:0.10+Math.random()*0.14,sd:Math.random(),dp:(Math.random()-0.5)*14});
  for(var bc2=0;bc2<6;bc2++){
    var cn=[[-1,-1],[1,-1],[1,1],[-1,-1],[1,1],[-1,1]][bc2];
    bCOR[(bi*6+bc2)*2]=cn[0];bCOR[(bi*6+bc2)*2+1]=cn[1];
  }
}
var bCenBuf=gl.createBuffer(),bColBuf=gl.createBuffer(),bRadBuf=gl.createBuffer(),
    bAlpBuf=gl.createBuffer(),bCorBuf=gl.createBuffer(),bSdBuf=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,bCorBuf);gl.bufferData(gl.ARRAY_BUFFER,bCOR,gl.DYNAMIC_DRAW);
(function(){var a=new Float32Array(NB*6);for(var i=0;i<NB;i++)for(var j=0;j<6;j++)a[i*6+j]=bBase[i].sd;
gl.bindBuffer(gl.ARRAY_BUFFER,bSdBuf);gl.bufferData(gl.ARRAY_BUFFER,a,gl.STATIC_DRAW);})();

function updateBillboards(time){
  var base=hueRGB(cur.hue),spread=gSpread;
  var darkF=Math.max(0.45,cur.l);
  // Wind: gusting vector from turbulence
  var gust=0.6+0.4*Math.sin(time*0.7)+0.25*Math.sin(time*1.7);
  var windStr=cur.tb*4*gust;
  var windAng=time*0.15;
  var windX=Math.cos(windAng)*windStr, windZ=Math.sin(windAng)*windStr*0.6;
  for(var i=0;i<NB;i++){
    var b=bBase[i];
    if(b.drag===undefined)b.drag=0.4+Math.random()*0.8;
    b.a+=0.00013*(0.5+cur.tb);
    var ang=b.a+b.r*2.0;
    var rr=b.r*spread*0.9;
    // Ragdoll: wind shoves clouds, heavier drag = more displacement
    var x=Math.cos(ang)*rr+windX*b.drag;
    var z=Math.sin(ang)*rr*0.8-4+windZ*b.drag;
    var y=b.y*spread*0.4+b.dp*0.3+Math.sin(time*0.9+b.sd*9)*cur.tb*0.8;
    // Stretch along wind direction (elongate + slight squash)
    var stretch=1+Math.min(0.9,windStr*0.12*b.drag);
    var squash=1-Math.min(0.3,windStr*0.04*b.drag);
    var wcos=Math.cos(windAng),wsin=Math.sin(windAng);
    for(var c2=0;c2<6;c2++){
      var cx0=bCOR[(i*6+c2)*2],cy0=bCOR[(i*6+c2)*2+1];
      // rotate corner into wind frame, stretch, rotate back
      var rx=cx0*wcos+cy0*wsin, ry=-cx0*wsin+cy0*wcos;
      rx*=stretch; ry*=squash;
      bCOR[(i*6+c2)*2]=rx*wcos-ry*wsin;
      bCOR[(i*6+c2)*2+1]=rx*wsin+ry*wcos;
    }
    for(var j=0;j<6;j++){
      var vi=i*6+j;
      bCX[vi*3]=x;bCX[vi*3+1]=y;bCX[vi*3+2]=z;
      var depthF=1-Math.min(1,Math.abs(z+4)/20)*0.4;
      bCC[vi*3]=base[0]*darkF*depthF;bCC[vi*3+1]=base[1]*darkF*depthF;bCC[vi*3+2]=base[2]*darkF*depthF;
      bRD[vi]=b.rad*(0.8+cur.i*0.5);
      bAL[vi]=b.al*(1.6+cur.l*1.5);
    }
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,bCenBuf);gl.bufferData(gl.ARRAY_BUFFER,bCX,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,bColBuf);gl.bufferData(gl.ARRAY_BUFFER,bCC,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,bRadBuf);gl.bufferData(gl.ARRAY_BUFFER,bRD,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,bAlpBuf);gl.bufferData(gl.ARRAY_BUFFER,bAL,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,bCorBuf);gl.bufferData(gl.ARRAY_BUFFER,bCOR,gl.DYNAMIC_DRAW);
}
function drawBillboardsP(prog,time,proj,view){
  bindProg(prog,proj,view,time);
  attr(prog,bCenBuf,"aCenter",3);attr(prog,bCorBuf,"aCorner",2);attr(prog,bColBuf,"aCol",3);
  attr(prog,bRadBuf,"aRadius",1);attr(prog,bAlpBuf,"aAlpha",1);attr(prog,bSdBuf,"aSeed",1);
  gl.drawArrays(gl.TRIANGLES,0,NB*6);
}

/* ---- Foreground dust: large faint motes for depth ---- */
var NFG=400;
var fgPos=new Float32Array(NFG*3),fgCol=new Float32Array(NFG*3),fgSize=new Float32Array(NFG),fgSeed=new Float32Array(NFG);
var fgBase=[];
for(var fgi=0;fgi<NFG;fgi++){
  fgBase.push({a:Math.random()*6.283,r:0.3+Math.random()*0.9,y:(Math.random()-0.5),
    sp:0.1+Math.random()*0.3,sd:Math.random(),sz:2.5+Math.random()*5});
  fgSeed[fgi]=fgBase[fgi].sd;
}
var fgBuf=gl.createBuffer(),fgColB=gl.createBuffer(),fgSizeB=gl.createBuffer(),fgSdB=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,fgSdB);gl.bufferData(gl.ARRAY_BUFFER,fgSeed,gl.STATIC_DRAW);
function updateForeground(time){
  var spread=gSpread;
  for(var k=0;k<NFG;k++){
    var b=fgBase[k];
    b.a+=0.003*b.sp;
    // Close to camera: larger orbit radius, slow drift
    var r=(1.2+b.r)*spread*0.9;
    var x=Math.cos(b.a)*r, z=Math.sin(b.a)*r*0.7-2;
    var y=b.y*spread*0.5+Math.sin(time*0.3+b.sd*6.28)*1.5;
    fgPos[k*3]=x;fgPos[k*3+1]=y;fgPos[k*3+2]=z;
    var tw=0.25+0.2*Math.sin(time*0.8+b.sd*12);
    var base=hueRGB(cur.hue);
    fgCol[k*3]=base[0]*tw*0.5;fgCol[k*3+1]=base[1]*tw*0.5;fgCol[k*3+2]=base[2]*tw*0.6;
    fgSize[k]=b.sz;
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,fgBuf);gl.bufferData(gl.ARRAY_BUFFER,fgPos,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,fgColB);gl.bufferData(gl.ARRAY_BUFFER,fgCol,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,fgSizeB);gl.bufferData(gl.ARRAY_BUFFER,fgSize,gl.DYNAMIC_DRAW);
}
/* ================= PLANETS ================= */
var NPL=3;
var planets=[
  {a:0.5,r:0.55,y:2.5,size:1.8,col:[0.3,0.6,1.0],sp:0.05},
  {a:2.8,r:0.75,y:-3.0,size:2.6,col:[1.0,0.5,0.2],sp:0.03},
  {a:4.5,r:0.4,y:1.0,size:1.2,col:[0.5,1.0,0.7],sp:0.08}
];
var plCen=new Float32Array(NPL*6*3),plCol=new Float32Array(NPL*6*3),
    plRad=new Float32Array(NPL*6),plAlp=new Float32Array(NPL*6),
    plCor=new Float32Array(NPL*6*2),plSd=new Float32Array(NPL*6);
(function(){
  var cn=[[-1,-1],[1,-1],[1,1],[-1,-1],[1,1],[-1,1]];
  for(var pi=0;pi<NPL;pi++)for(var q=0;q<6;q++){
    plCor[(pi*6+q)*2]=cn[q][0];plCor[(pi*6+q)*2+1]=cn[q][1];plSd[pi*6+q]=Math.random();
  }
})();
var plCenBuf=gl.createBuffer(),plColBuf=gl.createBuffer(),plRadBuf=gl.createBuffer(),
    plAlpBuf=gl.createBuffer(),plCorBuf=gl.createBuffer(),plSdBuf=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,plCorBuf);gl.bufferData(gl.ARRAY_BUFFER,plCor,gl.STATIC_DRAW);
gl.bindBuffer(gl.ARRAY_BUFFER,plSdBuf);gl.bufferData(gl.ARRAY_BUFFER,plSd,gl.STATIC_DRAW);

function updatePlanets(){
  var spread=gSpread;
  for(var pi=0;pi<NPL;pi++){
    var p=planets[pi];
    p.a+=p.sp*0.016;
    var x=Math.cos(p.a)*spread*p.r*1.3,z=Math.sin(p.a)*spread*p.r*1.1-4,y=p.y;
    for(var q=0;q<6;q++){
      var vi=pi*6+q;
      plCen[vi*3]=x;plCen[vi*3+1]=y;plCen[vi*3+2]=z;
      plCol[vi*3]=p.col[0];plCol[vi*3+1]=p.col[1];plCol[vi*3+2]=p.col[2];
      plRad[vi]=p.size;plAlp[vi]=0.95;
    }
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,plCenBuf);gl.bufferData(gl.ARRAY_BUFFER,plCen,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,plColBuf);gl.bufferData(gl.ARRAY_BUFFER,plCol,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,plRadBuf);gl.bufferData(gl.ARRAY_BUFFER,plRad,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,plAlpBuf);gl.bufferData(gl.ARRAY_BUFFER,plAlp,gl.DYNAMIC_DRAW);
}

/* ================= LIGHTNING (fractal + HDR lines + glow) ================= */
var bolts=[];
var strikeCd=0;
var NLB=900;
var lbPos=new Float32Array(NLB*3),lbCol=new Float32Array(NLB*3),lbSize=new Float32Array(NLB),lbSeed=new Float32Array(NLB);
for(var lbi=0;lbi<NLB;lbi++)lbSeed[lbi]=Math.random();
var lbBuf=gl.createBuffer(),lbColBuf=gl.createBuffer(),lbSizeBuf=gl.createBuffer(),lbSeedBuf=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,lbSeedBuf);gl.bufferData(gl.ARRAY_BUFFER,lbSeed,gl.STATIC_DRAW);
var lnPosBuf=gl.createBuffer(),lnColBuf=gl.createBuffer();

function makeBolt3D(){
  var spread=gSpread;
  var ox=(Math.random()-0.5)*spread*1.4,
      oy=(Math.random()-0.5)*spread*0.7,
      oz=(Math.random()-0.5)*spread*1.2-4;
  var th=Math.random()*6.283,ph=Math.acos(2*Math.random()-1);
  var len=5+Math.random()*10;
  var p0=[ox,oy,oz];
  var p1=[ox+Math.sin(ph)*Math.cos(th)*len,oy+Math.cos(ph)*len*0.7,oz+Math.sin(ph)*Math.sin(th)*len];
  function subdiv(a,b,disp,dep){
    if(dep===0)return [a,b];
    var mid=[(a[0]+b[0])/2+(Math.random()-0.5)*disp,
             (a[1]+b[1])/2+(Math.random()-0.5)*disp,
             (a[2]+b[2])/2+(Math.random()-0.5)*disp];
    var l=subdiv(a,mid,disp*0.55,dep-1),r=subdiv(mid,b,disp*0.55,dep-1);
    return l.slice(0,-1).concat(r);
  }
  var pts=subdiv(p0,p1,2.5,5);
  var branches=[];
  var nBr=3+Math.floor(Math.random()*3);
  for(var bi=0;bi<nBr;bi++){
    var idx=4+Math.floor(Math.random()*Math.max(1,pts.length-8));
    var bp=pts[idx];
    var bth=Math.random()*6.283,bph=Math.acos(2*Math.random()-1),bl=1.5+Math.random()*3.5;
    var be=[bp[0]+Math.sin(bph)*Math.cos(bth)*bl,bp[1]+Math.cos(bph)*bl,bp[2]+Math.sin(bph)*Math.sin(bth)*bl];
    branches.push({pts:subdiv(bp,be,1.0,3),w:0.4+Math.random()*0.3});
  }
  return {pts:pts,branches:branches,life:1,trail:[],_gold:false};
}

function drawLightning(time,proj,view){
  var lp=[],lc=[],n=0;
  function addGlow(x,y,z,br,sz,gold){
    if(n>=NLB)return;
    lbPos[n*3]=x;lbPos[n*3+1]=y;lbPos[n*3+2]=z;
    if(gold){lbCol[n*3]=br;lbCol[n*3+1]=br*0.72;lbCol[n*3+2]=br*0.3;}
    else{lbCol[n*3]=br*0.5;lbCol[n*3+1]=br*0.7;lbCol[n*3+2]=br;}
    lbSize[n]=sz;n++;
  }
  for(var i=0;i<bolts.length;i++){
    var b=bolts[i];
    var fl=b.life>0.75?3.2:(b.life>0.3?1.4:b.life*2.5);
    for(var s=0;s<b.pts.length-1;s++){
      var p0=b.pts[s],p1=b.pts[s+1];
      for(var pass=0;pass<2;pass++){
        lp.push(p0[0],p0[1],p0[2],p1[0],p1[1],p1[2]);
        var core=fl*(pass===0?1.0:0.4);
        lc.push(core,core*0.97,core*0.92,core,core*0.97,core*0.92);
      }
      if(lightningOrbs&&s%3===0){
        addGlow((p0[0]+p1[0])/2,(p0[1]+p1[1])/2,(p0[2]+p1[2])/2,fl*0.35,6+Math.random()*5,b._gold);
      }
    }
    for(var bi=0;bi<b.branches.length;bi++){
      var br=b.branches[bi],bp=br.pts;
      for(var bs=0;bs<bp.length-1;bs++){
        lp.push(bp[bs][0],bp[bs][1],bp[bs][2],bp[bs+1][0],bp[bs+1][1],bp[bs+1][2]);
        var bc=fl*br.w;
        lc.push(bc*0.8,bc*0.85,bc,bc*0.8,bc*0.85,bc);
      }
    }
    if(lightningOrbs&&b.life>0.6){
      var op=b.pts[0];
      for(var g=0;g<6;g++){
        addGlow(op[0]+(Math.random()-0.5)*3,op[1]+(Math.random()-0.5)*3,op[2]+(Math.random()-0.5)*3,fl*0.5,8+Math.random()*8,false);
      }
    }
    for(var ti=0;ti<b.trail.length;ti++){
      var tr=b.trail[ti];
      for(var ts=0;ts<tr.pts.length;ts+=2){
        var tp=tr.pts[ts];
        addGlow(tp[0],tp[1],tp[2],tr.a*0.8,2.0,false);
      }
    }
  }
  /* Solar flare arcs as gold lines */
  for(var fi=0;fi<flares.length;fi++){
    var f=flares[fi],fp=f.pts;
    for(var fs2=0;fs2<fp.length-1;fs2++){
      lp.push(fp[fs2][0],fp[fs2][1],fp[fs2][2],fp[fs2+1][0],fp[fs2+1][1],fp[fs2+1][2]);
      var fb=f.life*2.2;
      lc.push(fb,fb*0.7,fb*0.3,fb,fb*0.7,fb*0.3);
    }
  }
  if(lp.length>0){
    gl.useProgram(prL);
    gl.uniformMatrix4fv(gl.getUniformLocation(prL,"uProj"),false,proj);
    gl.uniformMatrix4fv(gl.getUniformLocation(prL,"uView"),false,view);
    gl.bindBuffer(gl.ARRAY_BUFFER,lnPosBuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(lp),gl.DYNAMIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER,lnColBuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(lc),gl.DYNAMIC_DRAW);
    attr(prL,lnPosBuf,"aPos",3);attr(prL,lnColBuf,"aCol",3);
    gl.drawArrays(gl.LINES,0,lp.length/3);
  }
  for(var pk=n;pk<NLB;pk++){lbPos[pk*3+1]=-100;lbCol[pk*3]=lbCol[pk*3+1]=lbCol[pk*3+2]=0;lbSize[pk]=0.01;}
  gl.bindBuffer(gl.ARRAY_BUFFER,lbBuf);gl.bufferData(gl.ARRAY_BUFFER,lbPos,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,lbColBuf);gl.bufferData(gl.ARRAY_BUFFER,lbCol,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,lbSizeBuf);gl.bufferData(gl.ARRAY_BUFFER,lbSize,gl.DYNAMIC_DRAW);
  if(n>0)drawPointsP(prP,time,proj,view,lbBuf,lbColBuf,lbSizeBuf,lbSeedBuf,NLB);
}

/* ================= SOLAR FLARES ================= */
var flares=[];
function makeFlare(){
  var th=Math.random()*6.283,ph=Math.acos(2*Math.random()-1);
  var r0=1.5+Math.random()*1.5;
  var ox=Math.sin(ph)*Math.cos(th)*r0,oy=Math.cos(ph)*r0*0.6,oz=Math.sin(ph)*Math.sin(th)*r0-4;
  var len=4+Math.random()*7;
  var dx=Math.sin(ph)*Math.cos(th)*len,dy=Math.cos(ph)*len*0.8,dz=Math.sin(ph)*Math.sin(th)*len;
  var pts=[],segs=14;
  for(var s=0;s<=segs;s++){
    var t=s/segs,arch=Math.sin(t*Math.PI)*1.5;
    pts.push([ox+dx*t+(Math.random()-0.5)*1.2,oy+dy*t+arch,oz+dz*t+(Math.random()-0.5)*1.2]);
  }
  return {pts:pts,life:1};
}

/* ================= SUPERNOVA SHOCKWAVE (3D shell) ================= */
var snova={active:false,t:0};
var NSW=250;
var swPos=new Float32Array(NSW*3),swCol=new Float32Array(NSW*3),swSize=new Float32Array(NSW),swSeed=new Float32Array(NSW);
var swDir=[];
for(var swi=0;swi<NSW;swi++){
  var sth=Math.random()*6.283,sph=Math.acos(2*Math.random()-1);
  swDir.push([Math.sin(sph)*Math.cos(sth),Math.cos(sph),Math.sin(sph)*Math.sin(sth)]);
  swSeed[swi]=Math.random();
}
var swBuf=gl.createBuffer(),swColB=gl.createBuffer(),swSizeB=gl.createBuffer(),swSeedB=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,swSeedB);gl.bufferData(gl.ARRAY_BUFFER,swSeed,gl.STATIC_DRAW);
function updateShockwave(){
  if(!snova.active){
    for(var k=0;k<NSW;k++){swPos[k*3+1]=-100;swCol[k*3]=swCol[k*3+1]=swCol[k*3+2]=0;swSize[k]=0.01;}
  }else{
    var R=snova.t*22,fade=Math.max(0,1-snova.t/1.4);
    for(var k2=0;k2<NSW;k2++){
      var d=swDir[k2];
      swPos[k2*3]=d[0]*R;swPos[k2*3+1]=d[1]*R*0.7;swPos[k2*3+2]=d[2]*R-4;
      swCol[k2*3]=1.0*fade;swCol[k2*3+1]=0.92*fade;swCol[k2*3+2]=0.75*fade;
      swSize[k2]=(2+Math.random()*2)*fade+0.01;
    }
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,swBuf);gl.bufferData(gl.ARRAY_BUFFER,swPos,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,swColB);gl.bufferData(gl.ARRAY_BUFFER,swCol,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,swSizeB);gl.bufferData(gl.ARRAY_BUFFER,swSize,gl.DYNAMIC_DRAW);
}

/* ================= DIAGNOSTICS ================= */
var hud=document.createElement('div');
hud.style.cssText='position:absolute;top:8px;left:8px;font-size:13px;font-weight:bold;color:#0f0;background:rgba(0,0,0,0.6);padding:6px 8px;border-radius:6px;font-family:monospace;pointer-events:none;z-index:10;white-space:pre-line';
canvas.parentElement.appendChild(hud);
var errDiv=document.createElement('div');
errDiv.style.cssText='position:absolute;top:8px;right:8px;font-size:10px;color:#f66;background:rgba(0,0,0,0.7);padding:6px 8px;border-radius:6px;font-family:monospace;pointer-events:none;z-index:10;max-width:45%;display:none';
canvas.parentElement.appendChild(errDiv);
var _lActDbg=0;
function updateDiag(){
  var msg="[v8b] emo: "+cur.name+"\\n theme: "+(cur.theme||"none")+"\\n lAct: "+_lActDbg.toFixed(2)+"\\n bolts: "+bolts.length+"\\n flares: "+flares.length;
  if(glErrors.length)msg+="\\nGL ERRORS: "+glErrors.length;
  hud.textContent=msg;
  if(glErrors.length){errDiv.textContent=glErrors.join("\\n").substring(0,500);errDiv.style.display="block";}
}

/* ================= UI ================= */
function setEmotion(idx){
  var e=E[idx];
  tgt={v:e[1],i:e[2],tb:e[3],l:e[4],tp:e[5],g:e[6],hue:e[8],name:e[0],theme:getTheme(e[0])};
  var dims=["valence","intensity","turbulence","luminosity","temp","gravity"],bars="";
  for(var d=0;d<6;d++){
    var vv=Math.round(((e[d+1]+1)/2)*100);
    bars+='<div style="flex:1"><div style="height:5px;background:var(--hatch-widget-border);border-radius:3px"><div style="height:5px;border-radius:3px;width:'+vv+'%;background:var(--hatch-widget-accent)"></div></div><div style="font-size:9px;opacity:.5;margin-top:2px">'+dims[d]+'</div></div>';
  }
  document.getElementById('gxcur').innerHTML='<b style="font-size:16px">'+e[7]+' '+e[0]+'</b> <span style="opacity:.6;font-size:12px">'+e[8]+' nebula</span><div style="display:flex;gap:5px;margin:6px 0;max-width:420px">'+bars+'</div><div style="font-size:12px;opacity:.7">Hikari: '+e[9]+' &middot; Athena: '+e[10]+'</div>';
  if(driftTimer)clearTimeout(driftTimer);
  if(drifting)driftTimer=setTimeout(driftRandom,14000);
}
function driftRandom(){if(!drifting)return;setEmotion(Math.floor(Math.random()*E.length));}
function jumpToEmotion(name){
  for(var i=0;i<E.length;i++){if(E[i][0]===name){setEmotion(i);return;}}
  for(var j=0;j<E.length;j++){if(E[j][0].toLowerCase().indexOf(name.toLowerCase())>=0){setEmotion(j);return;}}
}
var list=document.getElementById('gxlist');
function buildChips(filter){
  list.innerHTML='';
  var f=String(filter||'').toLowerCase(),shown=0;
  for(var i=0;i<E.length;i++){
    var e=E[i];
    if(f&&e[0].toLowerCase().indexOf(f)<0)continue;
    if(shown>=50)break;shown++;
    (function(idx,em){
      var b=document.createElement('button');
      b.textContent=em[0];
      b.style.cssText='padding:6px 10px;border-radius:20px;border:1px solid var(--hatch-widget-border);background:var(--hatch-widget-surface);color:var(--hatch-widget-text);cursor:pointer;font-size:11px;white-space:nowrap;flex-shrink:0';
      b.onclick=function(){setEmotion(idx);};
      list.appendChild(b);
    })(i,e);
  }
}
document.getElementById('gxs').oninput=function(){buildChips(this.value);};
document.getElementById('gxstorm').onclick=function(){jumpToEmotion("ion storm frustration");};
document.getElementById('gxflare').onclick=function(){jumpToEmotion("solar flare joy");};
document.getElementById('gxsn').onclick=function(){jumpToEmotion("supernova delight");};
document.getElementById('gxorbs').onclick=function(){
  lightningOrbs=!lightningOrbs;
  this.textContent='Orbs: '+(lightningOrbs?'ON':'OFF');
};
document.getElementById('gxdrift').onclick=function(){
  drifting=!drifting;
  this.textContent='Drift: '+(drifting?'ON':'OFF');
  if(drifting)driftTimer=setTimeout(driftRandom,3000);
  else if(driftTimer)clearTimeout(driftTimer);
};

/* ================= MAIN LOOP ================= */
var camR=26,camA=0.6,camH=7;
var startT=performance.now();
function loop(){
  requestAnimationFrame(loop);
  var time=(performance.now()-startT)/1000;
  var keys=["v","i","tb","l","tp","g"],kk;
  for(var qi=0;qi<keys.length;qi++){kk=keys[qi];cur[kk]+=(tgt[kk]-cur[kk])*0.04;}
  if(Math.abs(cur.v-tgt.v)<0.04&&Math.abs(cur.i-tgt.i)<0.04){cur.hue=tgt.hue;cur.theme=tgt.theme;}
  flashA*=0.85;
  camA+=0.0006*(0.5+cur.tb);

  var w=canvas.width,h=canvas.height;
  var proj=persp(55*Math.PI/180,w/h,0.5,200);
  var ex=Math.cos(camA)*camR,ez=Math.sin(camA)*camR;
  var view=lookAt([ex,camH,ez],[0,-1,0],[0,1,0]);

  gl.clearColor(0.004,0.004,0.012,1);
  gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA,gl.ONE);
  gl.disable(gl.DEPTH_TEST);

  updateStars(time);
  updateElements(time);
  updateBillboards(time);
  updatePlanets();
  updateShockwave();

  /* Core glow (dimmed to 10%) */
  var cc=hueRGB(cur.hue);
  /* (core drawn via billboard glow below) */

  drawPointsP(prP,time,proj,view,dBuf,dColB,dSizeB,dSeedB,ND);
  drawBillboardsP(prB,time,proj,view);
  drawCoreGlow(prB,time,proj,view);
  /* planets via billboard prog */
  (function(){
    bindProg(prB,proj,view,time);
    attr(prB,plCenBuf,"aCenter",3);attr(prB,plCorBuf,"aCorner",2);attr(prB,plColBuf,"aCol",3);
    attr(prB,plRadBuf,"aRadius",1);attr(prB,plAlpBuf,"aAlpha",1);attr(prB,plSdBuf,"aSeed",1);
    gl.drawArrays(gl.TRIANGLES,0,NPL*6);
  })();
  drawPointsP(prP,time,proj,view,sBuf,sColBuf,sSizeBuf,sSeedBuf,NS);
  if(cur.theme&&cur.theme!=="nebula")drawPointsP(prP,time,proj,view,eBuf,eColBuf,eSizeBuf,eSeedBuf,NE);
  updateSnow(time);
  updateSmoke(time);
  updateForeground(time);
  drawPointsP(prP,time,proj,view,fgBuf,fgColB,fgSizeB,fgSdB,NFG);
  drawPointsP(prP,time,proj,view,smBuf,smColB,smSizeB,smSdB,NSM);
  drawPointsP(prP,time,proj,view,snBuf,snColB,snSizeB,snSdB,NSW2);
  drawPointsP(prP,time,proj,view,swBuf,swColB,swSizeB,swSeedB,NSW);

  /* Lightning lifecycle */
  var lAct=Math.max(0,cur.tb-0.18)*3.2;
  if(cur.name&&cur.name.indexOf("ion storm")>=0)lAct=Math.max(lAct,1.6);
  if(cur.name&&cur.name.indexOf("thunderhead")>=0)lAct=Math.max(lAct,1.3);
  if(cur.name&&cur.name.indexOf("solar fury")>=0)lAct=Math.max(lAct,1.1);
  if(cur.name&&cur.name.indexOf("electric")>=0)lAct=Math.max(lAct,0.9);
  if(cur.name&&cur.name.indexOf("storm")>=0)lAct=Math.max(lAct,0.8);
  for(var bi3=bolts.length-1;bi3>=0;bi3--){
    var _b=bolts[bi3];
    if(_b.life>0.4&&Math.random()<0.5){
      _b.trail.push({pts:_b.pts.map(function(p){return [p[0],p[1],p[2]];}),a:_b.life*0.35});
      if(_b.trail.length>6)_b.trail.shift();
    }
    for(var _ti=_b.trail.length-1;_ti>=0;_ti--){_b.trail[_ti].a-=0.03;if(_b.trail[_ti].a<=0)_b.trail.splice(_ti,1);}
    _b.life-=0.035;
    // Restrike: 25% chance the channel re-fires like real lightning
    if(_b.life<0.45&&!_b.restruck&&Math.random()<0.25){_b.life=0.85;_b.restruck=true;}
    if(_b.life<=0&&_b.trail.length===0)bolts.splice(bi3,1);
  }
  strikeCd=Math.max(0,strikeCd-0.016);
  if(strikeCd<=0&&Math.random()<lAct*0.5&&bolts.length<10){
    bolts.push(makeBolt3D());
    strikeCd=0.4+Math.random()*1.2;
    flashA=Math.min(0.3,lAct*0.18);
  }
  _lActDbg=lAct;
  drawLightning(time,proj,view);

  /* Solar flares */
  var _nm=cur.name||"";
  if(_nm.indexOf("solar flare")>=0&&Math.random()<0.22&&flares.length<8)flares.push(makeFlare());
  for(var _fi=flares.length-1;_fi>=0;_fi--){flares[_fi].life-=0.025;if(flares[_fi].life<=0)flares.splice(_fi,1);}

  /* Supernova */
  if(_nm.indexOf("supernova")>=0&&!snova.active&&Math.random()<0.01)snova={active:true,t:0};
  if(snova.active){
    snova.t+=0.025;
    if(snova.t>1.4)snova.active=false;
    else flashA=Math.max(flashA,Math.max(0,0.55-snova.t*0.55));
  }

  /* Thunder flash (screen-space warm glow, no shake) */
  if(flashA>0.01){
    gl.enable(gl.SCISSOR_TEST);
    gl.disable(gl.SCISSOR_TEST);
  }

  if((window._frameNo=(window._frameNo||0)+1)%30===0)updateDiag();
}

/* Core glow billboard (10% brightness) */
var coreCenB=gl.createBuffer(),coreColB=gl.createBuffer(),coreRadB=gl.createBuffer(),
    coreAlpB=gl.createBuffer(),coreCorB=gl.createBuffer(),coreSdB=gl.createBuffer();
(function(){
  gl.bindBuffer(gl.ARRAY_BUFFER,coreCenB);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([0,-1,-4, 0,-1,-4, 0,-1,-4, 0,-1,-4, 0,-1,-4, 0,-1,-4]),gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,coreCorB);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1, 1,-1, 1,1, -1,-1, 1,1, -1,1]),gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,coreRadB);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([8,8,8,8,8,8]),gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,coreAlpB);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([0.10,0.10,0.10,0.10,0.10,0.10]),gl.STATIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,coreSdB);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([0.5,0.5,0.5,0.5,0.5,0.5]),gl.STATIC_DRAW);
})();
function drawCoreGlow(prog,time,proj,view){
  var cc=hueRGB(cur.hue);
  var pulse=0.85+0.15*Math.sin(time*2);
  var cr=Math.min(1,cc[0]*(0.3+cur.l*0.5)*pulse),cg=Math.min(1,cc[1]*(0.3+cur.l*0.5)*pulse),cb=Math.min(1,cc[2]*(0.3+cur.l*0.5)*pulse);
  gl.bindBuffer(gl.ARRAY_BUFFER,coreColB);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([cr,cg,cb, cr,cg,cb, cr,cg,cb, cr,cg,cb, cr,cg,cb, cr,cg,cb]),gl.DYNAMIC_DRAW);
  bindProg(prog,proj,view,time);
  attr(prog,coreCenB,"aCenter",3);attr(prog,coreCorB,"aCorner",2);attr(prog,coreColB,"aCol",3);
  attr(prog,coreRadB,"aRadius",1);attr(prog,coreAlpB,"aAlpha",1);attr(prog,coreSdB,"aSeed",1);
  gl.drawArrays(gl.TRIANGLES,0,6);
}

buildChips('');
resize();
for(var sei=0;sei<E.length;sei++){if(E[sei][0]==="ion storm frustration"){setEmotion(sei);break;}}
if(driftTimer)clearTimeout(driftTimer);
driftTimer=setTimeout(driftRandom,8000);
updateDiag();
loop();
})();
</script></div>"""

html_out = HTML.replace("__EMO_JSON__", EMO_JSON)

with open('/home/hatch/workspace/galaxy_viz/galaxy.html', 'w') as f:
    f.write(html_out)
print(f"Built galaxy.html: {len(html_out)} bytes", file=sys.stderr)
