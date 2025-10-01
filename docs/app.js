// ========= Elements =========
const fileInput     = document.getElementById('fileInput');
const saveBtn       = document.getElementById('saveBtn');
const resetBtn      = document.getElementById('resetBtn');
const statusEl      = document.getElementById('statusText');
const origCanvas    = document.getElementById('origCanvas');
const resultCanvas  = document.getElementById('resultCanvas');
const progress      = document.getElementById('progress');

const modalEl       = document.getElementById('mainModal');
const modalTitleEl  = document.getElementById('modalTitle');
const modalBodyEl   = document.getElementById('modalBody');
const modalOkBtn    = document.getElementById('modalOkBtn');

// Bootstrap modal instance
const MainModal = new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: false });

// Canvas contexts
const octx = origCanvas.getContext('2d', { willReadFrequently: true });
const rctx = resultCanvas.getContext('2d', { willReadFrequently: true });

// ========= State =========
let resultImageData = null;

// ========= Helpers =========
function setStatus(msg){ statusEl.textContent = msg; }
function showProgress(show=true){
  progress.classList.toggle('d-none', !show);
  progress.setAttribute('aria-hidden', show ? 'false' : 'true');
}

// Ensured-visible spinner (min 300ms)
async function runWithSpinner(fn){
  showProgress(true);
  await new Promise(r => setTimeout(r, 40)); // paint spinner
  const start = performance.now();
  const res = await fn();
  const elapsed = performance.now() - start;
  if (elapsed < 300) await new Promise(r => setTimeout(r, 300 - elapsed));
  showProgress(false);
  return res;
}

function loadImageToCanvas(file){
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      let w = img.naturalWidth, h = img.naturalHeight;
      const maxW = Math.min(1600, window.innerWidth - 60);
      const maxH = Math.min(1000, Math.floor(window.innerHeight * 0.55));
      const scale = Math.min(maxW / w, maxH / h, 1);
      w = Math.max(1, Math.round(w * scale));
      h = Math.max(1, Math.round(h * scale));
      origCanvas.width = w; origCanvas.height = h;
      resultCanvas.width = w; resultCanvas.height = h;
      octx.clearRect(0,0,w,h); rctx.clearRect(0,0,w,h);
      octx.drawImage(img, 0, 0, w, h);
      resultImageData = null;
      resolve();
    };
    img.onerror = reject;
    img.src = URL.createObjectURL(file);
  });
}

// ========= Modal Utilities =========
// IMPORTANT FIX: resolve *after* modal fully hides (hidden.bs.modal)
function showFormModal({ title, bodyHTML, okText = "OK", hideOk = false, onShown = null }){
  return new Promise(resolve => {
    modalTitleEl.textContent = title;
    modalBodyEl.innerHTML = bodyHTML;

    modalOkBtn.classList.toggle('d-none', !!hideOk);
    modalOkBtn.textContent = okText;

    const cleanup = () => {
      modalEl.removeEventListener('shown.bs.modal', shownHandler);
      modalOkBtn.onclick = null;
      modalBodyEl.querySelectorAll('[data-choice]').forEach(btn => { btn.onclick = null; });
    };

    const shownHandler = () => {
      const firstInput = modalBodyEl.querySelector('input, select, button, textarea');
      if (firstInput) firstInput.focus();
      if (typeof onShown === 'function') onShown();
    };

    modalEl.addEventListener('shown.bs.modal', shownHandler, { once: true });

    // Helper to wait for hidden before resolving
    function resolveAfterHide(value){
      const onHidden = () => {
        modalEl.removeEventListener('hidden.bs.modal', onHidden);
        cleanup();
        // Tiny microtask delay gives Bootstrap time to remove backdrops
        Promise.resolve().then(() => resolve(value));
      };
      modalEl.addEventListener('hidden.bs.modal', onHidden, { once: true });
      MainModal.hide();
    }

    modalOkBtn.onclick = () => {
      const form = modalBodyEl.querySelector('form');
      if (form) {
        if (!form.reportValidity()) return;
        const data = Object.fromEntries(new FormData(form).entries());
        resolveAfterHide(data);
      } else {
        resolveAfterHide(true);
      }
    };

    modalBodyEl.querySelectorAll('[data-choice]').forEach(btn => {
      btn.onclick = () => {
        const val = btn.getAttribute('data-choice');
        resolveAfterHide(val);
      };
    });

    MainModal.show();
  });
}

