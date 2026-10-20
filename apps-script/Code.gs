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

function doGet() {
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
  const students = {};
  ss.getSheetByName('Students').getDataRange().getValues().slice(1).forEach((r, i) => {
    const email = String(r[2] || '').trim().toLowerCase();
    if (!email || !email.includes('@')) return;
    students[email] = {
      cls: String(r[0] || '').trim() || 'No class',
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
  if (r.students[email]) return { email, role: 'student', name: r.students[email].name, cls: r.students[email].cls };
  return { email, role: 'none', name: email };
}

/** Whose files may `me` open? Their own; teachers may open anyone on the lists. */
function target_(me, target) {
  target = String(target || me.email).toLowerCase();
  if (me.role === 'none') throw new Error('Your account is not on a class list yet. Ask your teacher to add you.');
  if (target === me.email) return target;
  const r = roster_();
  if (me.role === 'teacher' && (r.students[target] || r.teachers[target])) return target;
  throw new Error('You do not have access to those files.');
}

function folderFor_(email) {
  const key = 'f:' + email;
  const id = PROPS.getProperty(key);
  if (id) { try { const f = DriveApp.getFolderById(id); if (!f.isTrashed()) return f; } catch (e) {} }
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const again = PROPS.getProperty(key);
    if (again && again !== id) return DriveApp.getFolderById(again);
    const r = roster_();
    const s = r.students[email];
    const parent = childFolder_(rootFolder_(), s ? s.cls : 'Teachers');
    const folder = parent.createFolder(s ? `${s.name} (${email})` : email);
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
  try { const m = JSON.parse(file.getDescription() || '{}'); return { bps: Array.isArray(m.bps) ? m.bps : [], v: +m.v || 0, by: m.by || '' }; }
  catch (e) { return { bps: [], v: 0, by: '' }; }
}

function ownFile_(folder, id) {
  try {
    const f = DriveApp.getFileById(id);
    if (f.isTrashed()) return null;
    const ps = f.getParents();
    while (ps.hasNext()) if (ps.next().getId() === folder.getId()) return f;
  } catch (e) {}
  return null;
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
 */
function listFiles(target, known) {
  const me = me_();
  const email = target_(me, target);
  known = known || {};
  const out = [];
  const it = folderFor_(email).getFiles();
  while (it.hasNext()) {
    const f = it.next();
    if (f.isTrashed()) continue;
    const m = meta_(f);
    const e = { id: f.getId(), name: f.getName(), v: m.v, by: m.by };
    if (known[e.id] !== m.v) { e.content = f.getBlob().getDataAsString('UTF-8'); e.bps = m.bps; }
    out.push(e);
  }
  return { files: out };
}

/**
 * Saves changes to `target`'s files.
 * upserts: [{key, id|null, base|null, name, content, bps}] — `base` is the version the edit started from.
 * If someone else saved the file since `base`, it is returned in `conflicts` instead of overwritten.
 */
function syncFiles(target, upserts, deletes) {
  const me = me_();
  const email = target_(me, target);
  const folder = folderFor_(email);
  const saved = {}, conflicts = [];
  (upserts || []).slice(0, MAX_FILES).forEach(u => {
    const content = String(u.content == null ? '' : u.content);
    if (content.length > MAX_FILE_CHARS) throw new Error(`${u.name} is too large to save.`);
    const name = cleanName_(u.name);
    const bps = Array.isArray(u.bps) ? u.bps.filter(n => typeof n === 'number').slice(0, 500) : [];
    let f = u.id ? ownFile_(folder, u.id) : null;
    let v = 1;
    if (f) {
      const m = meta_(f);
      if (u.base != null && m.v !== u.base) {
        conflicts.push({ key: u.key, id: f.getId(), name: f.getName(), content: f.getBlob().getDataAsString('UTF-8'), bps: m.bps, v: m.v, by: m.by });
        return;
      }
      v = m.v + 1;
      f.setContent(content);
      if (f.getName() !== name) f.setName(name);
    } else {
      f = folder.createFile(name, content, MimeType.PLAIN_TEXT);
    }
    f.setDescription(JSON.stringify({ bps, v, by: me.email }));
    saved[u.key] = { id: f.getId(), v };
  });
  (deletes || []).forEach(id => { const f = ownFile_(folder, id); if (f) f.setTrashed(true); });
  touch_(me);
  return { saved, conflicts };
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
    (classes[s.cls] = classes[s.cls] || []).push({ email, name: s.name, last: s.last });
  });
  return Object.keys(classes).sort().map(name => ({
    name,
    students: classes[name].sort((a, b) => a.name.localeCompare(b.name)),
  }));
}
