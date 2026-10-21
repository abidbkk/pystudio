/**
 * PyStudio server (Google Apps Script).
 *
 * - Deployed as a web app: Execute as "Me", access "Anyone within ics.edu.jo".
 * - Students and classes are listed in the "PyStudio – Classes" spreadsheet that setup() creates.
 * - Each person's files live in their own Drive folder under "PyStudio files" (owned by you).
 * - Who is calling is always taken from their Google sign-in (Session), never from the page.
 *
 * See SETUP.md for installation steps.
 */

const MAX_FILE_CHARS = 200000;
const MAX_FILES = 200;
const PROPS = PropertiesService.getScriptProperties();

// ---------------------------------------------------------------- web app

function doGet(e) {
  // <exec link>?page=loadtest opens the load-test page (teachers only, see loadtest.html)
  if (e && e.parameter && e.parameter.page === 'loadtest') {
    if (me_().role !== 'teacher') return HtmlService.createHtmlOutput('Teachers only.');
    return HtmlService.createHtmlOutputFromFile('loadtest').setTitle('PyStudio load test');
  }
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('PyStudio')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ---------------------------------------------------------------- one-time setup

/** Run this once from the editor (select "setup" and click Run). Safe to run again. */
function setup() {
  let ss = null;
  const sheetId = PROPS.getProperty('SHEET');
  if (sheetId) { try { ss = SpreadsheetApp.openById(sheetId); } catch (e) { ss = null; } }
  if (!ss) {
    ss = SpreadsheetApp.create('PyStudio – Classes');
    const st = ss.getSheets()[0].setName('Students');
    st.getRange(1, 1, 1, 4).setValues([['Class', 'Student name', 'Email', 'Last active (automatic)']]).setFontWeight('bold');
    st.getRange(2, 1, 2, 3).setValues([['9A', 'Example Student', 'student@ics.edu.jo'], ['9A', '', '']]);
    st.setFrozenRows(1);
    st.setColumnWidths(1, 1, 80); st.setColumnWidths(2, 2, 220); st.setColumnWidth(4, 180);
    const tt = ss.insertSheet('Teachers');
    tt.getRange(1, 1, 1, 2).setValues([['Email', 'Name']]).setFontWeight('bold');
    tt.getRange(2, 1).setNote('You (the owner of this script) are always a teacher. Add other teachers here.');
    tt.setFrozenRows(1); tt.setColumnWidth(1, 240);
    PROPS.setProperty('SHEET', ss.getId());
  }
  const root = rootFolder_();
  DriveApp.getFileById(ss.getId()).moveTo(root);
  Logger.log('Class list: ' + ss.getUrl());
  Logger.log('Student files folder: ' + root.getUrl());
}

/**
 * Copies the Google Classroom courses you tick into PyStudio's class list.
 * Needs the "Google Classroom API" service (Services + in the left panel). Safe to run again.
 *
 * 1. Lists all your active Classroom courses in the Courses tab. New courses start unticked;
 *    your ticks and "Name in PyStudio" are kept.
 * 2. Replaces the Students rows of Classroom classes with the current rosters of the ticked
 *    courses (unticked ones are removed). Classes you typed in yourself are kept, and so is
 *    "Last active".
 * 3. Adds co-teachers of ticked courses to the Teachers tab (nobody is removed).
 */
function importFromClassroom() {
  if (typeof Classroom === 'undefined') {
    throw new Error('Add the Google Classroom API first: click + next to "Services" in the left panel, choose "Google Classroom API", then Add.');
  }
  const ss = SpreadsheetApp.openById(PROPS.getProperty('SHEET'));
  const owner = Session.getEffectiveUser().getEmail().toLowerCase();
  const courses = pageAll_(t => Classroom.Courses.list({ teacherId: 'me', courseStates: ['ACTIVE'], pageToken: t }), 'courses');
  if (!courses.length) { Logger.log('No active Google Classroom classes found where you are a teacher.'); return; }

  // Default class name: the course name, plus the section when two courses share a name.
  const nameCount = {};
  courses.forEach(c => { nameCount[c.name] = (nameCount[c.name] || 0) + 1; });
  const defaultName = c => (nameCount[c.name] > 1 && c.section ? `${c.name} – ${c.section}` : c.name).trim();

  // 1. Courses tab
  const ct = coursesSheet_(ss);
  const prev = {};
  ct.getDataRange().getValues().slice(1).forEach(r => {
    const id = String(r[4] || '').trim();
    if (id) prev[id] = { use: r[0] === true, name: String(r[3] || '').trim() };
  });
  const crow = courses.map(c => [prev[c.id] ? prev[c.id].use : false, c.name, c.section || '', prev[c.id] ? prev[c.id].name : '', c.id]);
  crow.sort((a, b) => String(a[1]).localeCompare(String(b[1])) || String(a[2]).localeCompare(String(b[2])));
  if (ct.getLastRow() > 1) ct.getRange(2, 1, ct.getLastRow() - 1, 5).clearContent().removeCheckboxes();
  ct.getRange(2, 1, crow.length, 5).setValues(crow);
  ct.getRange(2, 1, crow.length, 1).insertCheckboxes();
  const byId = {};
  courses.forEach(c => { byId[c.id] = c; });
  const picked = crow.filter(r => r[0] === true).map(r => ({ course: byId[r[4]], cls: r[3] || defaultName(byId[r[4]]) }));

  // 2. Students tab. "Managed" classes are ones that came from Classroom (now or last time).
  const managed = new Set(JSON.parse(PROPS.getProperty('CLASSROOM_CLASSES') || '[]'));
  courses.forEach(c => managed.add(defaultName(c)));
  picked.forEach(p => managed.add(p.cls));
  const st = ss.getSheetByName('Students');
  const old = st.getDataRange().getValues().slice(1);
  const lastBy = {};
  old.forEach(r => { const e = String(r[2] || '').trim().toLowerCase(); if (e && r[3] && !lastBy[e]) lastBy[e] = r[3]; });
  const rows = old.filter(r => String(r[0] || '').trim() && !managed.has(String(r[0]).trim())
    && String(r[2] || '').includes('@') && String(r[2]).trim() !== 'student@ics.edu.jo');   // drop setup()'s example row

  const coTeachers = {};
  let noEmail = 0;
  const summary = [];
  picked.forEach(({ course: c, cls }) => {
    let count = 0;
    pageAll_(t => Classroom.Courses.Students.list(c.id, { pageToken: t }), 'students').forEach(s => {
      const email = String((s.profile && s.profile.emailAddress) || '').toLowerCase();
      if (!email) { noEmail++; return; }
      rows.push([cls, (s.profile.name && s.profile.name.fullName) || email, email, lastBy[email] || '']);
      count++;
    });
    pageAll_(t => Classroom.Courses.Teachers.list(c.id, { pageToken: t }), 'teachers').forEach(t => {
      const email = String((t.profile && t.profile.emailAddress) || '').toLowerCase();
      if (email && email !== owner) coTeachers[email] = (t.profile.name && t.profile.name.fullName) || email;
    });
    summary.push(`${cls}: ${count} student(s)`);
  });

  rows.sort((a, b) => String(a[0]).localeCompare(String(b[0])) || String(a[1]).localeCompare(String(b[1])));
  if (st.getLastRow() > 1) st.getRange(2, 1, st.getLastRow() - 1, 4).clearContent();
  if (rows.length) st.getRange(2, 1, rows.length, 4).setValues(rows);
  PROPS.setProperty('CLASSROOM_CLASSES', JSON.stringify(picked.map(p => p.cls)));

  // 3. Teachers tab
  const tt = ss.getSheetByName('Teachers');
  const have = new Set(tt.getDataRange().getValues().slice(1).map(r => String(r[0] || '').trim().toLowerCase()));
  const add = Object.keys(coTeachers).filter(e => !have.has(e)).map(e => [e, coTeachers[e]]);
  if (add.length) tt.getRange(tt.getLastRow() + 1, 1, add.length, 2).setValues(add);

  CacheService.getScriptCache().remove('roster');
  if (!picked.length) {
    Logger.log(`Found ${courses.length} Classroom course(s) and listed them in the Courses tab.\n` +
      'Tick the ones you want in PyStudio, then run importFromClassroom again.');
  } else {
    Logger.log(`Imported ${picked.length} of ${courses.length} course(s):\n  ` + summary.join('\n  '));
    const untickedNew = crow.filter(r => r[0] !== true && !prev[r[4]]).length;
    if (untickedNew) Logger.log(`${untickedNew} new course(s) were added to the Courses tab unticked.`);
  }
  if (add.length) Logger.log(`Added ${add.length} co-teacher(s): ` + add.map(a => a[1]).join(', '));
  if (noEmail) Logger.log(`⚠ ${noEmail} student(s) were skipped because Classroom did not share their email address.`);
  if (picked.length) prepareFolders();
  Logger.log('Class list: ' + ss.getUrl());
}

/**
 * Creates the Drive folder of every student on the class list who doesn't have one yet, so a
 * whole class logging in for the first time doesn't have to wait for folders to be made.
 * Runs automatically after importFromClassroom; safe to run again (from the editor) at any time.
 */
function prepareFolders() {
  CacheService.getScriptCache().remove('roster');
  const students = roster_().students;
  let made = 0;
  Object.keys(students).forEach(email => {
    if (PROPS.getProperty('f:' + email)) return;
    folderFor_(email);
    made++;
  });
  Logger.log(made ? `Created ${made} student folder(s).` : 'Every student already has a folder.');
  return made;
}

function coursesSheet_(ss) {
  let ct = ss.getSheetByName('Courses');
  if (ct) return ct;
  ct = ss.insertSheet('Courses', 0);
  ct.getRange(1, 1, 1, 5).setValues([['Use in PyStudio', 'Classroom course', 'Section', 'Name in PyStudio (optional)', "Course ID (don't edit)"]]).setFontWeight('bold');
  ct.setFrozenRows(1);
  ct.setColumnWidth(1, 120); ct.setColumnWidth(2, 240); ct.setColumnWidth(3, 100); ct.setColumnWidth(4, 200); ct.setColumnWidth(5, 160);
  ct.getRange('E:E').setFontColor('#999999');
  return ct;
}

function pageAll_(fetchPage, key) {
  let out = [], token;
  do {
    const r = fetchPage(token) || {};
    out = out.concat(r[key] || []);
    token = r.nextPageToken;
  } while (token);
  return out;
}

function rootFolder_() {
  const id = PROPS.getProperty('ROOT');
  if (id) { try { const f = DriveApp.getFolderById(id); if (!f.isTrashed()) return f; } catch (e) {} }
  const f = DriveApp.createFolder('PyStudio files');
  PROPS.setProperty('ROOT', f.getId());
  return f;
}

// ---------------------------------------------------------------- people

function roster_() {
  const cache = CacheService.getScriptCache();
  const hit = cache.get('roster');
  if (hit) return JSON.parse(hit);
  const ss = SpreadsheetApp.openById(PROPS.getProperty('SHEET'));
  // A student may appear on several rows (one per class); the first row holds "Last active".
  const students = {};
  ss.getSheetByName('Students').getDataRange().getValues().slice(1).forEach((r, i) => {
    const email = String(r[2] || '').trim().toLowerCase();
    if (!email || !email.includes('@')) return;
    const cls = String(r[0] || '').trim() || 'No class';
    if (students[email]) { if (!students[email].classes.includes(cls)) students[email].classes.push(cls); return; }
    students[email] = {
      classes: [cls],
      name: String(r[1] || '').trim() || email,
      row: i + 2,
      last: r[3] instanceof Date ? r[3].getTime() : null,
    };
  });
  const teachers = {};
  ss.getSheetByName('Teachers').getDataRange().getValues().slice(1).forEach(r => {
    const email = String(r[0] || '').trim().toLowerCase();
    if (email) teachers[email] = String(r[1] || '').trim() || email;
  });
  const owner = Session.getEffectiveUser().getEmail().toLowerCase();
  if (!teachers[owner]) teachers[owner] = 'Teacher';
  const data = { students, teachers };
  cache.put('roster', JSON.stringify(data), 60);
  return data;
}

function me_() {
  const email = (Session.getActiveUser().getEmail() || '').toLowerCase();
  if (!email) throw new Error('Not signed in');
  const r = roster_();
  if (r.teachers[email]) return { email, role: 'teacher', name: r.teachers[email] };
  if (r.students[email]) return { email, role: 'student', name: r.students[email].name, cls: r.students[email].classes.join(', ') };
  return { email, role: 'none', name: email };
}

/**
 * Whose files may `me` open? Their own; teachers may open anyone on the lists, and a class's
 * shared "Class files" (target "class:<name>"). Students read class files through listFiles().
 */
function target_(me, target) {
  if (me.role === 'none') throw new Error('Your account is not on a class list yet. Ask your teacher to add you.');
  if (/^loadtest:\d+$/.test(String(target || ''))) {      // pretend students for loadtest.html
    if (me.role !== 'teacher') throw new Error('Teachers only.');
    return String(target);
  }
  const cls = classOf_(target);
  if (cls) {
    if (me.role !== 'teacher') throw new Error('Only teachers can change class files.');
    if (!classExists_(cls)) throw new Error('There is no class called ' + cls + '.');
    return 'class:' + cls;
  }
  target = String(target || me.email).toLowerCase();
  if (target === me.email) return target;
  const r = roster_();
  if (me.role === 'teacher' && (r.students[target] || r.teachers[target])) return target;
  throw new Error('You do not have access to those files.');
}

function classOf_(target) {
  const m = /^class:(.+)$/.exec(String(target || ''));
  return m ? m[1] : null;
}

function classExists_(cls) {
  const r = roster_();
  return Object.keys(r.students).some(e => r.students[e].classes.includes(cls));
}

/** A class's shared files folder, or null if the teacher hasn't added any yet. */
function classFolder_(cls) {
  const id = PROPS.getProperty('f:class:' + cls);
  if (!id) return null;
  try { const f = DriveApp.getFolderById(id); return f.isTrashed() ? null : f; } catch (e) { return null; }
}

/** The folder id for `email` without asking Drive when it is already known. */
function folderIdFor_(email) {
  return PROPS.getProperty('f:' + email) || folderFor_(email).getId();
}

/** The id of `rootFolder()`'s subfolder `name`, remembered for a few minutes. */
function subfolderId_(rootFolder, rootId, name) {
  name = cleanFolder_(name);
  if (!name) return rootId;
  const cache = CacheService.getScriptCache(), key = 'sd:' + rootId + ':' + name;
  let id = cache.get(key);
  if (!id) { id = subfolder_(rootFolder(), name, true).getId(); cache.put(key, id, REMEMBER_S); }
  return id;
}

/** `email` is a person's email, or "class:<name>" for a class's shared files. */
function folderFor_(email) {
  const key = 'f:' + email;
  const id = PROPS.getProperty(key);
  if (id) { try { const f = DriveApp.getFolderById(id); if (!f.isTrashed()) return f; } catch (e) {} }
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const again = PROPS.getProperty(key);
    if (again && again !== id) return DriveApp.getFolderById(again);
    const cls = classOf_(email);
    let folder;
    if (/^loadtest:\d+$/.test(email)) {
      folder = childFolder_(rootFolder_(), '_loadtest').createFolder('student ' + email.split(':')[1]);
    } else if (cls) {
      folder = childFolder_(rootFolder_(), cls).createFolder('_Class files (students can see these)');
    } else {
      const s = roster_().students[email];
      folder = childFolder_(rootFolder_(), s ? s.classes[0] : 'Teachers').createFolder(s ? `${s.name} (${email})` : email);
    }
    PROPS.setProperty(key, folder.getId());
    return folder;
  } finally {
    lock.releaseLock();
  }
}

