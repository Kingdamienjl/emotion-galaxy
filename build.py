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
<button id="gxstorm" title="Ion storm frustration" style="padding:8px 10px;border-radius:8px;border:1px solid var(--hatch-widget-accent);background:transparent;cursor:pointer;font-size:14px">&#9889;</button><button id="gxflare" title="Solar flare joy" style="padding:8px 10px;border-radius:8px;border:1px solid var(--hatch-widget-accent);background:transparent;cursor:pointer;font-size:14px">&#9728;&#65039;</button><button id="gxsn" title="Supernova delight" style="padding:8px 10px;border-radius:8px;border:1px solid var(--hatch-widget-accent);background:transparent;cursor:pointer;font-size:14px">&#128165;</button><div id="gxtoggles" style="display:flex;gap:4px;flex-wrap:wrap;margin:4px 0"></div><button id="gxorbs" title="Toggle lightning orb glow" style="padding:8px 10px;border-radius:8px;border:1px solid var(--hatch-widget-border);background:transparent;color:var(--hatch-widget-text);cursor:pointer;font-size:11px;white-space:nowrap">Orbs: OFF</button><button id="gxdrift" style="padding:8px 14px;border-radius:8px;border:1px solid var(--hatch-widget-accent);background:transparent;color:var(--hatch-widget-accent);cursor:pointer;white-space:nowrap">Drift: ON</button>
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

