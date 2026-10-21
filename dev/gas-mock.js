// In-memory stand-ins for the Apps Script services Code.gs uses, so the real server code
// can run in the browser for testing. Not deployed anywhere.
(() => {
  let nid = 0;
  const id = p => p + (++nid);
  const iter = arr => { let i = 0; return { hasNext: () => i < arr.length, next: () => arr[i++] }; };
  const props = {}, cache = {};
  const files = {}, folders = {};

  function mkFolder(name, parent) {
    const f = { _id: id("fo"), _name: name, _parent: parent, _trashed: false,
      getId() { return this._id; }, getName() { return this._name; }, isTrashed() { return this._trashed || (this._parent && folders[this._parent]._trashed); },
      getUrl() { return "https://drive/" + this._id; },
      setName(n) { this._name = n; return this; }, setTrashed(t) { this._trashed = t; return this; },
      getParents() { return iter(this._parent ? [folders[this._parent]] : []); },
      getFolders() { return iter(Object.values(folders).filter(x => x._parent === this._id)); },
      createFolder(n) { return mkFolder(n, this._id); },
      getFoldersByName(n) { return iter(Object.values(folders).filter(x => x._parent === this._id && x._name === n && !x._trashed)); },
      createFile(n, c) { return mkFile(n, c, this._id); },
      getFiles() { return iter(Object.values(files).filter(x => x._parent === this._id)); },
      getFilesByName(n) { return iter(Object.values(files).filter(x => x._parent === this._id && x._name === n)); },
    };
    folders[f._id] = f; return f;
  }
  function mkFile(name, content, parent) {
    const f = { _id: id("fi"), _name: name, _content: content, _desc: "", _parent: parent, _trashed: false,
      getId() { return this._id; }, getName() { return this._name; }, setName(n) { this._name = n; return this; },
      getDescription() { return this._desc; }, setDescription(d) { this._desc = d; return this; },
      setContent(c) { this._content = c; return this; },
      getBlob() { const c = this._content; return { getDataAsString: () => c }; },
      isTrashed() { return this._trashed || folders[this._parent].isTrashed(); }, setTrashed(t) { this._trashed = t; return this; },
      getParents() { return iter([folders[this._parent]]); },
      moveTo(fo) { this._parent = fo.getId(); },
    };
    files[f._id] = f; return f;
  }

  const sheet = {
    Students: [["Class", "Student name", "Email", "Last active"],
      ["9A", "Sara Ahmad", "sara@ics.edu.jo", ""],
      ["9A", "Omar Khalil", "omar@ics.edu.jo", ""],
      ["10B", "Lina Haddad", "lina@ics.edu.jo", ""]],
    Teachers: [["Email", "Name"]],
  };
  const ss = { getSheetByName: n => ({
    getDataRange: () => ({ getValues: () => sheet[n].map(r => r.slice()) }),
    getRange: (row, col) => ({ setValue: v => { sheet[n][row - 1][col - 1] = v; } }),
  }) };

  window.GAS = { sheet, files, folders, as: "a.khan@ics.edu.jo" };
  window.PropertiesService = { getScriptProperties: () => ({ getProperty: k => props[k] ?? null, setProperty: (k, v) => { props[k] = v; },
    getProperties: () => ({ ...props }), deleteProperty: k => { delete props[k]; } }) };
  window.CacheService = { getScriptCache: () => ({ get: k => cache[k] ?? null, put: (k, v) => { cache[k] = v; }, putAll: m => { Object.assign(cache, m); }, remove: k => { delete cache[k]; }, removeAll: ks => ks.forEach(k => delete cache[k]) }) };
  window.Utilities = { getUuid: () => "u" + Math.random().toString(36).slice(2) };
  window.GAS_CACHE = cache;
  window.Session = { getActiveUser: () => ({ getEmail: () => GAS.as }), getEffectiveUser: () => ({ getEmail: () => "a.khan@ics.edu.jo" }) };
  window.LockService = { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) };
  window.MimeType = { PLAIN_TEXT: "text/plain" };
  window.SpreadsheetApp = { openById: () => ss };
  window.DriveApp = {
    getFolderById: i => { if (!folders[i]) throw new Error("no folder"); return folders[i]; },
    getFileById: i => { if (!files[i]) throw new Error("no file"); return files[i]; },
    createFolder: n => mkFolder(n, null),
  };
  props.SHEET = "sheet1";
  props.ROOT = mkFolder("PyStudio files", null).getId();
})();
