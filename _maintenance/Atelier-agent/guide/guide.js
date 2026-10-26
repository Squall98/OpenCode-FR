(function(){
  var r=document.documentElement;
  document.getElementById("theme").onclick=function(){var s=r.dataset.theme?r.dataset.theme==="dark":!matchMedia("(prefers-color-scheme: light)").matches;r.dataset.theme=s?"light":"dark";};
  var b=document.querySelectorAll("nav button");
  b.forEach(function(x){x.onclick=function(){b.forEach(function(y){y.setAttribute("aria-selected",y===x);});document.querySelectorAll("section").forEach(function(s){s.classList.toggle("actif",s.id===x.dataset.o);});scrollTo(0,0);};});
  var z=document.getElementById("zoom"),zi=z.querySelector("img");
  document.querySelectorAll("figure img").forEach(function(i){i.onclick=function(){zi.src=i.src;z.style.display="flex";};});
  z.onclick=function(){z.style.display="none";};
})();