// Always ask where to apply (Original/Result)
async function chooseSourceImageData(){
  if (!origCanvas.width) { alert("Open an image first."); return null; }

  if (!resultImageData) {
    await showFormModal({
      title: "Apply To",
      bodyHTML: `
        <p class="mb-2">Currently only the Original image is available.</p>
        <div class="alert alert-secondary py-2 mb-0">Using <strong>Original</strong>.</div>
      `,
      okText: "OK"
    });
    return octx.getImageData(0,0,origCanvas.width,origCanvas.height);
  }

  const choice = await showFormModal({
    title: "Apply To",
    bodyHTML: `
      <p class="mb-2">Where do you want to apply the operation?</p>
      <div class="d-grid gap-2">
        <button type="button" class="btn btn-outline-primary w-100" data-choice="result">Use Result (last output)</button>
        <button type="button" class="btn btn-outline-soft w-100" data-choice="original">Use Original (input)</button>
      </div>
    `,
    hideOk: true
  });

  if (choice === 'result') {
    return rctx.getImageData(0,0,resultCanvas.width,resultCanvas.height);
  }
  return octx.getImageData(0,0,origCanvas.width,origCanvas.height);
}

function putResultImageData(imgData){
  resultCanvas.width = imgData.width;
  resultCanvas.height = imgData.height;
  rctx.putImageData(imgData, 0, 0);
  resultImageData = imgData;
}

// ========= Image Ops =========
function clamp255(x){ return x<0?0:(x>255?255:x|0); }

function negative(img){
  const out = new ImageData(img.width, img.height);
  const a = img.data, b = out.data;
  for(let i=0;i<a.length;i+=4){
    b[i]=255-a[i]; b[i+1]=255-a[i+1]; b[i+2]=255-a[i+2]; b[i+3]=a[i+3];
  }
  return out;
}

function threshold(img, t=150){
  const out = new ImageData(img.width, img.height);
  const a = img.data, b = out.data;
  for(let i=0;i<a.length;i+=4){
    const g = Math.round(0.299*a[i] + 0.587*a[i+1] + 0.114*a[i+2]);
    const v = g < t ? 0 : 255;
    b[i]=v; b[i+1]=v; b[i+2]=v; b[i+3]=a[i+3];
  }
  return out;
}

function logTransform(img){
  const out = new ImageData(img.width, img.height);
  const a = img.data, b = out.data;
  const c = 255 / Math.log(1 + 255);
  for(let i=0;i<a.length;i+=4){
    b[i]   = clamp255(c * Math.log(1 + a[i]));
    b[i+1] = clamp255(c * Math.log(1 + a[i+1]));
    b[i+2] = clamp255(c * Math.log(1 + a[i+2]));
    b[i+3] = a[i+3];
  }
  return out;
}

function gammaTransform(img, gamma=2.2){
  const out = new ImageData(img.width, img.height);
  const a = img.data, b = out.data;
  const inv = 1/gamma;
  const lut = new Uint8Array(256);
  for(let i=0;i<256;i++) lut[i] = clamp255(Math.pow(i/255, inv)*255);
  for(let i=0;i<a.length;i+=4){
    b[i]=lut[a[i]]; b[i+1]=lut[a[i+1]]; b[i+2]=lut[a[i+2]]; b[i+3]=a[i+3];
  }
  return out;
}

function resizeNearest(img, newW, newH){
  const out = new ImageData(newW, newH);
  const a = img.data, b = out.data;
  const W = img.width, H = img.height;
  for(let y=0;y<newH;y++){
    const sy = Math.min(H-1, Math.floor(y * H / newH));
    for(let x=0;x<newW;x++){
      const sx = Math.min(W-1, Math.floor(x * W / newW));
      const si = (sy*W+sx)*4;
      const di = (y*newW+x)*4;
      b[di]=a[si]; b[di+1]=a[si+1]; b[di+2]=a[si+2]; b[di+3]=a[si+3];
    }
  }
  return out;
}