/* ============ ELEMENTAL MAPPING: elements attach to feelings ============ */
var EL={fire:0,lightning:0,wind:0,smoke:0,sun:0,sparkle:0,snow:0,flare:0,supernova:0};
function computeElementTargets(){
  var n=String(cur.name||"").toLowerCase(),t={};
  var angerFull=/anger|rage|fury|wrath|outrage/.test(n);
  var angerMild=/irritat|annoy|frustrat|resent|bitter|hostil|livid/.test(n);
  t.fire=angerFull?0.5+cur.i*0.5:(angerMild?0.25+cur.i*0.35:Math.max(0,-cur.v-0.5)*cur.i*0.8);
  var elec=/electric|ion|thunder|lightning|storm|tempest|shock|static|surge/.test(n);
  t.lightning=elec?0.4+cur.tb*0.6:Math.max(0,cur.tb-0.62)*2.5;
  var calm=/tranquil|calm|serene|peace|still|gentle|mellow|relax|hush|lull/.test(n);
  t.wind=calm?0.4+(1-cur.tb)*0.4:Math.max(0,0.35-cur.tb)*(cur.v>0?0.4:0.15);
  t.smoke=Math.max(0,0.6-cur.l)*1.3;
  t.sun=Math.max(0,cur.v-0.35)*Math.max(0,cur.tp-0.35)*3.0;
  t.sparkle=Math.max(0,cur.v-0.45)*Math.max(0,cur.l-0.55)*3.5;
  t.snow=Math.max(0,-cur.v-0.12)*1.6;
  t.flare=/solar|sun/.test(n)?0.5+cur.i*0.5:0;
  t.supernova=/supernova/.test(n)?1:0;
  for(var k in t)t[k]=Math.max(0,Math.min(1,t[k]));
  return t;
}
function updateElements2(){
  var tgt2=computeElementTargets();
  for(var k in EL)EL[k]+=(tgt2[k]-EL[k])*0.03;
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
/* Planet shader - procedural spheres with detail, terminator, rings */
var VS_PL=[
"attribute vec3 aCenter;",
"attribute vec2 aCorner;",
"attribute float aRadius;",
"attribute float aType;",
"attribute float aSeed;",
"uniform mat4 uProj;",
"uniform mat4 uView;",
"varying vec2 vP;",
"varying float vType;",
"varying float vSeed;",
"uniform float uTime;",
"void main(){",
"  vP=aCorner; vType=aType; vSeed=aSeed;",
"  vec4 vc=uView*vec4(aCenter,1.0);",
"  vc.xy+=aCorner*aRadius*2.2;",
"  gl_Position=uProj*vc;",
"}"
].join("\\n");
var FS_PL=[
"precision highp float;",
"varying vec2 vP;",
"varying float vType;",
"varying float vSeed;",
"uniform float uTime;",
"float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }",
"float vnoise(vec2 p){",
"  vec2 i=floor(p), f=fract(p);",
"  vec2 u=f*f*(3.0-2.0*f);",
"  return mix(mix(hash(i),hash(i+vec2(1,0)),u.x), mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),u.x), u.y);",
"}",
"float fbm(vec2 p){",
"  float v=0.0, a=0.5;",
"  for(int i=0;i<4;i++){ v+=a*vnoise(p); p*=2.03; a*=0.5; }",
"  return v;",
"}",
"void main(){",
"  vec2 p=vP*2.2;",
"  float r=length(p);",
"  vec3 L=normalize(vec3(0.55,0.45,0.72));",
"  float s=vSeed;",
"  vec2 sp=p*3.0+s*17.0;",
"  float continents=fbm(sp+fbm(sp*1.7+s*5.0));",
"  float detail=fbm(sp*3.1+s*29.0);",
"  float micro=vnoise(sp*9.0+s*43.0);",
"  vec3 base; vec3 atmo; float spec=0.0;",
"  if(vType<0.5){",
"    float b1=sin(p.y*10.0+s*12.0+uTime*0.06+fbm(sp*0.8)*3.0);",
"    float b2=sin(p.y*22.0-s*8.0+detail*2.0);",
"    base=mix(vec3(0.62,0.36,0.18),vec3(1.0,0.88,0.68),smoothstep(-0.7,0.7,b1));",
"    base=mix(base,vec3(0.85,0.55,0.30),smoothstep(0.1,0.9,b2)*0.5);",
"    float storm=smoothstep(0.72,0.95,fbm(sp*1.2+vec2(3.0,7.0)+uTime*0.03));",
"    base=mix(base,vec3(0.95,0.75,0.55),storm*0.7);",
"    base*=0.85+0.3*detail;",
"    atmo=vec3(0.9,0.7,0.5);",
"  } else if(vType<1.5){",
"    float land=smoothstep(0.42,0.58,continents);",
"    base=mix(vec3(0.30,0.18,0.12),vec3(0.72,0.42,0.22),land);",
"    base=mix(base,vec3(0.55,0.35,0.18),smoothstep(0.3,0.7,detail)*0.6);",
"    float cr=smoothstep(0.78,0.95,vnoise(sp*14.0+s*51.0));",
"    base*=1.0-cr*0.4;",
"    base+=vec3(0.05,0.03,0.02)*micro;",
"    float cap=smoothstep(0.55,0.8,p.y+s*0.15)+smoothstep(0.55,0.8,-p.y-s*0.15);",
"    base=mix(base,vec3(0.92,0.90,0.86),clamp(cap,0.0,1.0)*0.85);",
"    atmo=vec3(0.75,0.45,0.28);",
"  } else if(vType<2.5){",
"    float cracks=smoothstep(0.68,0.92,abs(continents-0.5)*2.0);",
"    base=mix(vec3(0.72,0.82,0.92),vec3(0.50,0.64,0.82),smoothstep(0.3,0.7,detail));",
"    base=mix(base,vec3(0.30,0.45,0.65),cracks*0.7);",
"    base+=vec3(0.08,0.10,0.12)*micro;",
"    spec=0.6;",
"    atmo=vec3(0.55,0.72,0.95);",
"  } else if(vType<3.5){",
"    float crust=smoothstep(0.35,0.65,continents);",
"    base=mix(vec3(0.10,0.06,0.06),vec3(0.28,0.14,0.08),crust);",
"    float lava=smoothstep(0.55,0.75,abs(detail-0.5)*2.2);",
"    base=mix(base,vec3(1.3,0.45,0.06),lava);",
"    base+=vec3(1.2,0.5,0.1)*smoothstep(0.75,0.95,lava)*1.2;",
"    base*=0.9+0.2*micro;",
"    atmo=vec3(1.0,0.35,0.08);",
"  } else {",
"    float b1=sin(p.y*8.0+s*10.0+fbm(sp*0.7)*2.5);",
"    base=mix(vec3(0.78,0.68,0.48),vec3(0.94,0.86,0.70),smoothstep(-0.6,0.6,b1));",
"    float b2=sin(p.y*18.0-s*6.0+detail*1.5);",
"    base=mix(base,vec3(0.66,0.56,0.38),smoothstep(0.2,0.9,b2)*0.45);",
"    base*=0.88+0.24*detail;",
"    atmo=vec3(0.9,0.8,0.6);",
"  }",
"  vec3 col; float alpha=1.0; bool isRing=false; vec3 ringCol=vec3(0.0); float ringA=0.0;",
"  if(vType>3.5){",
"    vec2 rp=vec2(p.x,p.y*3.4);",
"    float rr=length(rp);",
"    float inRing=step(1.08,rr)*step(rr,2.0);",
"    float ringBands=0.55+0.45*vnoise(vec2(rr*22.0,s*10.0));",
"    float cassini=smoothstep(0.03,0.09,abs(rr-1.55));",
"    ringCol=vec3(0.88,0.80,0.64)*ringBands*(0.35+0.65*cassini);",
"    float front=p.y<0.12?1.0:0.0;",
"    if(r>1.0){ ringA=inRing*0.92; isRing=true; }",
"    else if(inRing>0.5&&front>0.5){ ringA=0.88; isRing=true; }",
"  }",
"  if(isRing){",
"    float rdiff=max(dot(vec3(0.0,0.0,1.0),L),0.0);",
"    col=ringCol*(0.30+0.70*rdiff);",
"    alpha=ringA;",
"  } else {",
"    if(r>1.0) discard;",
"    vec3 n=vec3(p.x,p.y,sqrt(max(0.0,1.0-r*r)));",
"    float dl=max(dot(n,L),0.0);",
"    float term=smoothstep(-0.12,0.28,dl);",
"    col=base*(0.02+0.98*pow(term,1.3));",
"    vec3 V=vec3(0.0,0.0,1.0);",
"    vec3 H=normalize(L+V);",
"    col+=vec3(1.0,0.98,0.95)*pow(max(dot(n,H),0.0),24.0)*spec*term;",
"    float rim=pow(1.0-r,2.8);",
"    col+=atmo*rim*(0.15+0.55*term);",
"    float limb=pow(1.0-r,0.7);",
"    col=mix(col, atmo*0.25, limb*0.35*(1.0-term));",
"  }",
"  gl_FragColor=vec4(col,alpha);",
"}"
].join("\\n");
var prPL=prog(VS_PL,FS_PL,"planets");
/* Sparkle shader - 4-pointed star flares */
var VS_SP=[
"attribute vec3 aCenter;",
"attribute vec2 aCorner;",
"attribute float aRadius;",
"attribute float aSeed;",
"attribute float aBright;",
"uniform mat4 uProj;",
"uniform mat4 uView;",
"uniform float uTime;",
"varying vec2 vP;",
"varying float vSeed;",
"varying float vBright;",
"void main(){",
"  vP=aCorner; vSeed=aSeed; vBright=aBright;",
"  float tw=0.7+0.5*sin(uTime*2.2+aSeed*40.0);",
"  vec4 vc=uView*vec4(aCenter,1.0);",
"  vc.xy+=aCorner*aRadius*tw;",
"  gl_Position=uProj*vc;",
"}"
].join("\\n");
var FS_SP=[
"precision highp float;",
"varying vec2 vP;",
"varying float vSeed;",
"varying float vBright;",
"void main(){",
"  vec2 p=vP;",
"  float hx=smoothstep(0.10,0.0,abs(p.y))*smoothstep(1.0,0.15,abs(p.x));",
"  float vy=smoothstep(0.10,0.0,abs(p.x))*smoothstep(1.0,0.15,abs(p.y));",
"  float core=smoothstep(0.35,0.0,length(p));",
"  float star=hx+vy+core*1.2;",
"  if(star<0.01) discard;",
"  vec3 tint=mix(vec3(1.0,0.95,0.85),vec3(0.75,0.85,1.0),fract(vSeed*7.0));",
"  gl_FragColor=vec4(tint*star*vBright, star*vBright*0.85);",
"}"
].join("\\n");
var prSP=prog(VS_SP,FS_SP,"sparkles");
/* Shock bubble shader - iridescent expanding sphere */
var VS_SH=[
"attribute vec3 aCenter;",
"attribute vec2 aCorner;",
"attribute float aRadius;",
"uniform mat4 uProj;",
"uniform mat4 uView;",
"varying vec2 vP;",
"void main(){",
"  vP=aCorner;",
"  vec4 vc=uView*vec4(aCenter,1.0);",
"  vc.xy+=aCorner*aRadius;",
"  gl_Position=uProj*vc;",
"}"
].join("\\n");
var FS_SH=[
"precision highp float;",
"varying vec2 vP;",
"uniform float uTime;",
"void main(){",
"  vec2 p=vP;",
"  float r=length(p);",
"  if(r>1.0) discard;",
"  vec3 n=vec3(p.x,p.y,sqrt(max(0.0,1.0-r*r)));",
"  float fres=pow(1.0-max(dot(n,vec3(0.0,0.0,1.0)),0.0),2.0);",
"  float band=sin((r*8.0-uTime*2.0)+sin(atan(p.y,p.x)*3.0)*1.5);",
"  vec3 rainbow=mix(vec3(1.0,0.3,0.8),vec3(0.3,0.8,1.0),smoothstep(-1.0,1.0,band));",
"  rainbow=mix(rainbow,vec3(0.4,1.0,0.6),smoothstep(0.0,1.0,sin(band*2.0))*0.5);",
"  float alpha=fres*0.85+smoothstep(0.9,1.0,r)*0.3;",
"  vec3 col=rainbow*(0.4+fres*1.2)+vec3(0.9,0.95,1.0)*pow(fres,3.0)*0.8;",
"  // faint inner glow",
"  col+=vec3(0.5,0.7,1.0)*smoothstep(0.5,0.0,r)*0.15;",
"  gl_FragColor=vec4(col,alpha);",
"}"
].join("\\n");
var prSH=prog(VS_SH,FS_SH,"shockbubble");
var prL=prog(VS_L,FS_L,"lines");
/* Ribbon shader (GTA V style lightning - camera-facing quads) */
var VS_R=[
"attribute vec3 aPos;",
"attribute vec3 aCol;",
"attribute vec2 aUV;",
"uniform mat4 uProj;",
"uniform mat4 uView;",
"varying vec3 vCol;",
"varying vec2 vUV;",
"void main(){vCol=aCol;vUV=aUV;gl_Position=uProj*uView*vec4(aPos,1.0);}"
].join("\\n");
var FS_R=[
"precision highp float;",
"varying vec3 vCol;",
"varying vec2 vUV;",
"void main(){",
"  float d=abs(vUV.y-0.5)*2.0;",
"  float core=pow(max(0.0,1.0-d),2.2);",
"  float glow=pow(max(0.0,1.0-d),0.7)*0.35;",
"  float a=core+glow;",
"  gl_FragColor=vec4(vCol*a,a);",
"}"
].join("\\n");
var prR=prog(VS_R,FS_R,"ribbons");

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
var show={stars:true,elements:true,dust:true,clouds:true,planets:true,lightning:true,rays:true,smoke:true,snow:true,sparkle:true,shock:true,fg:true};
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
    if(EL.fire>0.02)y+=Math.sin(time*2+b.sd*6.28)*1.2*EL.fire+(1-b.r)*3*cur.i*EL.fire;
    sPos[k*3]=x;sPos[k*3+1]=y;sPos[k*3+2]=z;
    var coreF=1-b.r;
    var cr=Math.min(1,base[0]*(0.3+coreF)*bright);
    var cg=Math.min(1,base[1]*(0.3+coreF)*bright);
    var cb=Math.min(1,base[2]*(0.3+coreF)*bright);
    if(cur.v<0){cr=Math.min(1,cr+(-cur.v)*0.25);cb=Math.min(1,cb+(-cur.v)*0.12);}
    if(EL.fire>0.02){
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
var NSW2=800;
var snPos=new Float32Array(NSW2*3),snCol=new Float32Array(NSW2*3),snSize=new Float32Array(NSW2),snSeed=new Float32Array(NSW2);
var snBase=[];
for(var sni=0;sni<NSW2;sni++){
  snBase.push({x:(Math.random()-0.5)*2,y:Math.random(),z:(Math.random()-0.5)*2,
    sp:0.3+Math.random()*0.7,ph:Math.random()*6.28,sd:Math.random(),sz:2.2+Math.random()*3.2});
  snSeed[sni]=snBase[sni].sd;
}
var snBuf=gl.createBuffer(),snColB=gl.createBuffer(),snSizeB=gl.createBuffer(),snSdB=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,snSdB);gl.bufferData(gl.ARRAY_BUFFER,snSeed,gl.STATIC_DRAW);
function updateSnow(time){
  var spread=gSpread;
  var snowA=EL.snow;
  for(var k=0;k<NSW2;k++){
    var b=snBase[k];
    if(snowA<0.02){snPos[k*3+1]=-100;snCol[k*3]=snCol[k*3+1]=snCol[k*3+2]=0;snSize[k]=0.01;continue;}
    // Slow fall with sway, swirl buildup near bottom
    b.y-=0.0035*b.sp*(0.4+snowA);
    if(b.y<-0.9){b.y=0.9;b.x=(Math.random()-0.5)*2;b.z=(Math.random()-0.5)*2;}
    // Flutter: snowflakes wobble as they fall
    var flutter=Math.sin(time*2.2+b.ph*3.0)*0.35+Math.sin(time*3.7+b.ph)*0.15;
    var sway=Math.sin(time*0.9+b.ph)*0.5+flutter;
    // Swirl: vortex motion
    var ang=Math.atan2(b.z,b.x)+0.006*(0.5+snowA)+Math.sin(time*0.5+b.ph)*0.01;
    var rad=Math.hypot(b.x,b.z);
    rad=Math.max(0.15,rad-0.0008*snowA);
    var x=Math.cos(ang)*rad*spread*0.8+sway;
    var z=Math.sin(ang)*rad*spread*0.7-4+Math.cos(time*0.7+b.ph)*0.3;
    var y=b.y*spread*0.55;
    snPos[k*3]=x;snPos[k*3+1]=y;snPos[k*3+2]=z;
    var tw2=0.6+0.4*Math.sin(time*2+b.ph*3);
    snCol[k*3]=1.4*tw2*snowA;snCol[k*3+1]=1.5*tw2*snowA;snCol[k*3+2]=1.8*tw2*snowA;
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
    if(EL.fire>0.02){
      b.a+=0.045*b.sp*(1+cur.i*1.5);
      b.y+=0.008*b.sp*(0.5+cur.i);
      if(b.y>1)b.y=-1;
      var r=b.r*spread*0.45;
      x=Math.cos(b.a)*r+Math.sin(time*7+b.sd*30)*0.5*cur.i;
      z=Math.sin(b.a)*r*0.8-4+Math.cos(time*6+b.sd*25)*0.5*cur.i;
      y=b.y*spread*0.5;
      var heat=1-Math.abs(b.y);
      cr=1.0*EL.fire;cg=(0.25+heat*0.45)*EL.fire;cb=(0.05+heat*0.1)*EL.fire;
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
var NSM=900;
var smPos=new Float32Array(NSM*3),smCol=new Float32Array(NSM*3),smSize=new Float32Array(NSM),smSeed=new Float32Array(NSM);
var smBase=[];
for(var smi=0;smi<NSM;smi++){
  smBase.push({a:Math.random()*6.283,r:0.2+Math.random()*0.8,y:Math.random(),
    sp:0.2+Math.random()*0.5,ph:Math.random()*6.28,sd:Math.random(),sz:5+Math.random()*8,life:Math.random()});
  smSeed[smi]=smBase[smi].sd;
}
var smBuf=gl.createBuffer(),smColB=gl.createBuffer(),smSizeB=gl.createBuffer(),smSdB=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,smSdB);gl.bufferData(gl.ARRAY_BUFFER,smSeed,gl.STATIC_DRAW);
function updateSmoke(time){
  var spread=gSpread;
  var smokeA=EL.smoke;
  for(var k=0;k<NSM;k++){
    var b=smBase[k];
    if(smokeA<0.03){smPos[k*3+1]=-100;smCol[k*3]=smCol[k*3+1]=smCol[k*3+2]=0;smSize[k]=0.01;continue;}
    // Rise + curl: lifelike wisp motion
    b.life+=0.0022*b.sp*(0.5+cur.tb*0.5);
    if(b.life>1){b.life=0;b.a=Math.random()*6.283;b.r=0.2+Math.random()*0.6;}
    b.a+=0.003*(0.5+cur.tb*0.5);
    var r=b.r*spread*(0.5+b.life*0.7);
    var curl=Math.sin(time*0.8+b.ph+b.life*5)*0.8;
    var x=Math.cos(b.a)*r+curl;
    var z=Math.sin(b.a)*r*0.75-4+Math.cos(time*0.6+b.ph)*0.6;
    var y=(b.y-0.5)*spread*0.4+b.life*spread*0.35;
    smPos[k*3]=x;smPos[k*3+1]=y;smPos[k*3+2]=z;
    var fade=Math.sin(b.life*Math.PI);
    var g=0.32+0.1*Math.sin(time+b.ph);
    smCol[k*3]=g*1.6*smokeA*fade;smCol[k*3+1]=g*1.7*smokeA*fade;smCol[k*3+2]=g*2.0*smokeA*fade;
    var breathe=1+0.18*Math.sin(time*0.9+b.ph*2.0);
    smSize[k]=b.sz*(0.7+b.life*0.9)*breathe;
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
var bCOR0=new Float32Array(NB*6*2);
var bBase=[];
for(var bi=0;bi<NB;bi++){
  bBase.push({a:Math.random()*6.283,r:0.15+Math.random()*0.85,y:(Math.random()-0.5)*0.7,
    rad:6+Math.random()*14,al:0.10+Math.random()*0.14,sd:Math.random(),dp:(Math.random()-0.5)*14,
    hueShift:(Math.random()-0.5)*0.35});
  for(var bc2=0;bc2<6;bc2++){
    var cn=[[-1,-1],[1,-1],[1,1],[-1,-1],[1,1],[-1,1]][bc2];
    bCOR[(bi*6+bc2)*2]=cn[0];bCOR[(bi*6+bc2)*2+1]=cn[1];
    bCOR0[(bi*6+bc2)*2]=cn[0];bCOR0[(bi*6+bc2)*2+1]=cn[1];
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
  var windStr=(EL.wind*5+cur.tb*1.5)*gust;
  var windAng=time*0.15;
  var windX=Math.cos(windAng)*windStr, windZ=Math.sin(windAng)*windStr*0.6;
  var _wl=Math.hypot(windX,windZ); if(_wl>3){windX*=3/_wl;windZ*=3/_wl;}
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
      var cx0=bCOR0[(i*6+c2)*2],cy0=bCOR0[(i*6+c2)*2+1];
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
      var stormDark=1-EL.lightning*0.55;
      var hs=b.hueShift||0;
      bCC[vi*3]=Math.min(1,base[0]*darkF*depthF*stormDark+Math.max(0,hs)*0.5);
      bCC[vi*3+1]=base[1]*darkF*depthF*stormDark;
      bCC[vi*3+2]=Math.min(1,base[2]*darkF*depthF*stormDark+Math.max(0,-hs)*0.5);
      bRD[vi]=Math.min(14,b.rad*(0.8+cur.i*0.5));
      var _cdx=x-camPos[0],_cdy=y-camPos[1],_cdz=z-camPos[2];
      var _cdist=Math.sqrt(_cdx*_cdx+_cdy*_cdy+_cdz*_cdz);
      var _camFade=Math.min(1,Math.max(0,(_cdist-10)/8));
      var _smokeX=1-Math.min(1,EL.smoke*2.2);
      bAL[vi]=b.al*(1.6+cur.l*1.5)*_camFade*_smokeX;
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
/* ---- Sunlight rays (happiness + warmth) ---- */
var NRAY=14;
var rayPos=new Float32Array(NRAY*2*3), rayCol=new Float32Array(NRAY*2*3);
var rayBuf=gl.createBuffer(), rayColB=gl.createBuffer();
function updateSunRays(time,proj,view){
  if(!show.rays)return;
  var rayI=Math.max(EL.sun, EL.lightning*0.7);
  if(rayI>0.03){
    var sunI=rayI;
    for(var i=0;i<NRAY;i++){
      var a=(i/NRAY)*Math.PI*2+time*0.05;
      var len=(6+Math.sin(time*1.3+i)*2)*(0.5+sunI*0.8);
      var dx=Math.cos(a),dy=Math.sin(a)*0.6;
      // perpendicular for jaggedness
      var px2=-dy,py2=dx;
      var pts=[];
      var segs=9;
      for(var s2=0;s2<=segs;s2++){
        var t=s2/segs;
        var rr=1.5+t*(len-1.5);
        var jag=(Math.sin(s2*12.9898+i*78.233)*43758.5453)%1;
        jag=(jag-Math.floor(jag)-0.5)*2.0*(0.4+t*1.4);
        // animate the jag slightly
        jag+=Math.sin(time*4+s2*2.1+i)*0.15*t;
        pts.push([dx*rr+px2*jag, dy*rr+py2*jag, -4+Math.sin(a)*2*t+Math.sin(time*2+s2)*0.1*t]);
      }
      var b=sunI*(0.7+0.3*Math.sin(time*3+i*1.7));
      var stormMix=Math.min(1,EL.lightning*1.5);
      var cr=b*(1.4-0.5*stormMix), cg=b*(1.1-0.2*stormMix), cb=b*(0.5+0.7*stormMix);
      boltRibbons(pts,0.055,cr,cg,cb,0.9+0.2*Math.sin(time*5+i));
    }
  }
  drawRibbons(proj,view);
}
/* ---- Sparkle glitter (joy + brightness) ---- */
var NSP=250;
var spPos=new Float32Array(NSP*3),spCol=new Float32Array(NSP*3),spSize=new Float32Array(NSP),spSeed=new Float32Array(NSP);
var spBase=[];
for(var spi=0;spi<NSP;spi++){
  spBase.push({a:Math.random()*6.283,r:Math.pow(Math.random(),0.7),ph:Math.random()*6.28,sd:Math.random(),sz:0.5+Math.random()*1.2});
  spSeed[spi]=spBase[spi].sd;
}
var spBuf=gl.createBuffer(),spColB=gl.createBuffer(),spSizeB=gl.createBuffer(),spSdB=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,spSdB);gl.bufferData(gl.ARRAY_BUFFER,spSeed,gl.STATIC_DRAW);
function updateSparkle(time){
  var spread=gSpread;
  for(var k=0;k<NSP;k++){
    var b=spBase[k];
    if(EL.sparkle<0.03){spPos[k*3+1]=-100;spCol[k*3]=spCol[k*3+1]=spCol[k*3+2]=0;spSize[k]=0.01;continue;}
    b.a+=0.01;
    var r=b.r*spread*0.75;
    spPos[k*3]=Math.cos(b.a)*r;
    spPos[k*3+1]=Math.sin(b.a*2+time)*r*0.3;
    spPos[k*3+2]=Math.sin(b.a)*r*0.7-4;
    var tw=0.3+0.7*Math.abs(Math.sin(time*4+b.ph*5));
    spCol[k*3]=1.0*tw*EL.sparkle;spCol[k*3+1]=0.95*tw*EL.sparkle;spCol[k*3+2]=0.75*tw*EL.sparkle;
    spSize[k]=b.sz*(0.8+tw*0.8);
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,spBuf);gl.bufferData(gl.ARRAY_BUFFER,spPos,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,spColB);gl.bufferData(gl.ARRAY_BUFFER,spCol,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,spSizeB);gl.bufferData(gl.ARRAY_BUFFER,spSize,gl.DYNAMIC_DRAW);
}
/* ================= PLANETS ================= */
var NPL=5;
var planets=[
  {a:0.8,r:1.70,y:4.5,size:4.2,type:0,sp:0.020},  /* gas giant - background */
  {a:2.9,r:1.35,y:-3.2,size:2.8,type:1,sp:0.045}, /* rocky - away from center */
  {a:4.4,r:1.50,y:-4.8,size:2.2,type:2,sp:0.030}, /* ice - away from center */
  {a:5.6,r:1.60,y:2.8,size:3.0,type:3,sp:0.060},  /* lava - background */
  {a:1.9,r:1.90,y:0.8,size:3.8,type:4,sp:0.015}   /* ringed - deep background */
];
var plCen=new Float32Array(NPL*6*3),plTyp=new Float32Array(NPL*6),
    plRad=new Float32Array(NPL*6),
    plCor=new Float32Array(NPL*6*2),plSd=new Float32Array(NPL*6);
(function(){
  var cn=[[-1,-1],[1,-1],[1,1],[-1,-1],[1,1],[-1,1]];
  for(var pi=0;pi<NPL;pi++)for(var q=0;q<6;q++){
    plCor[(pi*6+q)*2]=cn[q][0];plCor[(pi*6+q)*2+1]=cn[q][1];plSd[pi*6+q]=Math.random();
  }
})();
var plCenBuf=gl.createBuffer(),plTypBuf=gl.createBuffer(),plRadBuf=gl.createBuffer(),
    plCorBuf=gl.createBuffer(),plSdBuf=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,plCorBuf);gl.bufferData(gl.ARRAY_BUFFER,plCor,gl.STATIC_DRAW);
gl.bindBuffer(gl.ARRAY_BUFFER,plSdBuf);gl.bufferData(gl.ARRAY_BUFFER,plSd,gl.STATIC_DRAW);

function updatePlanets(){
  var spread=gSpread;
  for(var pi=0;pi<NPL;pi++){
    var p=planets[pi];
    p.a+=p.sp*0.016;
    var x=Math.cos(p.a)*spread*p.r*1.35,z=Math.sin(p.a)*spread*p.r*1.15-4,y=p.y;
    for(var q=0;q<6;q++){
      var vi=pi*6+q;
      plCen[vi*3]=x;plCen[vi*3+1]=y;plCen[vi*3+2]=z;
      plTyp[vi]=p.type;plRad[vi]=p.size;
    }
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,plCenBuf);gl.bufferData(gl.ARRAY_BUFFER,plCen,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,plTypBuf);gl.bufferData(gl.ARRAY_BUFFER,plTyp,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,plRadBuf);gl.bufferData(gl.ARRAY_BUFFER,plRad,gl.DYNAMIC_DRAW);
}

var NSP2=160;
var spkCen=new Float32Array(NSP2*6*3),spkCor=new Float32Array(NSP2*6*2),
    spkRad=new Float32Array(NSP2*6),spkSd=new Float32Array(NSP2*6),spkBr=new Float32Array(NSP2*6);
var spkBase=[];
for(var spi=0;spi<NSP2;spi++){
  spkBase.push({
    x:(Math.random()-0.5)*36, y:(Math.random()-0.5)*20, z:-4+(Math.random()-0.5)*24,
    sz:0.25+Math.random()*0.55, sd:Math.random(), ph:Math.random()*6.28
  });
}
(function(){
  var cn=[[-1,-1],[1,-1],[1,1],[-1,-1],[1,1],[-1,1]];
  for(var pi=0;pi<NSP2;pi++)for(var q=0;q<6;q++){
    spkCor[(pi*6+q)*2]=cn[q][0];spkCor[(pi*6+q)*2+1]=cn[q][1];spkSd[pi*6+q]=spkBase[pi].sd;
  }
})();
var spkCenBuf=gl.createBuffer(),spkCorBuf=gl.createBuffer(),spkRadBuf=gl.createBuffer(),
    spkSdBuf=gl.createBuffer(),spkBrBuf=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,spkCorBuf);gl.bufferData(gl.ARRAY_BUFFER,spkCor,gl.STATIC_DRAW);
gl.bindBuffer(gl.ARRAY_BUFFER,spkSdBuf);gl.bufferData(gl.ARRAY_BUFFER,spkSd,gl.STATIC_DRAW);
function updateSparkles(time){
  var boost=0.35+EL.sparkle*1.8+cur.l*0.5;
  for(var i=0;i<NSP2;i++){
    var b=spkBase[i];
    // gentle drift
    var x=b.x+Math.sin(time*0.3+b.ph)*0.8;
    var y=b.y+Math.cos(time*0.22+b.ph*1.3)*0.6;
    for(var q=0;q<6;q++){
      var vi=i*6+q;
      spkCen[vi*3]=x;spkCen[vi*3+1]=y;spkCen[vi*3+2]=b.z;
      spkRad[vi]=b.sz;
      spkBr[vi]=boost*(0.6+0.4*Math.sin(time*1.5+b.ph*3.0));
    }
  }
  gl.bindBuffer(gl.ARRAY_BUFFER,spkCenBuf);gl.bufferData(gl.ARRAY_BUFFER,spkCen,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,spkRadBuf);gl.bufferData(gl.ARRAY_BUFFER,spkRad,gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,spkBrBuf);gl.bufferData(gl.ARRAY_BUFFER,spkBr,gl.DYNAMIC_DRAW);
}

var shockBubbles=[];
var shCenBuf=gl.createBuffer(),shCorBuf=gl.createBuffer(),shRadBuf=gl.createBuffer();
(function(){
  var cn=[[-1,-1],[1,-1],[1,1],[-1,-1],[1,1],[-1,1]];
  var tmp=new Float32Array(6*2);
  for(var q=0;q<6;q++){tmp[q*2]=cn[q][0];tmp[q*2+1]=cn[q][1];}
  gl.bindBuffer(gl.ARRAY_BUFFER,shCorBuf);gl.bufferData(gl.ARRAY_BUFFER,tmp,gl.STATIC_DRAW);
})();
function spawnShockBubble(){
  shockBubbles.push({
    x:(Math.random()-0.5)*16, y:(Math.random()-0.5)*8, z:-4+(Math.random()-0.5)*8,
    r:0.5, maxR:6+Math.random()*6, life:1
  });
}
function updateShockBubbles(time,proj,view){
  // Trigger: supernova emotion OR high intensity + high luminosity moments
  var shockTrig=EL.supernova>0.5||(cur.i>0.85&&cur.l>0.7&&Math.random()<0.008);
  if(shockTrig&&shockBubbles.length<3)spawnShockBubble();
  if(shockBubbles.length===0)return;
  var cen=[],rad=[];
  for(var i=shockBubbles.length-1;i>=0;i--){
    var b=shockBubbles[i];
    b.r+=(b.maxR-b.r)*0.03+0.08;
    b.life-=0.008;
    if(b.life<=0||b.r>=b.maxR){shockBubbles.splice(i,1);continue;}
    for(var q=0;q<6;q++){
      cen.push(b.x,b.y,b.z);rad.push(b.r);
    }
  }
  if(cen.length===0)return;
  gl.useProgram(prSH);
  gl.uniformMatrix4fv(gl.getUniformLocation(prSH,"uProj"),false,proj);
  gl.uniformMatrix4fv(gl.getUniformLocation(prSH,"uView"),false,view);
  gl.uniform1f(gl.getUniformLocation(prSH,"uTime"),time);
  gl.bindBuffer(gl.ARRAY_BUFFER,shCenBuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(cen),gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER,shRadBuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(rad),gl.DYNAMIC_DRAW);
  attr(prSH,shCenBuf,"aCenter",3);attr(prSH,shCorBuf,"aCorner",2);attr(prSH,shRadBuf,"aRadius",1);
  gl.drawArrays(gl.TRIANGLES,0,cen.length/3);
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
var rbPosBuf=gl.createBuffer(),rbColBuf=gl.createBuffer(),rbUVBuf=gl.createBuffer();
var MAXRB=6000;

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
  var nBr=4+Math.floor(Math.random()*4);
  for(var bi=0;bi<nBr;bi++){
    var idx=4+Math.floor(Math.random()*Math.max(1,pts.length-8));
    var bp=pts[idx];
    var bth=Math.random()*6.283,bph=Math.acos(2*Math.random()-1),bl=1.5+Math.random()*3.5;
    var be=[bp[0]+Math.sin(bph)*Math.cos(bth)*bl,bp[1]+Math.cos(bph)*bl,bp[2]+Math.sin(bph)*Math.sin(bth)*bl];
    branches.push({pts:subdiv(bp,be,1.0,3),w:0.4+Math.random()*0.3});
  }
  return {pts:pts,branches:branches,life:1,trail:[],_gold:false};
}

/* Shared ribbon system (lightning + electric sun rays) */
var rbRp=[],rbRc=[],rbRu=[],rbRn=0;
function ribbonSeg(p0,p1,w0,w1,r,g,b){
  if(rbRn>=MAXRB)return;
  var cx=camPos[0],cy=camPos[1],cz=camPos[2];
  var dx=p1[0]-p0[0],dy=p1[1]-p0[1],dz=p1[2]-p0[2];
  var mx=(p0[0]+p1[0])/2-cx,my=(p0[1]+p1[1])/2-cy,mz=(p0[2]+p1[2])/2-cz;
  var sx=dy*mz-dz*my,sy=dz*mx-dx*mz,sz=dx*my-dy*mx;
  var sl=Math.hypot(sx,sy,sz)||1;sx/=sl;sy/=sl;sz/=sl;
  var v=[
    [p0[0]-sx*w0,p0[1]-sy*w0,p0[2]-sz*w0,0],
    [p0[0]+sx*w0,p0[1]+sy*w0,p0[2]+sz*w0,1],
    [p1[0]-sx*w1,p1[1]-sy*w1,p1[2]-sz*w1,0],
    [p1[0]+sx*w1,p1[1]+sy*w1,p1[2]+sz*w1,1]
  ];
  var idx=[0,1,2,1,3,2];
  for(var k=0;k<6;k++){
    var vv=v[idx[k]];
    rbRp.push(vv[0],vv[1],vv[2]);rbRc.push(r,g,b);rbRu.push(idx[k]%2,vv[3]);rbRn++;
  }
}
function boltRibbons(pts,wBase,colR,colG,colB,flick){
  for(var s=0;s<pts.length-1;s++){
    var p0=pts[s],p1=pts[s+1];
    var t=s/(pts.length-1);
    var taper=1-t*0.6;
    var w=wBase*taper*(0.8+0.4*flick);
    ribbonSeg(p0,p1,w*5.5,w*5.5,colR*0.18,colG*0.22,colB*0.45);
    ribbonSeg(p0,p1,w,w,colR,colG,colB);
  }
}
function drawRibbons(proj,view){
  if(rbRn>0){
    gl.useProgram(prR);
    gl.uniformMatrix4fv(gl.getUniformLocation(prR,"uProj"),false,proj);
    gl.uniformMatrix4fv(gl.getUniformLocation(prR,"uView"),false,view);
    gl.bindBuffer(gl.ARRAY_BUFFER,rbPosBuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(rbRp),gl.DYNAMIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER,rbColBuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(rbRc),gl.DYNAMIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER,rbUVBuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(rbRu),gl.DYNAMIC_DRAW);
    attr(prR,rbPosBuf,"aPos",3);attr(prR,rbColBuf,"aCol",3);attr(prR,rbUVBuf,"aUV",2);
    gl.drawArrays(gl.TRIANGLES,0,rbRn);
  }
  rbRp=[];rbRc=[];rbRu=[];rbRn=0;
}
function drawLightning(time,proj,view){
  // glow points (for orb mode and trail)
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
    // GTA V flicker: bright strike, flickering decay
    var flick=b.life>0.7?1.0:(0.6+0.4*Math.sin(time*16+b.pts[0][0]*10));
    var fl=(b.life>0.75?3.4:(b.life>0.3?1.6:b.life*2.8))*flick;
    // main channel: white-hot core + blue halo
    boltRibbons(b.pts,0.09,fl,fl*0.96,fl*0.88,1.0);
    // branches: thinner, bluer
    for(var bi=0;bi<b.branches.length;bi++){
      var br=b.branches[bi],bp=br.pts;
      boltRibbons(bp,0.05*br.w+0.02,fl*0.75*br.w,fl*0.8*br.w,fl*br.w,0.8);
    }
    if(lightningOrbs){
      for(var s=0;s<b.pts.length;s+=3){
        var pp=b.pts[s];
        addGlow(pp[0],pp[1],pp[2],fl*0.3,7+Math.random()*6,b._gold);
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
  /* Solar flare arcs as gold ribbons */
  for(var fi=0;fi<flares.length;fi++){
    var f=flares[fi],fp=f.pts;
    var fb=f.life*2.4;
    boltRibbons(fp,0.06,fb,fb*0.65,fb*0.25,1.0);
  }
  drawRibbons(proj,view);
  // Draw glow points
  if(n>0){
    gl.bindBuffer(gl.ARRAY_BUFFER,lbBuf);gl.bufferData(gl.ARRAY_BUFFER,lbPos,gl.DYNAMIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER,lbColBuf);gl.bufferData(gl.ARRAY_BUFFER,lbCol,gl.DYNAMIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER,lbSizeBuf);gl.bufferData(gl.ARRAY_BUFFER,lbSize,gl.DYNAMIC_DRAW);
    drawPointsP(prP,time,proj,view,lbBuf,lbColBuf,lbSizeBuf,lbSeedBuf,n);
  }
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
    var R=snova.t*22,fade=Math.max(0,1-snova.t/1.6);
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
  var msg="[v15] emo: "+cur.name+"\\n theme: "+(cur.theme||"none")+"\\n lAct: "+_lActDbg.toFixed(2)+"\\n bolts: "+bolts.length+"\\n flares: "+flares.length+"\\n el: F"+EL.fire.toFixed(1)+" L"+EL.lightning.toFixed(1)+" W"+EL.wind.toFixed(1)+" S"+EL.sun.toFixed(1);
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
var camPos=[26,7,0];
var startT=performance.now();
function loop(){
  requestAnimationFrame(loop);
  var time=(performance.now()-startT)/1000;
  var keys=["v","i","tb","l","tp","g"],kk;
  for(var qi=0;qi<keys.length;qi++){kk=keys[qi];cur[kk]+=(tgt[kk]-cur[kk])*0.04;}
  if(Math.abs(cur.v-tgt.v)<0.04&&Math.abs(cur.i-tgt.i)<0.04){cur.hue=tgt.hue;cur.theme=tgt.theme;}
  flashA*=0.85;
  updateElements2();
  camA+=0.0006*(0.5+cur.tb);

  var w=canvas.width,h=canvas.height;
  var proj=persp(55*Math.PI/180,w/h,0.5,200);
  var ex=Math.cos(camA)*camR,ez=Math.sin(camA)*camR;
  camPos=[ex,camH,ez];
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

  if(show.dust)drawPointsP(prP,time,proj,view,dBuf,dColB,dSizeB,dSeedB,ND);
  if(show.clouds)drawBillboardsP(prB,time,proj,view);
  if(show.clouds)drawCoreGlow(prB,time,proj,view);
  /* planets via billboard prog */
  updateSparkles(time);
  if(show.sparkle)(function(){
    gl.useProgram(prSP);
    gl.uniformMatrix4fv(gl.getUniformLocation(prSP,"uProj"),false,proj);
    gl.uniformMatrix4fv(gl.getUniformLocation(prSP,"uView"),false,view);
    gl.uniform1f(gl.getUniformLocation(prSP,"uTime"),time);
    attr(prSP,spkCenBuf,"aCenter",3);attr(prSP,spkCorBuf,"aCorner",2);
    attr(prSP,spkRadBuf,"aRadius",1);attr(prSP,spkSdBuf,"aSeed",1);attr(prSP,spkBrBuf,"aBright",1);
    gl.drawArrays(gl.TRIANGLES,0,NSP2*6);
  })();
  if(show.shock)updateShockBubbles(time,proj,view);
  if(show.planets)(function(){
    gl.useProgram(prPL);
    gl.uniformMatrix4fv(gl.getUniformLocation(prPL,"uProj"),false,proj);
    gl.uniformMatrix4fv(gl.getUniformLocation(prPL,"uView"),false,view);
    gl.uniform1f(gl.getUniformLocation(prPL,"uTime"),time);
    attr(prPL,plCenBuf,"aCenter",3);attr(prPL,plCorBuf,"aCorner",2);
    attr(prPL,plRadBuf,"aRadius",1);attr(prPL,plTypBuf,"aType",1);attr(prPL,plSdBuf,"aSeed",1);
    gl.drawArrays(gl.TRIANGLES,0,NPL*6);
  })();
  if(show.stars)drawPointsP(prP,time,proj,view,sBuf,sColBuf,sSizeBuf,sSeedBuf,NS);
  if(show.elements&&cur.theme&&cur.theme!=="nebula")drawPointsP(prP,time,proj,view,eBuf,eColBuf,eSizeBuf,eSeedBuf,NE);
  updateSnow(time);
  updateSmoke(time);
  updateForeground(time);
  if(show.fg)drawPointsP(prP,time,proj,view,fgBuf,fgColB,fgSizeB,fgSdB,NFG);
  if(show.smoke)drawPointsP(prP,time,proj,view,smBuf,smColB,smSizeB,smSdB,NSM);
  if(show.snow)drawPointsP(prP,time,proj,view,snBuf,snColB,snSizeB,snSdB,NSW2);
  if(show.shock)drawPointsP(prP,time,proj,view,swBuf,swColB,swSizeB,swSeedB,NSW);

  /* Lightning lifecycle */
  var lAct=EL.lightning*1.8;
  for(var bi3=bolts.length-1;bi3>=0;bi3--){
    var _b=bolts[bi3];
    if(_b.life>0.4&&Math.random()<0.5){
      _b.trail.push({pts:_b.pts.map(function(p){return [p[0],p[1],p[2]];}),a:_b.life*0.3});
      if(_b.trail.length>6)_b.trail.shift();
    }
    for(var _ti=_b.trail.length-1;_ti>=0;_ti--){_b.trail[_ti].a-=0.03;if(_b.trail[_ti].a<=0)_b.trail.splice(_ti,1);}
    _b.life-=0.008;
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
  if(show.lightning)drawLightning(time,proj,view);
  updateSunRays(time,proj,view);
  updateSparkle(time);
  if(show.sparkle)drawPointsP(prP,time,proj,view,spBuf,spColB,spSizeB,spSdB,NSP);

  /* Solar flares */
  var _nm=cur.name||"";
  if(EL.flare>0.25&&Math.random()<EL.flare*0.3&&flares.length<8)flares.push(makeFlare());
  for(var _fi=flares.length-1;_fi>=0;_fi--){flares[_fi].life-=0.025;if(flares[_fi].life<=0)flares.splice(_fi,1);}

  /* Supernova */
  if(EL.supernova>0.5&&!snova.active&&Math.random()<0.02)snova={active:true,t:0};
  if(snova.active){
    snova.t+=0.012;
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
(function(){
  var tg=document.getElementById('gxtoggles');
  Object.keys(show).forEach(function(k){
    var b=document.createElement('button');
    b.textContent=k;
    b.style.cssText='padding:3px 8px;border-radius:12px;font-size:10px;border:1px solid var(--hatch-widget-accent);background:transparent;color:var(--hatch-widget-accent);cursor:pointer';
    b.onclick=function(){show[k]=!show[k];b.style.opacity=show[k]?'1':'0.35';};
    tg.appendChild(b);
  });
})();
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
