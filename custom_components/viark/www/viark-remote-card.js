function t(t,e,i,o){var n,r=arguments.length,s=r<3?e:null===o?o=Object.getOwnPropertyDescriptor(e,i):o;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)s=Reflect.decorate(t,e,i,o);else for(var a=t.length-1;a>=0;a--)(n=t[a])&&(s=(r<3?n(s):r>3?n(e,i,s):n(e,i))||s);return r>3&&s&&Object.defineProperty(e,i,s),s}"function"==typeof SuppressedError&&SuppressedError;const e=globalThis,i=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,o=Symbol(),n=new WeakMap;let r=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==o)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(i&&void 0===t){const i=void 0!==e&&1===e.length;i&&(t=n.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&n.set(e,t))}return t}toString(){return this.cssText}};const s=(t,...e)=>{const i=1===t.length?t[0]:e.reduce((e,i,o)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+t[o+1],t[0]);return new r(i,t,o)},a=i?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const i of t.cssRules)e+=i.cssText;return(t=>new r("string"==typeof t?t:t+"",void 0,o))(e)})(t):t,{is:c,defineProperty:l,getOwnPropertyDescriptor:d,getOwnPropertyNames:h,getOwnPropertySymbols:u,getPrototypeOf:p}=Object,g=globalThis,f=g.trustedTypes,m=f?f.emptyScript:"",_=g.reactiveElementPolyfillSupport,b=(t,e)=>t,y={toAttribute(t,e){switch(e){case Boolean:t=t?m:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let i=t;switch(e){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t)}catch(t){i=null}}return i}},v=(t,e)=>!c(t,e),$={attribute:!0,type:String,converter:y,reflect:!1,useDefault:!1,hasChanged:v};Symbol.metadata??=Symbol("metadata"),g.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=$){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const i=Symbol(),o=this.getPropertyDescriptor(t,i,e);void 0!==o&&l(this.prototype,t,o)}}static getPropertyDescriptor(t,e,i){const{get:o,set:n}=d(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:o,set(e){const r=o?.call(this);n?.call(this,e),this.requestUpdate(t,r,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??$}static _$Ei(){if(this.hasOwnProperty(b("elementProperties")))return;const t=p(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(b("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(b("properties"))){const t=this.properties,e=[...h(t),...u(t)];for(const i of e)this.createProperty(i,t[i])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,i]of e)this.elementProperties.set(t,i)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const i=this._$Eu(t,e);void 0!==i&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const i=new Set(t.flat(1/0).reverse());for(const t of i)e.unshift(a(t))}else void 0!==t&&e.push(a(t));return e}static _$Eu(t,e){const i=e.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,o)=>{if(i)t.adoptedStyleSheets=o.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const i of o){const o=document.createElement("style"),n=e.litNonce;void 0!==n&&o.setAttribute("nonce",n),o.textContent=i.cssText,t.appendChild(o)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){const i=this.constructor.elementProperties.get(t),o=this.constructor._$Eu(t,i);if(void 0!==o&&!0===i.reflect){const n=(void 0!==i.converter?.toAttribute?i.converter:y).toAttribute(e,i.type);this._$Em=t,null==n?this.removeAttribute(o):this.setAttribute(o,n),this._$Em=null}}_$AK(t,e){const i=this.constructor,o=i._$Eh.get(t);if(void 0!==o&&this._$Em!==o){const t=i.getPropertyOptions(o),n="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:y;this._$Em=o;const r=n.fromAttribute(e,t.type);this[o]=r??this._$Ej?.get(o)??r,this._$Em=null}}requestUpdate(t,e,i,o=!1,n){if(void 0!==t){const r=this.constructor;if(!1===o&&(n=this[t]),i??=r.getPropertyOptions(t),!((i.hasChanged??v)(n,e)||i.useDefault&&i.reflect&&n===this._$Ej?.get(t)&&!this.hasAttribute(r._$Eu(t,i))))return;this.C(t,e,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:o,wrapped:n},r){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,r??e??this[t]),!0!==n||void 0!==r)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),!0===o&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,i]of t){const{wrapped:t}=i,o=this[e];!0!==t||this._$AL.has(e)||void 0===o||this.C(e,void 0,i,o)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[b("elementProperties")]=new Map,w[b("finalized")]=new Map,_?.({ReactiveElement:w}),(g.reactiveElementVersions??=[]).push("2.1.2");const A=globalThis,k=t=>t,E=A.trustedTypes,q=E?E.createPolicy("lit-html",{createHTML:t=>t}):void 0,x="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,S="?"+C,M=`<${S}>`,P=document,R=()=>P.createComment(""),T=t=>null===t||"object"!=typeof t&&"function"!=typeof t,O=Array.isArray,L="[ \t\n\f\r]",H=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,U=/-->/g,V=/>/g,j=RegExp(`>|${L}(?:([^\\s"'>=/]+)(${L}*=${L}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),z=/'/g,N=/"/g,I=/^(?:script|style|textarea|title)$/i,D=t=>(e,...i)=>({_$litType$:t,strings:e,values:i}),B=D(1),F=D(2),Z=Symbol.for("lit-noChange"),W=Symbol.for("lit-nothing"),K=new WeakMap,G=P.createTreeWalker(P,129);function Y(t,e){if(!O(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==q?q.createHTML(e):e}const J=(t,e)=>{const i=t.length-1,o=[];let n,r=2===e?"<svg>":3===e?"<math>":"",s=H;for(let e=0;e<i;e++){const i=t[e];let a,c,l=-1,d=0;for(;d<i.length&&(s.lastIndex=d,c=s.exec(i),null!==c);)d=s.lastIndex,s===H?"!--"===c[1]?s=U:void 0!==c[1]?s=V:void 0!==c[2]?(I.test(c[2])&&(n=RegExp("</"+c[2],"g")),s=j):void 0!==c[3]&&(s=j):s===j?">"===c[0]?(s=n??H,l=-1):void 0===c[1]?l=-2:(l=s.lastIndex-c[2].length,a=c[1],s=void 0===c[3]?j:'"'===c[3]?N:z):s===N||s===z?s=j:s===U||s===V?s=H:(s=j,n=void 0);const h=s===j&&t[e+1].startsWith("/>")?" ":"";r+=s===H?i+M:l>=0?(o.push(a),i.slice(0,l)+x+i.slice(l)+C+h):i+C+(-2===l?e:h)}return[Y(t,r+(t[i]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),o]};class X{constructor({strings:t,_$litType$:e},i){let o;this.parts=[];let n=0,r=0;const s=t.length-1,a=this.parts,[c,l]=J(t,e);if(this.el=X.createElement(c,i),G.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(o=G.nextNode())&&a.length<s;){if(1===o.nodeType){if(o.hasAttributes())for(const t of o.getAttributeNames())if(t.endsWith(x)){const e=l[r++],i=o.getAttribute(t).split(C),s=/([.?@])?(.*)/.exec(e);a.push({type:1,index:n,name:s[2],strings:i,ctor:"."===s[1]?ot:"?"===s[1]?nt:"@"===s[1]?rt:it}),o.removeAttribute(t)}else t.startsWith(C)&&(a.push({type:6,index:n}),o.removeAttribute(t));if(I.test(o.tagName)){const t=o.textContent.split(C),e=t.length-1;if(e>0){o.textContent=E?E.emptyScript:"";for(let i=0;i<e;i++)o.append(t[i],R()),G.nextNode(),a.push({type:2,index:++n});o.append(t[e],R())}}}else if(8===o.nodeType)if(o.data===S)a.push({type:2,index:n});else{let t=-1;for(;-1!==(t=o.data.indexOf(C,t+1));)a.push({type:7,index:n}),t+=C.length-1}n++}}static createElement(t,e){const i=P.createElement("template");return i.innerHTML=t,i}}function Q(t,e,i=t,o){if(e===Z)return e;let n=void 0!==o?i._$Co?.[o]:i._$Cl;const r=T(e)?void 0:e._$litDirective$;return n?.constructor!==r&&(n?._$AO?.(!1),void 0===r?n=void 0:(n=new r(t),n._$AT(t,i,o)),void 0!==o?(i._$Co??=[])[o]=n:i._$Cl=n),void 0!==n&&(e=Q(t,n._$AS(t,e.values),n,o)),e}class tt{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:i}=this._$AD,o=(t?.creationScope??P).importNode(e,!0);G.currentNode=o;let n=G.nextNode(),r=0,s=0,a=i[0];for(;void 0!==a;){if(r===a.index){let e;2===a.type?e=new et(n,n.nextSibling,this,t):1===a.type?e=new a.ctor(n,a.name,a.strings,this,t):6===a.type&&(e=new st(n,this,t)),this._$AV.push(e),a=i[++s]}r!==a?.index&&(n=G.nextNode(),r++)}return G.currentNode=P,o}p(t){let e=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}}class et{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,o){this.type=2,this._$AH=W,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=o,this._$Cv=o?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=Q(this,t,e),T(t)?t===W||null==t||""===t?(this._$AH!==W&&this._$AR(),this._$AH=W):t!==this._$AH&&t!==Z&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>O(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==W&&T(this._$AH)?this._$AA.nextSibling.data=t:this.T(P.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:i}=t,o="number"==typeof i?this._$AC(t):(void 0===i.el&&(i.el=X.createElement(Y(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===o)this._$AH.p(e);else{const t=new tt(o,this),i=t.u(this.options);t.p(e),this.T(i),this._$AH=t}}_$AC(t){let e=K.get(t.strings);return void 0===e&&K.set(t.strings,e=new X(t)),e}k(t){O(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let i,o=0;for(const n of t)o===e.length?e.push(i=new et(this.O(R()),this.O(R()),this,this.options)):i=e[o],i._$AI(n),o++;o<e.length&&(this._$AR(i&&i._$AB.nextSibling,o),e.length=o)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=k(t).nextSibling;k(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class it{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,o,n){this.type=1,this._$AH=W,this._$AN=void 0,this.element=t,this.name=e,this._$AM=o,this.options=n,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=W}_$AI(t,e=this,i,o){const n=this.strings;let r=!1;if(void 0===n)t=Q(this,t,e,0),r=!T(t)||t!==this._$AH&&t!==Z,r&&(this._$AH=t);else{const o=t;let s,a;for(t=n[0],s=0;s<n.length-1;s++)a=Q(this,o[i+s],e,s),a===Z&&(a=this._$AH[s]),r||=!T(a)||a!==this._$AH[s],a===W?t=W:t!==W&&(t+=(a??"")+n[s+1]),this._$AH[s]=a}r&&!o&&this.j(t)}j(t){t===W?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class ot extends it{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===W?void 0:t}}class nt extends it{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==W)}}class rt extends it{constructor(t,e,i,o,n){super(t,e,i,o,n),this.type=5}_$AI(t,e=this){if((t=Q(this,t,e,0)??W)===Z)return;const i=this._$AH,o=t===W&&i!==W||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,n=t!==W&&(i===W||o);o&&this.element.removeEventListener(this.name,this,i),n&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class st{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){Q(this,t)}}const at=A.litHtmlPolyfillSupport;at?.(X,et),(A.litHtmlVersions??=[]).push("3.3.3");const ct=globalThis;class lt extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,i)=>{const o=i?.renderBefore??e;let n=o._$litPart$;if(void 0===n){const t=i?.renderBefore??null;o._$litPart$=n=new et(e.insertBefore(R(),t),t,void 0,i??{})}return n._$AI(t),n})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return Z}}lt._$litElement$=!0,lt.finalized=!0,ct.litElementHydrateSupport?.({LitElement:lt});const dt=ct.litElementPolyfillSupport;dt?.({LitElement:lt}),(ct.litElementVersions??=[]).push("4.2.2");const ht={attribute:!0,type:String,converter:y,reflect:!1,hasChanged:v},ut=(t=ht,e,i)=>{const{kind:o,metadata:n}=i;let r=globalThis.litPropertyMetadata.get(n);if(void 0===r&&globalThis.litPropertyMetadata.set(n,r=new Map),"setter"===o&&((t=Object.create(t)).wrapped=!0),r.set(i.name,t),"accessor"===o){const{name:o}=i;return{set(i){const n=e.get.call(this);e.set.call(this,i),this.requestUpdate(o,n,t,!0,i)},init(e){return void 0!==e&&this.C(o,void 0,t,e),e}}}if("setter"===o){const{name:o}=i;return function(i){const n=this[o];e.call(this,i),this.requestUpdate(o,n,t,!0,i)}}throw Error("Unsupported decorator location: "+o)};function pt(t){return(e,i)=>"object"==typeof i?ut(t,e,i):((t,e,i)=>{const o=e.hasOwnProperty(i);return e.constructor.createProperty(i,t),o?Object.getOwnPropertyDescriptor(e,i):void 0})(t,e,i)}function gt(t){return pt({...t,state:!0,attribute:!1})}const ft=t=>({type:"key",key:t}),mt={type:"none"},_t={power:{icon:"M16.56,5.44L15.11,6.89C16.84,7.94 18,9.83 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12C6,9.83 7.16,7.94 8.88,6.88L7.44,5.44C5.36,6.88 4,9.28 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12C20,9.28 18.64,6.88 16.56,5.44M13,3H11V13H13",action:{type:"power"}},mute:{icon:"M12,4L9.91,6.09L12,8.18M4.27,3L3,4.27L7.73,9H3V15H7L12,20V13.27L16.25,17.53C15.58,18.04 14.83,18.46 14,18.7V20.77C15.38,20.45 16.63,19.82 17.68,18.96L19.73,21L21,19.73L12,10.73M19,12C19,12.94 18.8,13.82 18.46,14.64L19.97,16.15C20.62,14.91 21,13.5 21,12C21,7.72 18,4.14 14,3.23V5.29C16.89,6.15 19,8.83 19,12M16.5,12C16.5,10.23 15.5,8.71 14,7.97V10.18L16.45,12.63C16.5,12.43 16.5,12.21 16.5,12Z",action:ft("mute")},resol:{label:"RESOL",action:ft("resolution")},txt:{label:"TXT",action:ft("teletext")},audio:{label:"AUDIO",action:ft("audio")},subt:{label:"SUBT",action:ft("subtitle")},digit_1:{label:"1",action:ft("digit_1")},digit_2:{label:"2",action:ft("digit_2")},digit_3:{label:"3",action:ft("digit_3")},digit_4:{label:"4",action:ft("digit_4")},digit_5:{label:"5",action:ft("digit_5")},digit_6:{label:"6",action:ft("digit_6")},digit_7:{label:"7",action:ft("digit_7")},digit_8:{label:"8",action:ft("digit_8")},digit_9:{label:"9",action:ft("digit_9")},chevron_left:{label:"<",action:mt},digit_0:{label:"0",action:ft("digit_0")},chevron_right:{label:">",action:mt},vol_up:{label:"VOL\n+",action:ft("volume_up"),repeat:!0},vol_down:{label:"VOL\n−",action:ft("volume_down"),repeat:!0},fav:{label:"FAV",action:ft("favourite")},epg:{label:"EPG",action:ft("epg")},ch_up:{label:"CH\n+",action:ft("channel_up"),repeat:!0},ch_down:{label:"CH\n−",action:ft("channel_down"),repeat:!0},info:{label:"INFO",action:ft("info")},menu:{label:"MENU",action:ft("menu")},recall:{label:"RECALL",action:ft("recall")},exit:{label:"EXIT",action:ft("exit")},up:{icon:"M7,15L12,10L17,15H7Z",action:ft("up"),repeat:!0},down:{icon:"M7,10L12,15L17,10H7Z",action:ft("down"),repeat:!0},left:{icon:"M14,7L9,12L14,17V7Z",action:ft("left"),repeat:!0},right:{icon:"M10,17L15,12L10,7V17Z",action:ft("right"),repeat:!0},ok:{label:"OK",action:ft("ok")},red:{action:ft("red")},green:{action:ft("green")},yellow:{action:ft("yellow")},blue:{action:ft("blue")},f1:{label:"F1",action:ft("f1")},f2:{label:"F2",action:ft("f2")},media:{label:"MEDIA",action:ft("usb")},update:{label:"UPDATE",action:mt},rewind:{icon:"M11.5,12L20,18V6M11,18V6L2.5,12L11,18Z",action:ft("rewind")},play:{icon:"M8,5.14V19.14L19,12.14L8,5.14Z",action:ft("play")},pause:{icon:"M14,19H18V5H14M6,19H10V5H6V19Z",action:ft("pause")},fast_forward:{icon:"M13,6V18L21.5,12M4,18L12.5,12L4,6V18Z",action:ft("fast_forward")},timer:{label:"TIMER",action:ft("timer")},record:{icon:"M19,12C19,15.86 15.86,19 12,19C8.14,19 5,15.86 5,12C5,8.14 8.14,5 12,5C15.86,5 19,8.14 19,12Z",action:ft("record")},stop:{icon:"M18,18H6V6H18V18Z",action:ft("stop")},tv_radio:{label:"TV/R",action:ft("tv_radio")}},bt=_t,yt=Object.keys(_t),vt=t=>Object.prototype.hasOwnProperty.call(_t,t),$t="viark-remote-card",wt="viark-remote-card-editor",At="viark",kt={show_name:!0,show_status:!0,haptics:!0},Et=["media_player","remote"],qt=["show_name","show_status","haptics"],xt=/^[a-z0-9_]+\.[a-z0-9_]+$/,Ct=t=>"object"==typeof t&&null!==t&&!Array.isArray(t),St=t=>t.split(".",1)[0];function Mt(t,e){const i=`buttons.${t}`;if(!Ct(e))throw new Error(`'${i}' must be a mapping.`);const o=["key","perform_action","action"].filter(t=>void 0!==e[t]);if(1!==o.length)throw new Error(`'${i}' needs exactly one of 'key', 'perform_action' or 'action: none'.`);const{key:n,perform_action:r,action:s,data:a,target:c}=e;if("key"===o[0]){const t="string"==typeof n&&""!==n.trim(),e="number"==typeof n&&Number.isInteger(n)&&n>=0;if(!t&&!e)throw new Error(`'${i}.key' must be a key name or a non-negative key code.`)}if("perform_action"===o[0]){if("string"!=typeof r||!xt.test(r))throw new Error(`'${i}.perform_action' must look like 'domain.action'.`)}else if(void 0!==a||void 0!==c)throw new Error(`'${i}': 'data' and 'target' only apply to 'perform_action'.`);if("action"===o[0]&&"none"!==s)throw new Error(`'${i}.action' only supports 'none'.`);if(void 0!==a&&!Ct(a))throw new Error(`'${i}.data' must be a mapping.`);if(void 0!==c&&!Ct(c))throw new Error(`'${i}.target' must be a mapping.`)}function Pt(t,e){const i={entity_id:t};return"remote"===St(t)?{domain:"remote",service:"send_command",data:{command:e},target:i}:{domain:At,service:"send_key",data:{key:e},target:i}}function Rt(t){const e=Object.values(t.entities??{}).filter(t=>t.platform===At);return(e.find(t=>t.entity_id.startsWith("media_player."))??e.find(t=>t.entity_id.startsWith("remote.")))?.entity_id}const Tt=()=>Object.fromEntries(Array.from({length:10},(t,e)=>[`digit_${e}`,String(e)])),Ot="<, >, UPDATE",Lt={card:{name:"Viark Remote Card",description:"A replica of the Viark satellite receiver remote control."},status:{on:"On",standby:"Standby",unavailable:"Unavailable",not_found:"Entity not available: {entity}"},toast:{unsupported:"{button} is not supported by the Viark integration yet."},editor:{entity:"Viark entity (media player or remote)",name:"Name",name_helper:"Shown at the bottom of the remote. Defaults to VIARK.",show_name:"Show name",show_status:"Show power and channel",haptics:"Haptic feedback",buttons_hint:`Buttons without a verified key in the integration (${Ot}) do nothing by default. You can assign each of them a key code or any action in YAML under "buttons:" — see the README.`},buttons:{power:"Power",mute:"Mute",resol:"Resolution",txt:"Teletext",audio:"Audio track",subt:"Subtitles",...Tt(),chevron_left:"Left angle (<)",chevron_right:"Right angle (>)",vol_up:"Volume up",vol_down:"Volume down",fav:"Favourites",epg:"Programme guide",ch_up:"Channel up",ch_down:"Channel down",info:"Info",menu:"Menu",recall:"Recall",exit:"Exit",up:"Up",down:"Down",left:"Left",right:"Right",ok:"OK",red:"Red",green:"Green",yellow:"Yellow",blue:"Blue",f1:"F1",f2:"F2",media:"Media",update:"Update",rewind:"Rewind",play:"Play",pause:"Pause",fast_forward:"Fast forward",timer:"Timer",record:"Record",stop:"Stop",tv_radio:"TV / Radio"}},Ht={card:{name:"Tarjeta mando Viark",description:"Una réplica del mando a distancia del receptor de satélite Viark."},status:{on:"Encendido",standby:"En espera",unavailable:"No disponible",not_found:"Entidad no disponible: {entity}"},toast:{unsupported:"La integración Viark todavía no admite el botón {button}."},editor:{entity:"Entidad Viark (reproductor multimedia o mando)",name:"Nombre",name_helper:"Se muestra al pie del mando. Por defecto, VIARK.",show_name:"Mostrar nombre",show_status:"Mostrar encendido y canal",haptics:"Respuesta háptica",buttons_hint:`Los botones sin tecla verificada en la integración (${Ot}) no hacen nada por defecto. Puedes asignar a cada uno un código de tecla o cualquier acción en YAML bajo "buttons:" — consulta el README.`},buttons:{power:"Encendido",mute:"Silencio",resol:"Resolución",txt:"Teletexto",audio:"Pista de audio",subt:"Subtítulos",...Tt(),chevron_left:"Ángulo izquierdo (<)",chevron_right:"Ángulo derecho (>)",vol_up:"Subir volumen",vol_down:"Bajar volumen",fav:"Favoritos",epg:"Guía de programación",ch_up:"Canal siguiente",ch_down:"Canal anterior",info:"Información",menu:"Menú",recall:"Último canal",exit:"Salir",up:"Arriba",down:"Abajo",left:"Izquierda",right:"Derecha",ok:"Aceptar",red:"Rojo",green:"Verde",yellow:"Amarillo",blue:"Azul",f1:"F1",f2:"F2",media:"Multimedia",update:"Actualizar",rewind:"Retroceso rápido",play:"Reproducir",pause:"Pausa",fast_forward:"Avance rápido",timer:"Temporizador",record:"Grabar",stop:"Detener",tv_radio:"TV / Radio"}},Ut={en:Lt,es:Ht};function Vt(t,e){let i=t;for(const t of e.split(".")){if("object"!=typeof i)return;i=i[t]}return"string"==typeof i?i:void 0}function jt(t,e,i={}){const o=(t??"en").split("-")[0].toLowerCase();return(Vt(Ut[o],e)??Vt(Lt,e)??e).replace(/\{(\w+)\}/g,(t,e)=>i[e]??t)}function zt(t,e,i){const o=()=>{const o=window.customElements;o.get(t)||(o.define(t,e),i?.())};null!==document.querySelector("home-assistant")&&!window.customElements.get("home-assistant")?window.customElements.whenDefined("home-assistant").then(o):o()}const Nt=s`
  :host {
    display: block;
  }

  ha-card {
    height: 100%;
    box-sizing: border-box;
    padding: 16px;
    display: flex;
    justify-content: center;
  }

  .warning {
    padding: 8px;
    color: var(--error-color, #db4437);
  }

  .frame {
    container-type: inline-size;
    width: min(100%, var(--viark-remote-width, 280px));
  }

  .remote {
    --key-top: #3c3e43;
    --key-bottom: #25272b;
    --key-text: #ededed;
    --key-shadow: #09090a;
    --gap-color: #17181b;

    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    gap: 5cqi;
    padding: 0 7cqi 6cqi;
    border-radius: 16cqi 16cqi 14cqi 14cqi;
    background: linear-gradient(
      90deg,
      #101113 0%,
      #27292d 5%,
      #1e1f22 50%,
      #27292d 95%,
      #101113 100%
    );
    box-shadow:
      0 2cqi 5cqi rgba(0, 0, 0, 0.45),
      inset 0 0 0 0.5cqi #0b0c0d;
    color: var(--key-text);
    font-family: "Roboto Condensed", "Arial Narrow", Roboto, system-ui, sans-serif;
    font-weight: 600;
    user-select: none;
    -webkit-user-select: none;
    -webkit-tap-highlight-color: transparent;
  }

  /* Glossy IR window, doubling as the status display. */
  .cap {
    box-sizing: border-box;
    height: 14cqi;
    margin-inline: -7cqi;
    padding-inline: 10cqi;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2.5cqi;
    border-radius: 16cqi 16cqi 4cqi 4cqi;
    border-bottom: 0.6cqi solid #07070a;
    background: linear-gradient(#2b2c30, #0c0c0e 70%);
    overflow: hidden;
  }

  .led {
    flex: none;
    width: 2.6cqi;
    height: 2.6cqi;
    border-radius: 50%;
    background: #4a4a4a;
  }
  .led.on {
    background: #5bd46a;
    box-shadow: 0 0 2cqi #5bd46a;
  }
  .led.standby {
    background: #d8433b;
    box-shadow: 0 0 1.6cqi rgba(216, 67, 59, 0.7);
  }

  .status {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    color: #9fb4c8;
    font-size: 4cqi;
    font-weight: 500;
    letter-spacing: 0.02em;
  }

  /* ---- Keys ---------------------------------------------------------------- */

  .key {
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 0;
    margin: 0;
    padding: 0;
    border: none;
    border-radius: 3cqi;
    background: linear-gradient(var(--key-top), var(--key-bottom));
    box-shadow:
      0 0.9cqi 0 var(--key-shadow),
      inset 0 0.35cqi 0 rgba(255, 255, 255, 0.09);
    color: var(--key-text);
    font: inherit;
    font-size: 3.6cqi;
    line-height: 1.05;
    letter-spacing: 0.02em;
    cursor: pointer;
    touch-action: manipulation;
    -webkit-touch-callout: none;
    transition:
      transform 60ms ease,
      box-shadow 60ms ease,
      filter 120ms ease;
  }
  .key:active:not(:disabled) {
    transform: translateY(0.7cqi);
    box-shadow:
      0 0.2cqi 0 var(--key-shadow),
      inset 0 0.35cqi 0 rgba(255, 255, 255, 0.05);
    filter: brightness(1.3);
  }
  .key:focus-visible {
    outline: 0.8cqi solid var(--primary-color, #03a9f4);
    outline-offset: 0.6cqi;
  }
  .key:disabled {
    cursor: default;
    opacity: 0.45;
  }
  .key svg {
    width: 1em;
    height: 1em;
    fill: currentColor;
  }

  .row {
    display: flex;
    justify-content: space-between;
    padding-inline: 1cqi;
  }

  .grid {
    display: grid;
  }
  .four {
    grid-template-columns: repeat(4, 1fr);
    gap: 3cqi 4cqi;
  }

  .round {
    width: 14cqi;
    height: 14cqi;
    border-radius: 50%;
    font-size: 7cqi;
  }
  .power {
    background: radial-gradient(circle at 40% 35%, #ff6c73, #e23542 60%, #b0222c);
    box-shadow:
      0 0.9cqi 0 #4f0e14,
      inset 0 0.35cqi 0 rgba(255, 255, 255, 0.2);
    color: #fff;
  }
  .mute {
    background: radial-gradient(circle at 40% 35%, #4b4d53, #26282c 70%);
  }

  .pills .key {
    height: 8.5cqi;
    border-radius: 3.5cqi;
    font-size: 3.1cqi;
  }

  .numpad {
    grid-template-columns: repeat(3, 1fr);
    gap: 3.2cqi 7cqi;
    padding-inline: 1.5cqi;
  }
  .numpad .key {
    height: 8.5cqi;
    font-size: 5.2cqi;
  }

  /* ---- Volume / channel rockers ------------------------------------------- */

  .rockers {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(2, 13cqi);
    gap: 3cqi 7cqi;
    padding-inline: 1.5cqi;
    justify-items: center;
    align-items: center;
  }
  .rocker {
    grid-row: 1 / span 2;
    align-self: stretch;
    width: 82%;
    display: flex;
    flex-direction: column;
    border-radius: 3cqi;
    box-shadow: 0 0.9cqi 0 var(--key-shadow);
    overflow: hidden;
  }
  .rocker.vol {
    grid-column: 1;
  }
  .rocker.ch {
    grid-column: 3;
  }
  .rocker .key {
    flex: 1;
    border-radius: 0;
    box-shadow: inset 0 0.35cqi 0 rgba(255, 255, 255, 0.09);
    font-size: 4cqi;
    line-height: 1.15;
  }
  .rocker .key + .key {
    border-top: 0.5cqi solid #141517;
  }
  .rocker .key:active:not(:disabled) {
    transform: none;
  }
  .middle {
    grid-column: 2;
    width: 72%;
    height: 11.5cqi;
    font-size: 3.8cqi;
  }

  /* ---- Navigation pad ------------------------------------------------------ */

  .dpad {
    position: relative;
    height: 78cqi;
  }
  .ring {
    position: absolute;
    top: calc(50% - 33cqi);
    left: calc(50% - 33cqi);
    width: 66cqi;
    height: 66cqi;
    border-radius: 50%;
    overflow: hidden;
    background: radial-gradient(circle, #303236 0%, #26282c 70%, #1c1d20 100%);
    box-shadow:
      0 1cqi 0 var(--key-shadow),
      inset 0 0.4cqi 0 rgba(255, 255, 255, 0.08);
  }
  .wedge {
    position: absolute;
    inset: 0;
    display: flex;
    margin: 0;
    padding: 0;
    border: none;
    background: transparent;
    color: #e8e8e8;
    font-size: 22cqi;
    cursor: pointer;
    touch-action: manipulation;
    -webkit-touch-callout: none;
    transition: background-color 80ms ease;
  }
  .wedge svg {
    width: 1em;
    height: 1em;
    fill: currentColor;
  }
  .wedge.up {
    clip-path: polygon(0 0, 100% 0, 50% 50%);
    justify-content: center;
    align-items: flex-start;
    padding-top: 0;
  }
  .wedge.down {
    clip-path: polygon(0 100%, 100% 100%, 50% 50%);
    justify-content: center;
    align-items: flex-end;
    padding-bottom: 0;
  }
  .wedge.left {
    clip-path: polygon(0 0, 0 100%, 50% 50%);
    align-items: center;
    justify-content: flex-start;
    padding-left: 0;
  }
  .wedge.right {
    clip-path: polygon(100% 0, 100% 100%, 50% 50%);
    align-items: center;
    justify-content: flex-end;
    padding-right: 0;
  }
  .wedge:active:not(:disabled) {
    background-color: rgba(255, 255, 255, 0.1);
  }
  .wedge:focus-visible {
    outline: none;
    background-color: rgba(3, 169, 244, 0.3);
  }
  .wedge:disabled {
    cursor: default;
    opacity: 0.45;
  }

  .ok,
  .corner {
    position: absolute;
    border: 1.4cqi solid var(--gap-color);
    border-radius: 50%;
    background-clip: padding-box;
  }
  .ok {
    top: calc(50% - 12cqi);
    left: calc(50% - 12cqi);
    width: 24cqi;
    height: 24cqi;
    font-size: 7.5cqi;
  }
  .corner {
    width: 17cqi;
    height: 17cqi;
    font-size: 3.3cqi;
    letter-spacing: 0;
  }
  .corner.info {
    top: 0.5cqi;
    left: 1cqi;
  }
  .corner.menu {
    top: 0.5cqi;
    right: 1cqi;
  }
  .corner.recall {
    bottom: 1.5cqi;
    left: 1cqi;
  }
  .corner.exit {
    bottom: 1.5cqi;
    right: 1cqi;
  }

  /* ---- Colour keys ---------------------------------------------------------- */

  .colors {
    justify-items: center;
    padding-inline: 1cqi;
  }
  .color {
    width: 11.5cqi;
    height: 10.5cqi;
    border-radius: 2cqi;
  }
  .color.red {
    background: linear-gradient(#ff6d73, #e0414a);
  }
  .color.green {
    background: linear-gradient(#34cc72, #15a150);
  }
  .color.yellow {
    background: linear-gradient(#fff05a, #efd200);
  }
  .color.blue {
    background: linear-gradient(#45adff, #1985db);
  }

  /* ---- Lower media panel ---------------------------------------------------- */

  .panel {
    padding: 4cqi 3cqi;
    border-radius: 5cqi;
    background-color: #141517;
    background-image: radial-gradient(
      rgba(255, 255, 255, 0.05) 0.25cqi,
      transparent 0.4cqi
    );
    background-size: 2cqi 2cqi;
    box-shadow:
      inset 0 0.6cqi 1.5cqi rgba(0, 0, 0, 0.6),
      0 0.3cqi 0 rgba(255, 255, 255, 0.04);
  }
  .panel .four {
    gap: 3.2cqi 3.5cqi;
  }
  .panel .key {
    height: 7.5cqi;
    border-radius: 2.6cqi;
    font-size: 3cqi;
    letter-spacing: 0;
  }
  .panel .key svg {
    font-size: 5cqi;
  }
  .panel .record svg {
    color: #e5262f;
  }

  .name {
    padding-top: 3cqi;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    text-align: center;
    text-transform: uppercase;
    color: #c5d3e1;
    font-size: 6.5cqi;
    font-weight: 700;
    letter-spacing: 0.08em;
  }

  @media (prefers-reduced-motion: reduce) {
    .key,
    .wedge {
      transition: none;
    }
  }
`,It=[{name:"entity",required:!0,selector:{entity:{filter:[{integration:At,domain:"media_player"},{integration:At,domain:"remote"}]}}},{name:"name",selector:{text:{}}},{name:"",type:"grid",schema:[{name:"show_name",selector:{boolean:{}}},{name:"show_status",selector:{boolean:{}}},{name:"haptics",selector:{boolean:{}}}]}];class Dt extends lt{constructor(){super(...arguments),this._computeLabel=t=>jt(this._lang,`editor.${t.name}`),this._computeHelper=t=>"name"===t.name?jt(this._lang,"editor.name_helper"):void 0}setConfig(t){this._config=t}connectedCallback(){super.connectedCallback(),async function(){if(!customElements.get("ha-form"))try{const t=await(window.loadCardHelpers?.()),e=await(t?.createCardElement({type:"button"})),i=e?.constructor;await(i?.getConfigElement?.())}catch{}}().then(()=>this.requestUpdate())}get _lang(){return this.hass?.locale?.language??this.hass?.language}render(){return this.hass&&this._config?B`
      <ha-form
        .hass=${this.hass}
        .data=${{...kt,...this._config}}
        .schema=${It}
        .computeLabel=${this._computeLabel}
        .computeHelper=${this._computeHelper}
        @value-changed=${this._valueChanged}
      ></ha-form>
      <p class="hint">${jt(this._lang,"editor.buttons_hint")}</p>
    `:W}_valueChanged(t){t.stopPropagation();const e={...t.detail.value};for(const[t,i]of Object.entries(kt))e[t]===i&&delete e[t];e.name||delete e.name,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:e},bubbles:!0,composed:!0}))}}Dt.styles=s`
    .hint {
      margin: 16px 0 0;
      color: var(--secondary-text-color);
      font-size: 0.875rem;
      line-height: 1.4;
    }
  `,t([pt({attribute:!1})],Dt.prototype,"hass",void 0),t([gt()],Dt.prototype,"_config",void 0),zt(wt,Dt);const Bt=t=>new Promise(e=>setTimeout(e,t));class Ft extends lt{constructor(){super(...arguments),this._holdToken=0,this._holdFired=!1}static getConfigElement(){return document.createElement(wt)}static getStubConfig(t){return{entity:Rt(t)??"media_player.viark_receiver"}}setConfig(t){!function(t){if(!Ct(t))throw new Error("Invalid configuration.");const{entity:e,name:i,buttons:o}=t;if("string"!=typeof e||!e)throw new Error("Set 'entity' to the media_player or remote entity of your Viark receiver.");if(!Et.includes(St(e)))throw new Error(`'entity' must be a media_player or remote entity, got '${e}'.`);if(void 0!==i&&"string"!=typeof i)throw new Error("'name' must be text.");for(const e of qt)if(void 0!==t[e]&&"boolean"!=typeof t[e])throw new Error(`'${e}' must be true or false.`);if(void 0!==o){if(!Ct(o))throw new Error("'buttons' must be a mapping of button name to override.");for(const[t,e]of Object.entries(o)){if(!vt(t))throw new Error(`Unknown button '${t}'. Valid buttons: ${yt.join(", ")}.`);Mt(t,e)}}}(t),this._config=t}getCardSize(){return 16}getGridOptions(){return{columns:6,min_columns:4}}disconnectedCallback(){super.disconnectedCallback(),this._cancelHold()}get _lang(){return this.hass?.locale?.language??this.hass?.language}get _playerId(){return this.hass&&this._config?function(t,e){if(e.startsWith("media_player."))return e;const i=t.entities??{},o=i[e]?.device_id;return o?Object.values(i).find(t=>t.device_id===o&&t.entity_id.startsWith("media_player."))?.entity_id:void 0}(this.hass,this._config.entity):void 0}_option(t){return this._config?.[t]??kt[t]}shouldUpdate(t){if(!this._config)return!1;if(t.has("_config"))return!0;const e=t.get("hass");return!e||!this.hass||(e.language!==this.hass.language||e.locale?.language!==this.hass.locale?.language||e.entities!==this.hass.entities||[this._config.entity,this._playerId].some(t=>void 0!==t&&e.states[t]!==this.hass.states[t]))}_statusText(t,e){if("on"!==t)return"unknown"===t?"":jt(this._lang,`status.${t}`);const i=e?.attributes.media_channel,o=e?.attributes.media_title,n=[i,o].filter(t=>null!=t&&""!==t);return n.length?n.join("  "):jt(this._lang,"status.on")}render(){if(!this._config||!this.hass)return W;const t=this.hass.states[this._config.entity];if(!t)return B`<ha-card>
        <div class="warning">
          ${jt(this._lang,"status.not_found",{entity:this._config.entity})}
        </div>
      </ha-card>`;const e=this._playerId,i=e?this.hass.states[e]:void 0,o=function(t,e){if("unavailable"===t.state||"unavailable"===e?.state)return"unavailable";const i=e?.state??t.state;return"off"===i||"standby"===i?"standby":"unknown"===i?"unknown":"on"}(t,i),n="unavailable"===o,r=this._config.name??"VIARK",s=this._config.name??i?.attributes.friendly_name??t.attributes.friendly_name??r,a=(t,e="key")=>this._renderKey(t,e,n);return B`
      <ha-card>
        <div class="frame">
          <div class="remote" role="group" aria-label=${s}>
            <div class="cap">
              <span class="led ${o}"></span>
              ${this._option("show_status")?B`<span class="status" aria-live="polite"
                      >${this._statusText(o,i)}</span
                    >`:W}
            </div>

            <div class="row">
              ${a("power","key round power")} ${a("mute","key round mute")}
            </div>

            <div class="grid four pills">
              ${["resol","txt","audio","subt"].map(t=>a(t))}
            </div>

            <div class="grid numpad">
              ${["digit_1","digit_2","digit_3","digit_4","digit_5","digit_6","digit_7","digit_8","digit_9","chevron_left","digit_0","chevron_right"].map(t=>a(t))}
            </div>

            <div class="rockers">
              <div class="rocker vol">${a("vol_up")}${a("vol_down")}</div>
              ${a("fav","key middle")}
              <div class="rocker ch">${a("ch_up")}${a("ch_down")}</div>
              ${a("epg","key middle")}
            </div>

            <div class="dpad">
              <div class="ring">
                ${a("up","wedge up")} ${a("down","wedge down")}
                ${a("left","wedge left")} ${a("right","wedge right")}
              </div>
              ${a("ok","key ok")} ${a("info","key corner info")}
              ${a("menu","key corner menu")} ${a("recall","key corner recall")}
              ${a("exit","key corner exit")}
            </div>

            <div class="grid four colors">
              ${["red","green","yellow","blue"].map(t=>a(t,`key color ${t}`))}
            </div>

            <div class="panel">
              <div class="grid four">
                ${["f1","f2","media","update","rewind","play","pause","fast_forward","timer","record","stop","tv_radio"].map(t=>a(t,`key ${t}`))}
              </div>
            </div>

            ${this._option("show_name")?B`<div class="name">${r}</div>`:W}
          </div>
        </div>
      </ha-card>
    `}_renderKey(t,e,i){const o=bt[t],n=jt(this._lang,`buttons.${t}`),r=o.icon?B`<svg viewBox="0 0 24 24" aria-hidden="true">
          ${F`<path d=${o.icon}></path>`}
        </svg>`:(o.label??"").split("\n").map(t=>B`<span>${t}</span>`);return B`<button
      type="button"
      class=${e}
      data-button=${t}
      title=${n}
      aria-label=${n}
      ?disabled=${i}
      @click=${this._onClick}
      @pointerdown=${this._onPointerDown}
      @pointerup=${this._cancelHold}
      @pointerleave=${this._cancelHold}
      @pointercancel=${this._cancelHold}
      @contextmenu=${this._onContextMenu}
    >
      ${r}
    </button>`}_buttonId(t){const e=t.currentTarget?.dataset.button;return e&&vt(e)?e:void 0}_onClick(t){const e=this._buttonId(t);e&&(this._holdFired&&0!==t.detail?this._holdFired=!1:this._press(e))}_onPointerDown(t){const e=this._buttonId(t);if(this._cancelHold(),this._holdFired=!1,!e||!bt[e].repeat||0!==t.button)return;const i=this._holdToken;this._holdTimer=setTimeout(()=>{this._holdFired=!0,this._repeat(e,i)},500)}_onContextMenu(t){const e=this._buttonId(t);e&&bt[e].repeat&&t.preventDefault()}async _repeat(t,e){for(;e===this._holdToken&&this.isConnected;){if(!await this._press(t))return;await Bt(450)}}_cancelHold(){clearTimeout(this._holdTimer),this._holdTimer=void 0,this._holdToken++}async _press(t){if(!this.hass||!this._config)return!1;const e=function(t,e){const i=e.buttons?.[t];if(i){if("none"===i.action)return{type:"none"};if(i.perform_action){const[t,e]=i.perform_action.split(".");return{type:"call",call:{domain:t,service:e,data:i.data,target:i.target}}}if(void 0!==i.key)return{type:"call",call:Pt(e.entity,String(i.key).trim())}}const o=bt[t].action;switch(o.type){case"power":return{type:"call",call:{domain:St(e.entity),service:"toggle",target:{entity_id:e.entity}}};case"key":return{type:"call",call:Pt(e.entity,o.key)};case"none":return{type:"unsupported"}}}(t,this._config);if("none"===e.type)return!1;if("unsupported"===e.type)return this._haptic("warning"),this._fire("hass-notification",{message:jt(this._lang,"toast.unsupported",{button:jt(this._lang,`buttons.${t}`)})}),!1;this._haptic("light");const{domain:i,service:o,data:n,target:r}=e.call;try{return await this.hass.callService(i,o,n,r),!0}catch(t){return this._haptic("failure"),console.debug(`${$t}: ${i}.${o} failed`,t),!1}}_haptic(t){this._option("haptics")&&this._fire("haptic",t)}_fire(t,e){this.dispatchEvent(new CustomEvent(t,{detail:e,bubbles:!0,composed:!0}))}}Ft.styles=Nt,t([pt({attribute:!1})],Ft.prototype,"hass",void 0),t([gt()],Ft.prototype,"_config",void 0),zt($t,Ft,()=>{window.customCards=window.customCards??[],window.customCards.push({type:$t,name:jt(navigator.language,"card.name"),description:jt(navigator.language,"card.description"),preview:!0,documentationURL:"https://github.com/jorgediez/ha-viark#remote-card"}),console.info("%c VIARK-REMOTE-CARD %c v1.4.0 ","color: #fff; background: #1e1f22; font-weight: 700;","color: #1e1f22; background: #c5d3e1; font-weight: 700;")});export{Ft as ViarkRemoteCard};