function convolve3x3(img, kernel, scale=1, offset=0, repeat=1){
  const W=img.width, H=img.height;
  let curr = new ImageData(new Uint8ClampedArray(img.data), W, H);
  const k = kernel.flat();
  const half = 1;

  for(let pass=0; pass<repeat; pass++){
    const src=curr.data, out=new ImageData(W,H), dst=out.data;
    for(let y=0;y<H;y++){
      for(let x=0;x<W;x++){
        let r=0,g=0,b=0;
        for(let ky=-half; ky<=half; ky++){
          const yy = Math.min(H-1, Math.max(0, y+ky));
          for(let kx=-half; kx<=half; kx++){
            const xx = Math.min(W-1, Math.max(0, x+kx));
            const kv = k[(ky+half)*3 + (kx+half)];
            const i = (yy*W + xx)*4;
            r += src[i]   * kv;
            g += src[i+1] * kv;
            b += src[i+2] * kv;
          }
        }
        const di = (y*W+x)*4;
        dst[di]   = clamp255(r*scale + offset);
        dst[di+1] = clamp255(g*scale + offset);
        dst[di+2] = clamp255(b*scale + offset);
        dst[di+3] = src[di+3];
      }
    }
    curr = out;
  }
  return curr;
}

// Kernels
const K_MEAN     = [[1,1,1],[1,1,1],[1,1,1]]; // /9
const K_WEIGHTED = [[1,2,1],[2,4,2],[1,2,1]]; // /16
const K_GAUSS    = [[1,2,1],[2,4,2],[1,2,1]]; // /16
const K_SHARPEN1 = [[0,-1,0],[-1,5,-1],[0,-1,0]];
const K_LAPLACE  = [[0,1,0],[1,-4,1],[0,1,0]];

function smooth(img, mode="weighted", strength="medium"){
  const repeat = strength==="low"?1:strength==="high"?3:2;
  if(mode==="mean")     return convolve3x3(img, K_MEAN,     1/9,  0, repeat);
  if(mode==="weighted") return convolve3x3(img, K_WEIGHTED, 1/16, 0, repeat);
  if(mode==="gaussian") return convolve3x3(img, K_GAUSS,    1/16, 0, repeat);
  return img;
}

function sharpenFirst(img, strength="medium"){
  const repeat = strength==="low"?1:strength==="high"?3:2;
  return convolve3x3(img, K_SHARPEN1, 1, 0, repeat);
}

function laplacianEdge(img){
  const out = convolve3x3(img, K_LAPLACE, 1, 0, 1);
  const d = out.data;
  for(let i=0;i<d.length;i+=4){
    d[i]   = clamp255(Math.abs(d[i]-128)+128);
    d[i+1] = clamp255(Math.abs(d[i+1]-128)+128);
    d[i+2] = clamp255(Math.abs(d[i+2]-128)+128);
  }
  return out;
}

function sharpenSecond(img, strength="medium"){
  const alpha = strength==="low"?0.2:strength==="high"?0.6:0.4;
  const lap = convolve3x3(img, K_LAPLACE, 1, 0, 1);
  const out = new ImageData(img.width, img.height);
  const a=img.data, l=lap.data, b=out.data;
  for(let i=0;i<a.length;i+=4){
    b[i]   = clamp255(a[i]   - alpha*(l[i]-128));
    b[i+1] = clamp255(a[i+1] - alpha*(l[i+1]-128));
    b[i+2] = clamp255(a[i+2] - alpha*(l[i+2]-128));
    b[i+3] = a[i+3];
  }
  return out;
}