function childFolder_(parent, name) {
  const it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

function touch_(me) {
  if (me.role !== 'student') return;
  const cache = CacheService.getScriptCache();
  if (cache.get('seen:' + me.email)) return;
  cache.put('seen:' + me.email, '1', 300);
  const s = roster_().students[me.email];
  SpreadsheetApp.openById(PROPS.getProperty('SHEET')).getSheetByName('Students').getRange(s.row, 4).setValue(new Date());
}

// ---------------------------------------------------------------- files

function meta_(file) {
  return parseMeta_(file.getDescription());
}

function parseMeta_(description) {
  try { const m = JSON.parse(description || '{}'); return { bps: Array.isArray(m.bps) ? m.bps : [], v: +m.v || 0, by: m.by || '' }; }
  catch (e) { return { bps: [], v: 0, by: '' }; }
}

// ---------------------------------------------------------------- remembered facts
// To keep requests fast the server remembers, for 5 minutes, a "changed" code per folder and
// where each file lives. Changes made in PyStudio update these at once; changes made directly
// in Google Drive are picked up when they expire (within about 5 minutes).

const REMEMBER_S = 300;

/** The folder's current "changed" code (a new one is made if none is remembered). */
function folderToken_(folderId) {
  const cache = CacheService.getScriptCache(), key = 'ft:' + folderId;
  let t = cache.get(key);
  if (!t) { t = Utilities.getUuid(); cache.put(key, t, REMEMBER_S); }
  return t;
}

/** Call after anything in the folder changes, so the next check lists it again. */
function folderChanged_(folderId) {
  CacheService.getScriptCache().put('ft:' + folderId, Utilities.getUuid(), REMEMBER_S);
}

/** {root, dir, v, name} for a file: which person/class folder it belongs to, its subfolder, version and name. */
function fileInfo_(id) {
  const raw = CacheService.getScriptCache().get('fi:' + id);
  try { return raw ? JSON.parse(raw) : null; } catch (e) { return null; }
}
function rememberFiles_(map) {   // id -> {root, dir, v, name}
  const out = {};
  Object.keys(map).forEach(id => { out['fi:' + id] = JSON.stringify(map[id]); });
  if (Object.keys(out).length) CacheService.getScriptCache().putAll(out, REMEMBER_S);
}

/** The file `id` if it is in `folder` or one of its (one level deep) subfolders. */
function ownFile_(folder, id) {
  try {
    const f = DriveApp.getFileById(id);
    if (f.isTrashed()) return null;
    const ps = f.getParents();
    while (ps.hasNext()) {
      const p = ps.next();
      if (p.getId() === folder.getId()) return f;
      const gs = p.getParents();
      while (gs.hasNext()) if (gs.next().getId() === folder.getId() && !p.isTrashed()) return f;
    }
  } catch (e) {}
  return null;
}

function cleanFolder_(name) {
  return String(name || '').replace(/[\\/:*?"<>|\u0000-\u001f]/g, '').trim().slice(0, 40);
}

/** The subfolder `name` of `folder` ("" means `folder` itself), created if `create`. */
function subfolder_(folder, name, create) {
  name = cleanFolder_(name);
  if (!name) return folder;
  const it = folder.getFoldersByName(name);
  while (it.hasNext()) { const f = it.next(); if (!f.isTrashed()) return f; }
  return create ? folder.createFolder(name) : null;
}

function cleanName_(name) {
  name = String(name || '').replace(/[\\/:*?"<>|\u0000-\u001f]/g, '').trim().slice(0, 100);
  return name || 'untitled.py';
}

// ---------------------------------------------------------------- API (called from the page)

function whoAmI() {
  const me = me_();
  touch_(me);
  return me;
}

/**
 * Lists the files of `target` (default: yourself). `known` maps file id -> version the page
 * already has; content is only sent for files that are new or changed.
 * A student listing their own files also gets their classes' shared files (`classKnown` works like `known`).
 */
function listFiles(target, known, classKnown, since, classSince) {
  // `since` / `classSince[cls]` are the "changed" codes the page got last time: if the folder
  // hasn't changed since, the answer is just { unchanged: true } without reading Drive.
  const me = me_();
  const email = target_(me, target);
  const token = folderToken_(folderIdFor_(email));     // read before listing (see folderChanged_)
  const res = since && since === token ? { unchanged: true } : filesIn_(folderFor_(email), known || {});
  res.token = token;
  if (email === me.email && me.role === 'student') {
    classSince = classSince || {};
    res.classes = roster_().students[me.email].classes.map(cls => {
      const cid = PROPS.getProperty('f:class:' + cls);
      if (!cid) return { cls, files: [] };                // the teacher hasn't added class files yet
      const t = folderToken_(cid);
      if (classSince[cls] && classSince[cls] === t) return { cls, unchanged: true, token: t };
      const cf = classFolder_(cls);
      return cf ? { cls, files: filesIn_(cf, classKnown || {}).files, token: t } : { cls, files: [] };
    });
  }
  return res;
}

/** Files in `folder` (folder: "") and in each of its subfolders (folder: subfolder name). */
function filesIn_(folder, known) {
  const out = [], folders = [], seen = {}, rootId = folder.getId();
  const add = (dir, name) => {
    const dirId = dir.getId();
    const it = dir.getFiles();
    while (it.hasNext()) {
      const f = it.next();
      if (f.isTrashed()) continue;
      const m = meta_(f);
      const e = { id: f.getId(), name: f.getName(), folder: name, v: m.v, by: m.by };
      if (known[e.id] !== m.v) { e.content = f.getBlob().getDataAsString('UTF-8'); e.bps = m.bps; }
      out.push(e);
      seen[e.id] = { root: rootId, dir: dirId, v: m.v, name: e.name };
    }
  };
  add(folder, '');
  const it = folder.getFolders();
  while (it.hasNext()) {
    const d = it.next();
    if (d.isTrashed()) continue;
    folders.push(d.getName());
    add(d, d.getName());
  }
  rememberFiles_(seen);
  return { files: out, folders };
}

/** Teachers only: copies a file into a class's shared files, replacing one with the same name. */
function shareToClass(cls, name, content, bps, inFolder) {
  const me = me_();
  const classRoot = folderFor_(target_(me, 'class:' + cls));
  const folder = subfolder_(classRoot, inFolder || '', true);
  name = cleanName_(name);
  content = String(content == null ? '' : content);
  if (content.length > MAX_FILE_CHARS) throw new Error(`${name} is too large to share.`);
  bps = Array.isArray(bps) ? bps.filter(n => typeof n === 'number').slice(0, 500) : [];
  let f = null;
  const it = folder.getFilesByName(name);
  while (it.hasNext()) { const x = it.next(); if (!x.isTrashed()) { f = x; break; } }
  let v = 1;
  if (f) { v = meta_(f).v + 1; f.setContent(content); }
  else f = folder.createFile(name, content, MimeType.PLAIN_TEXT);
  f.setDescription(JSON.stringify({ bps, v, by: me.email }));
  folderChanged_(classRoot.getId());
  return { id: f.getId(), v, replaced: v > 1 };
}

/**
 * Saves changes to `target`'s files.
 * upserts: [{key, id|null, base|null, name, folder, content, bps}] — `base` is the version the edit
 * started from; `folder` is a subfolder name or "".
 * If someone else saved the file since `base`, it is returned in `conflicts` instead of overwritten.
 */
function syncFiles(target, upserts, deletes) {
  const me = me_();
  const email = target_(me, target);
  // Only fetch the Folder from Drive when it is really needed (new files, moves, deletes).
  const rootId = folderIdFor_(email);
  let root = null;
  const rootFolder = () => root || (root = folderFor_(email));
  const folderById = id => id === rootId ? rootFolder() : DriveApp.getFolderById(id);
  const saved = {}, conflicts = [], remembered = {};
  (upserts || []).slice(0, MAX_FILES).forEach(u => {
    const content = String(u.content == null ? '' : u.content);
    if (content.length > MAX_FILE_CHARS) throw new Error(`${u.name} is too large to save.`);
    const name = cleanName_(u.name);
    const bps = Array.isArray(u.bps) ? u.bps.filter(n => typeof n === 'number').slice(0, 500) : [];
    const dirId = subfolderId_(rootFolder, rootId, u.folder);
    // Already known to belong to this person/class (checked in the last few minutes)? Then go
    // straight to the file and skip the folder and parent checks.
    const info = u.id ? fileInfo_(u.id) : null;
    const knownHere = !!info && info.root === rootId;
    let f = null;
    if (u.id && knownHere) {
      try { f = DriveApp.getFileById(u.id); } catch (e) { f = null; }
    } else if (u.id) {
      f = ownFile_(rootFolder(), u.id);
    }
    let v = 1;
    if (f) {
      if (u.base != null) {
        const m = meta_(f);
        if (m.v !== u.base) {
          conflicts.push({ key: u.key, id: f.getId(), name: f.getName(), content: f.getBlob().getDataAsString('UTF-8'), bps: m.bps, v: m.v, by: m.by });
          return;
        }
      }
      v = (knownHere ? info.v : meta_(f).v) + 1;
      f.setContent(content);
      if (!(knownHere && info.name === name) && f.getName() !== name) f.setName(name);
      if (!(knownHere && info.dir === dirId)) {
        let here = false;
        const ps = f.getParents();
        while (ps.hasNext()) if (ps.next().getId() === dirId) here = true;
        if (!here) f.moveTo(folderById(dirId));
      }
    } else {
      f = folderById(dirId).createFile(name, content, MimeType.PLAIN_TEXT);
    }
    f.setDescription(JSON.stringify({ bps, v, by: me.email }));
    const fid = u.id && f ? (knownHere ? u.id : f.getId()) : f.getId();
    saved[u.key] = { id: fid, v };
    remembered[fid] = { root: rootId, dir: dirId, v, name };
  });
  (deletes || []).forEach(id => {
    const f = ownFile_(rootFolder(), id);
    if (f) f.setTrashed(true);
    CacheService.getScriptCache().remove('fi:' + id);
  });
  rememberFiles_(remembered);
  if (Object.keys(saved).length || (deletes || []).length) folderChanged_(rootId);
  touch_(me);
  return { saved, conflicts };
}

/** Creates, renames or deletes (moves to the Drive trash) one of `target`'s folders. */
function folderOp(target, op, name, newName) {
  const me = me_();
  const folder = folderFor_(target_(me, target));
  folderChanged_(folder.getId());
  name = cleanFolder_(name);
  if (!name) throw new Error('Folder names cannot be empty.');
  // forget remembered subfolder ids for the names involved (see subfolderId_)
  CacheService.getScriptCache().removeAll(['sd:' + folder.getId() + ':' + name, 'sd:' + folder.getId() + ':' + cleanFolder_(newName)]);
  if (op === 'create') { subfolder_(folder, name, true); return { ok: true }; }
  const d = subfolder_(folder, name, false);
  if (!d) { if (op === 'delete') return { ok: true }; throw new Error(`There is no folder called ${name}.`); }
  if (op === 'rename') {
    newName = cleanFolder_(newName);
    if (!newName) throw new Error('Folder names cannot be empty.');
    if (newName !== name && subfolder_(folder, newName, false)) throw new Error(`There is already a folder called ${newName}.`);
    d.setName(newName);
    return { ok: true };
  }
  if (op === 'delete') { d.setTrashed(true); return { ok: true }; }
  throw new Error('Unknown folder action.');
}

/** Teachers only: removes the load-test folders (to the Drive trash). */
function loadTestCleanup() {
  if (me_().role !== 'teacher') throw new Error('Teachers only.');
  const it = rootFolder_().getFoldersByName('_loadtest');
  while (it.hasNext()) it.next().setTrashed(true);
  Object.keys(PROPS.getProperties()).filter(k => k.indexOf('f:loadtest:') === 0).forEach(k => PROPS.deleteProperty(k));
  return true;
}

/** Teachers only: classes and their students. */
function listClasses() {
  const me = me_();
  if (me.role !== 'teacher') throw new Error('Teachers only.');
  CacheService.getScriptCache().remove('roster');
  const r = roster_();
  const classes = {};
  Object.keys(r.students).forEach(email => {
    const s = r.students[email];
    s.classes.forEach(cls => (classes[cls] = classes[cls] || []).push({ email, name: s.name, last: s.last }));
  });
  return Object.keys(classes).sort().map(name => ({
    name,
    students: classes[name].sort((a, b) => a.name.localeCompare(b.name)),
  }));
}
