/* Selo de novidade: compara textos com o mesmo critério de tools/repeticao.py
   (palavras de 4+ letras, sem acento, sem palavras comuns; sobreposição relativa ao texto menor). */
const NOV=(()=>{
  const STOP=new Set(`para pela pelo pelos pelas como mais menos sobre entre desde quando onde quem qual quais porque porque
este esta isto esse essa isso aquele aquela seus suas dele dela deles delas nosso nossa voce voces eles elas
ainda depois antes agora hoje ontem amanha semana dias anos sendo sera foram fosse tinha teve tem vai vao
pode podem deve devem fazer feito disse diz dizer contra todo toda todos todas cada outro outra outros outras muito muita
entao assim tambem apenas mesmo mesma nunca sempre nada tudo algo alguem governo brasil`.split(/\s+/));
  const norm=t=>{const s=String(t||"").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g,"");
    return new Set((s.match(/[a-z0-9][a-z0-9.,]*[a-z0-9]|[a-z0-9]/g)||[]).filter(w=>(w.length>=4||/^\d+$/.test(w))&&!STOP.has(w)))};
  const sim=(a,b)=>{if(!a.size||!b.size)return 0;let n=0;a.forEach(w=>{if(b.has(w))n++});return n/Math.min(a.size,b.size)};
  return{norm,sim};
})();