// Histogram
function drawHistogramToCanvas(img, canvas){
  const ctx = canvas.getContext('2d');
  const w = canvas.width = 800;
  const h = canvas.height = 240;
  ctx.clearRect(0,0,w,h);

  const r = new Uint32Array(256);
  const g = new Uint32Array(256);
  const b = new Uint32Array(256);
  for(let i=0;i<img.data.length;i+=4){ r[img.data[i]]++; g[img.data[i+1]]++; b[img.data[i+2]]++; }

  const max = Math.max(maxv(r), maxv(g), maxv(b));
  const barW = Math.max(1, Math.floor(w/256));

  function maxv(arr){ let m=0; for(let i=0;i<256;i++) if(arr[i]>m) m=arr[i]; return m; }
  function draw(arr, color){
    ctx.fillStyle = color;
    for(let i=0;i<256;i++){
      const bh = Math.round((arr[i]/max)*(h-20));
      ctx.fillRect(i*barW, h-bh, barW, bh);
    }
  }
  ctx.fillStyle = 'rgba(255,255,255,0.06)';
  for(let i=0;i<10;i++){ const y = Math.round(i*h/10); ctx.fillRect(0,y,w,1); }

  draw(r, "rgba(255,95,95,0.9)");
  draw(g, "rgba(90,235,130,0.9)");
  draw(b, "rgba(95,150,255,0.9)");
}

// ========= Wiring =========
fileInput.addEventListener('change', async (e)=>{
  const file = e.target.files?.[0];
  if(!file) return;
  try {
    await loadImageToCanvas(file);
    setStatus(`Opened: ${file.name}`);
  } catch {
    alert("Failed to load image.");
  }
});

saveBtn.addEventListener('click', ()=>{
  if(!resultCanvas.width || !resultImageData){
    alert("No processed image yet.");
    return;
  }
  const url = resultCanvas.toDataURL('image/png');
  const a = document.createElement('a');
  a.href = url; a.download = 'result.png';
  a.click();
});

resetBtn.addEventListener('click', ()=>{
  if (!origCanvas.width) { setStatus("Nothing to reset."); return; }
  rctx.clearRect(0,0,resultCanvas.width,resultCanvas.height);
  resultImageData = null;
  setStatus("Result cleared.");
});

