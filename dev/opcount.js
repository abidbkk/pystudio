// Counts Drive operations per request for a given Code.gs (run in a page that has gas-mock.js loaded).
window.opCount = async function (codeUrl) {
  (0, eval)(await (await fetch('/dev/gas-mock.js', { cache: 'no-store' })).text());
  (0, eval)(await (await fetch(codeUrl, { cache: 'no-store' })).text());
  let ops = 0;
  const wrapAll = () => {
    for (const o of [...Object.values(GAS.files), ...Object.values(GAS.folders)]) {
      if (o._wrapped) continue; o._wrapped = true;
      for (const k of Object.keys(o)) if (typeof o[k] === "function" && !k.startsWith("_") && k !== "getId") {
        const fn = o[k]; o[k] = function (...a) { ops++; return fn.apply(this, a); };
      }
    }
  };
  for (const k of ['getFileById', 'getFolderById']) { const fn = DriveApp[k]; DriveApp[k] = (...a) => { ops++; return fn(...a); }; }
  const measure = f => { wrapAll(); ops = 0; const r = f(); wrapAll(); return [ops, r]; };
  const clone = x => JSON.parse(JSON.stringify(x));

  // Sara has 5 files, one of them in a folder
  GAS.as = 'sara@ics.edu.jo';
  const ids = [];
  for (let i = 1; i <= 5; i++) {
    const r = syncFiles(null, [{ key: 'k', id: null, base: null, name: `file${i}.py`, folder: i === 5 ? 'Sorting' : '', content: `print(${i})`, bps: [] }], []);
    ids.push(r.saved.k.id);
  }
  // PyStudio opens her files
  const [openOps, first] = measure(() => clone(listFiles(null, {}, {})));
  const known = {}; first.files.forEach(f => known[f.id] = f.v);
  // she types and it saves (twice)
  const save = n => syncFiles(null, [{ key: 'k', id: ids[0], base: null, name: 'file1.py', folder: '', content: `print('edit ${n}')`, bps: [] }], []);
  const [save1Ops] = measure(() => save(1));
  const [save2Ops] = measure(() => save(2));
  // update check right after her own save (folder changed)
  const [pollChangedOps, afterSave] = measure(() => clone(listFiles(null, known, {}, first.token, {})));
  afterSave.files.forEach(f => known[f.id] = f.v);
  // update check when nothing has changed
  const [pollQuietOps, quiet] = measure(() => clone(listFiles(null, known, {}, afterSave.token, {})));
  return { open: openOps, save1: save1Ops, save2: save2Ops, checkAfterChange: pollChangedOps, checkNothingChanged: pollQuietOps, quietAnswer: quiet.unchanged ? 'unchanged' : 'full list' };
};
