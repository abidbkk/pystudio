/**
 * A pretend class for trying PyStudio out: run makeDemoClass() once from the editor.
 * It adds five made-up students (emails @example.com, so nobody can sign in as them) to the
 * Students tab, makes their folders with a few files each, and adds some Class files.
 * Safe to run again: nothing that already exists is changed. removeDemoClass() takes it all away.
 */

const DEMO_CLASS = 'Y10 Comp Sci';

const DEMO_CLASS_FILES = {
  'Task 1 - Greeting.py':
`# Task 1: ask for the user's name and age, then greet them
name = input("What is your name? ")
age = int(input("How old are you? "))
print("Hello", name)
print("Next year you will be", age + 1)
`,
  'Task 2 - Times table.py':
`# Task 2: print the times table for a number the user chooses
number = int(input("Which times table? "))
for i in range(1, 13):
    print(i, "x", number, "=", i * number)
`,
  'Task 3 - Grade.py':
`# Task 3: turn a mark out of 100 into a grade
mark = int(input("Enter the mark: "))
if mark >= 80:
    print("Grade A")
elif mark >= 60:
    print("Grade B")
elif mark >= 40:
    print("Grade C")
else:
    print("Grade U")
`,
};

const DEMO_STUDENTS = [
  { name: 'Layla Nasser', email: 'layla.nasser@example.com', files: {
    'greeting.py':
`name = input("What is your name? ")
age = int(input("How old are you? "))
print("Hello", name)
print("Next year you will be", age + 1)
`,
    'times table.py':
`number = int(input("Which times table? "))
for i in range(1, 13):
    print(i, "x", number, "=", i * number)
`,
    'grade.py':
`mark = int(input("Enter the mark: "))
if mark >= 80:
    print("Grade A")
elif mark >= 60:
    print("Grade B")
else:
    print("Grade C")
`,
  } },
  { name: 'Yousef Haddad', email: 'yousef.haddad@example.com', files: {
    'hello.py': '# Start typing your code here\nprint("Hello world")\n',
    'greeting.py':
`name = input("What is your name? ")
age = input("How old are you? ")
print("Hello", name)
print("Next year you will be", age + 1)
`,
  } },
  { name: 'Mira Saleh', email: 'mira.saleh@example.com', files: {
    'greeting.py':
`name = input("Name: ")
print("Hi " + name + "!")
`,
    'times table.py':
`number = int(input("Which times table? "))
for i in range(1, 11):
    print(number, "times", i, "is", number * i)
`,
    'countdown.py':
`import turtle
count = 10
while count > 0:
    print(count)
    turtle.forward(count * 10)
    turtle.left(90)
    count = count - 1
print("Lift off!")
`,
  } },
  { name: 'Kareem Odeh', email: 'kareem.odeh@example.com', files: {
    'times table.py':
`number = int(input("Which times table? "))
for i in range(1, 13)
    print(i, "x", number, "=", i * number)
`,
    'grade.py':
`mark = int(input("Enter the mark: "))
if mark >= 80:
    print("Grade A")
if mark >= 60:
    print("Grade B")
if mark >= 40:
    print("Grade C")
`,
  } },
  { name: 'Hana Jaber', email: 'hana.jaber@example.com', files: {
    'greeting.py':
`name = input("What is your name? ")
age = int(input("How old are you? "))
print("Hello", name, "you are", age)
`,
    'times table.py':
`number = int(input("Which times table? "))
total = 0
for i in range(1, 13):
    answer = i * number
    total = total + answer
    print(i, "x", number, "=", answer)
print("All the answers add up to", total)
`,
    'grade.py':
`mark = int(input("Enter the mark: "))
if mark >= 80:
    print("Grade A")
elif mark >= 60:
    print("Grade B")
elif mark >= 40:
    print("Grade C")
else:
    print("Grade U")
`,
  } },
];

/** Run this once from the editor (select "makeDemoClass" and click Run). */
function makeDemoClass() {
  const owner = Session.getEffectiveUser().getEmail().toLowerCase();
  const st = SpreadsheetApp.openById(PROPS.getProperty('SHEET')).getSheetByName('Students');
  const have = new Set(st.getDataRange().getValues().slice(1)
    .filter(r => String(r[0] || '').trim() === DEMO_CLASS)
    .map(r => String(r[2] || '').trim().toLowerCase()));
  const add = DEMO_STUDENTS.filter(s => !have.has(s.email)).map(s => [DEMO_CLASS, s.name, s.email]);
  if (add.length) st.getRange(st.getLastRow() + 1, 1, add.length, 3).setValues(add);
  CacheService.getScriptCache().remove('roster');

  let made = 0;
  const addFiles = (key, files) => {
    const folder = folderFor_(key);
    Object.keys(files).forEach(name => {
      if (folder.getFilesByName(name).hasNext()) return;
      folder.createFile(name, files[name], MimeType.PLAIN_TEXT)
        .setDescription(JSON.stringify({ bps: [], v: 1, by: owner }));
      made++;
    });
    folderChanged_(folder.getId());
  };
  DEMO_STUDENTS.forEach(s => addFiles(s.email, s.files));
  addFiles('class:' + DEMO_CLASS, DEMO_CLASS_FILES);
  Logger.log(`${DEMO_CLASS}: added ${add.length} student(s) and ${made} file(s).`);
}

/** Takes the demo class away again: its rows, folders (to the Drive trash) and remembered folder ids. */
function removeDemoClass() {
  const st = SpreadsheetApp.openById(PROPS.getProperty('SHEET')).getSheetByName('Students');
  const emails = new Set(DEMO_STUDENTS.map(s => s.email));
  const rows = st.getDataRange().getValues();
  for (let i = rows.length - 1; i >= 1; i--) {
    if (String(rows[i][0] || '').trim() === DEMO_CLASS && emails.has(String(rows[i][2] || '').trim().toLowerCase())) st.deleteRow(i + 1);
  }
  // Only the demo's own folders go; anything else in the class folder is left alone.
  [...emails, 'class:' + DEMO_CLASS].forEach(key => {
    const id = PROPS.getProperty('f:' + key);
    if (id) { try { DriveApp.getFolderById(id).setTrashed(true); } catch (e) {} }
    PROPS.deleteProperty('f:' + key);
  });
  const it = rootFolder_().getFoldersByName(DEMO_CLASS);
  while (it.hasNext()) {
    const d = it.next(), sub = d.getFolders();
    let empty = !d.getFiles().hasNext();
    while (empty && sub.hasNext()) if (!sub.next().isTrashed()) empty = false;
    if (empty) d.setTrashed(true);
  }
  CacheService.getScriptCache().remove('roster');
  Logger.log(`${DEMO_CLASS} removed.`);
}