// Action buttons
document.querySelectorAll('.action').forEach(btn=>{
  btn.addEventListener('click', async ()=>{
    if(!origCanvas.width){ alert("Open an image first."); return; }
    const action = btn.dataset.action;

    try {
      // 1) Params (no spinner during input)
      let params = {};
      if(action==='threshold'){
        const data = await showFormModal({
          title: "Threshold",
          bodyHTML: `
            <form class="vstack gap-2">
              <label class="form-label mb-0">Value (0–255)</label>
              <input name="t" type="number" min="0" max="255" value="150" class="form-control" required />
            </form>`,
        });
        params.t = Math.max(0, Math.min(255, parseInt(data.t||'150',10)));
      } else if(action==='smoothing'){
        const data = await showFormModal({
          title: "Smoothing",
          bodyHTML: `
            <form class="vstack gap-3">
              <div>
                <div class="form-label mb-1 fw-700">Filter</div>
                <div class="d-flex flex-wrap gap-3">
                  <div class="form-check"><input class="form-check-input" type="radio" name="mode" value="mean" id="m1"><label class="form-check-label" for="m1">Mean (3×3)</label></div>
                  <div class="form-check"><input class="form-check-input" type="radio" name="mode" value="weighted" id="m2" checked><label class="form-check-label" for="m2">Weighted (1-2-1)</label></div>
                  <div class="form-check"><input class="form-check-input" type="radio" name="mode" value="gaussian" id="m3"><label class="form-check-label" for="m3">Gaussian (1-2-1)</label></div>
                </div>
              </div>
              <div>
                <div class="form-label mb-1 fw-700">Strength</div>
                <div class="d-flex flex-wrap gap-3">
                  <div class="form-check"><input class="form-check-input" type="radio" name="str" value="low" id="s1"><label class="form-check-label" for="s1">Low</label></div>
                  <div class="form-check"><input class="form-check-input" type="radio" name="str" value="medium" id="s2" checked><label class="form-check-label" for="s2">Medium</label></div>
                  <div class="form-check"><input class="form-check-input" type="radio" name="str" value="high" id="s3"><label class="form-check-label" for="s3">High</label></div>
                </div>
              </div>
            </form>`
        });
        params.mode = data.mode || 'weighted';
        params.str  = data.str  || 'medium';
      } else if(action==='sharpen'){
        const data = await showFormModal({
          title: "Sharpening",
          bodyHTML: `
            <form class="vstack gap-3">
              <div>
                <div class="form-label mb-1 fw-700">Method</div>
                <div class="d-flex flex-wrap gap-3">
                  <div class="form-check"><input class="form-check-input" type="radio" name="kind" value="first" id="k1"><label class="form-check-label" for="k1">First-order derivative</label></div>
                  <div class="form-check"><input class="form-check-input" type="radio" name="kind" value="second" id="k2" checked><label class="form-check-label" for="k2">Second-order derivative</label></div>
                </div>
              </div>
              <div>
                <div class="form-label mb-1 fw-700">Strength</div>
                <div class="d-flex flex-wrap gap-3">
                  <div class="form-check"><input class="form-check-input" type="radio" name="str" value="low" id="ss1"><label class="form-check-label" for="ss1">Low</label></div>
                  <div class="form-check"><input class="form-check-input" type="radio" name="str" value="medium" id="ss2" checked><label class="form-check-label" for="ss2">Medium</label></div>
                  <div class="form-check"><input class="form-check-input" type="radio" name="str" value="high" id="ss3"><label class="form-check-label" for="ss3">High</label></div>
                </div>
              </div>
            </form>`
        });
        params.kind = data.kind || 'second';
        params.str  = data.str  || 'medium';
      } else if(action==='gamma'){
        const data = await showFormModal({
          title: "Gamma",
          bodyHTML: `
            <form class="vstack gap-2">
              <label class="form-label mb-0">Gamma (>0, e.g. 2.2)</label>
              <input name="g" type="number" step="0.01" min="0.01" value="2.2" class="form-control" required />
            </form>`
        });
        params.g = Math.max(0.01, parseFloat(data.g||'2.2'));
      } else if(action==='resize'){
        const baseW = origCanvas.width, baseH = origCanvas.height;
        const data = await showFormModal({
          title: "Resize (Nearest)",
          bodyHTML: `
            <form class="row g-3 align-items-end">
              <div class="col-6">
                <label class="form-label mb-0">Width</label>
                <input name="w" type="number" min="1" max="10000" value="${baseW}" class="form-control" required />
              </div>
              <div class="col-6">
                <label class="form-label mb-0">Height</label>
                <input name="h" type="number" min="1" max="10000" value="${baseH}" class="form-control" required />
              </div>
            </form>`
        });
        params.w = Math.min(10000, Math.max(1, parseInt(data.w||baseW,10)));
        params.h = Math.min(10000, Math.max(1, parseInt(data.h||baseH,10)));
      } else if(action==='histogram'){
        await showFormModal({
          title: "Histogram",
          bodyHTML: `
            <div class="text-muted small mb-2">RGB intensity distribution of the current image.</div>
            <canvas id="histCanvas" width="800" height="240" class="w-100 rounded-3 border border-soft"></canvas>`,
          okText: "Close",
          onShown: () => {
            const base = resultImageData ? resultImageData : octx.getImageData(0,0,origCanvas.width,origCanvas.height);
            const hcv = document.getElementById('histCanvas');
            if(hcv) drawHistogramToCanvas(base, hcv);
          }
        });
        return;
      }

      // 2) Always choose source (now guaranteed to show after previous modal closes)
      const src = await chooseSourceImageData();
      if(!src) return;

      // 3) Compute with spinner
      const out = await runWithSpinner(async ()=>{
        if(action==='negative') return negative(src);
        if(action==='threshold')return threshold(src, params.t);
        if(action==='smoothing')return smooth(src, params.mode, params.str);
        if(action==='sharpen')  return (params.kind==='first' ? sharpenFirst(src, params.str) : sharpenSecond(src, params.str));
        if(action==='laplacian')return laplacianEdge(src);
        if(action==='log')      return logTransform(src);
        if(action==='gamma')    return gammaTransform(src, params.g);
        if(action==='resize')   return resizeNearest(src, params.w, params.h);
        return src;
      });

      putResultImageData(out);
      setStatus(`Applied ${action}`);
    } catch (err){
      console.error(err);
      alert("Operation failed.");
    }
  });
});

// Init
setStatus("Ready");
