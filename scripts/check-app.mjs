// Dependency-free behavior checks. Browser layout/accessibility still need visual QA.
import fs from 'node:fs/promises';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root = new URL('../', import.meta.url);
const data = JSON.parse(await fs.readFile(new URL('data/menus.json', root)));
const elements = new Map(), handlers = {};
function element(selector) {
 if (!elements.has(selector)) elements.set(selector, {value:'',checked:false,hidden:false,open:false,innerHTML:'',textContent:'',dataset:{},listeners:{},classList:{add(){},remove(){}},addEventListener(type,fn){this.listeners[type]=fn},setAttribute(k,v){this[k]=v},add(){},focus(){},showModal(){this.open=true},close(){this.open=false;this.listeners.close?.()},children:[]});
 return elements.get(selector);
}
const mealButtons=['Lunch','Dinner'].map(meal=>Object.assign(element(meal),{dataset:{meal}}));
const document={querySelector:element,querySelectorAll:s=>s==='dialog'?[element('#detail'),element('#about')]:s==='[data-meal]'?mealButtons:[],addEventListener:(type,fn)=>handlers[type]=fn,activeElement:{focus(){},isConnected:true}};
const ctx=vm.createContext({document,window:{addEventListener(){}},navigator:{onLine:true},location:{hash:'',protocol:'http:'},history:{replaceState(){}},localStorage:{getItem:()=>null,setItem(){}},setTimeout,clearTimeout,Option:function(){},fetch:async()=>({ok:true,json:async()=>structuredClone(data)}),console});
vm.runInContext(await fs.readFile(new URL('app.js',root),'utf8'),ctx);
await new Promise(resolve=>setTimeout(resolve,10));
const run=code=>vm.runInContext(code,ctx);
assert.match(element('#result-count').textContent,/119 lunch menus/);
assert.match(element('#grid').innerHTML,/Prawns curry 150g/);
run("meal='Dinner';render()");assert.match(element('#result-count').textContent,/116 dinner menus/);
element('#explicit-only').checked=true;run('render()');assert.match(element('#result-count').textContent,/2 dinner menus/);
run("meal='Lunch';render()");assert.equal(element('#empty').hidden,false);
run("meal='Dinner';reset()");element('#search').value='paneer';run('render()');assert.ok(run('filtered().length')>0);assert.ok(run("filtered().every(m=>m.searchText.includes('paneer'))"));
element('#search').value='no-such-ingredient-xyz';run('render()');assert.equal(element('#empty').hidden,false);
run('reset()');element('#style').value='Soup';element('#protein').value='Chicken';run('render()');assert.ok(run('filtered().length')>0);assert.ok(run("filtered().every(m=>m.tags.includes('Soup')&&m.tags.includes('Chicken'))"));
run("showDetail('menu-00896')");assert.equal(element('#detail').open,true);assert.match(element('#detail-content').innerHTML,/mint chutney/);assert.match(element('#detail-content').innerHTML,/L906/);assert.match(element('#detail-content').innerHTML,/Insufficient portion information/);
run('showAbout()');assert.match(element('#about-content').innerHTML,/295/);assert.doesNotMatch(element('#about-content').innerHTML,/export-legacy/);
for(const menu of data.menus){const html=run(`card(menus.find(m=>m.id===${JSON.stringify(menu.id)}))`);assert.ok(html.includes(menu.image.path)||menu.image.status!=='generated');assert.ok(html.includes('data-open'));}
for(const file of ['app.js','service-worker.js'])new vm.Script(await fs.readFile(new URL(file,root),'utf8'),{filename:file});
console.log('PASS: startup, Lunch/Dinner counts, explicit filter, search, combined filters, empty state, linked recipe details, nutrition/provenance, all 235 cards and JavaScript syntax.');
