# Setting up classes and online saving (Google Apps Script)

PyStudio runs on GitHub Pages. A small Apps Script project in **your** school Google account adds:

- **Sign-in:** students are recognised by their school Google account. There are no passwords or codes.
- **Saving:** each person's files go into a folder in **your** Google Drive.
- **Class lists:** you edit a Google Sheet listing classes, students and teachers.

Students use the Apps Script link (it ends in `/exec`). The plain GitHub link still works, but
files are then saved only in that browser.

## 1. Put the code in your Apps Script project
1. Open your **PyStudio** project at https://script.google.com.
2. In **`Code.gs`**, replace everything with the contents of [`apps-script/Code.gs`](apps-script/Code.gs).
3. In **`index.html`**, replace everything with the contents of [`apps-script/index.html`](apps-script/index.html).
4. Press **Ctrl+S**.

## 2. Run the one-time setup
1. In the toolbar's function menu (next to **Debug**), pick **`setup`**, then click **Run**.
2. Google asks for permission to use Drive and Sheets. Click **Review permissions** and choose your account.
   If you see "Google hasn't verified this app", click **Advanced → Go to PyStudio**. It's your own script.
3. The **Execution log** at the bottom shows two links:
   - **Class list**: the spreadsheet *PyStudio – Classes*
   - **Student files folder**: *PyStudio files* in your Drive

   Both are in your Drive, so you can find them again there.

## 3. Fill in the class list

### Option A: import from Google Classroom (recommended)
1. In the Apps Script editor's left panel, click **+** next to **Services**, choose **Google Classroom API**, and click **Add**.
2. In the function menu, pick **`importFromClassroom`** and click **Run**. Allow the new Classroom permissions when asked.
   This first run only fills a new **Courses** tab in the class list with all your active Classroom courses, all unticked.
3. Open the class list. In the **Courses** tab, tick **Use in PyStudio** for the courses you want.
   You can also type a shorter **Name in PyStudio**, such as `9A`.
4. Run **`importFromClassroom`** again. The **Students** tab now holds the students of the ticked courses,
   and co-teachers of those courses are added to the **Teachers** tab.

Run `importFromClassroom` again whenever students join or leave, or after you change the ticks.
New Classroom courses appear in the Courses tab unticked. Unticking a course removes its students from PyStudio's list,
but their files stay in Drive. Classes you typed into the Students tab yourself are never touched.
You don't need to redeploy after an import.

### Option B: type it in
In the **Students** tab, add one row per student:

| Class | Student name | Email | Last active (automatic) |
|---|---|---|---|
| 9A | Sara Ahmad | sara.ahmad@ics.edu.jo | |

- Delete the example row. A student in several classes gets one row per class.
- To add other teachers, put their emails in the **Teachers** tab. You're always a teacher.
- Changes reach PyStudio within about a minute.

## 4. Publish the new version
1. Click **Deploy → Manage deployments**, then the pencil ✏️.
2. Set **Version** to **New version** and click **Deploy**.
   The `/exec` link stays the same.
3. Give that link to your students. A short link or QR code makes it easier to share.

## How it works for you
- You open the same link. You get **My files**, plus a **Classes** panel at the bottom left.
- Pick a class, then click a student to open their files. You can run and debug them.
  While you watch, their changes appear every few seconds.
- You can also edit their files. Your edits save into the student's file, and they see them within about 20 seconds.
  If you both change the same file at the same moment, nothing is lost: the second person's version is saved as `name-mine.py`.
- You can also browse everyone's work directly in the *PyStudio files* folder in Drive, organised as Class → Student.
- Deleted files go to **your** Drive trash, so you can restore them for 30 days.

## Pseudocode
**📝 Pseudocode** shows the current file as Cambridge IGCSE (0984) pseudocode next to the Python. It's view only.
- It updates as you type. Click a pseudocode line to highlight the Python line it came from. Moving the cursor in the Python highlights the matching pseudocode lines.
- It follows the syllabus style: `←`, `IF … THEN … ELSE … ENDIF`, `CASE OF`, `FOR … TO … STEP … NEXT`, `WHILE … DO … ENDWHILE`,
  `REPEAT … UNTIL`, `PROCEDURE`/`FUNCTION … RETURNS`, `INPUT`/`OUTPUT`, `MOD`/`DIV`, `LENGTH`/`SUBSTRING`/`UCASE`/`LCASE`,
  `ROUND`/`RANDOM` and file handling.
- Arrays keep Python's 0-based indexes, written as `ARRAY[0:n]`. `DECLARE` lines are added automatically, and names are written in PascalCase.
- Python with no Cambridge equivalent (for example lists that grow, list comprehensions or turtle) is marked with a `// Note` line, or with `< >` around the Python.
- **Copy** and **Print** are at the top of the panel.

## Folders
- **Make a folder:** **+ Folder**. Click a folder to open or close it. Hover over it to rename ✎ or delete ✕.
  Deleting a folder sends it, with its files, to your Drive trash.
- **New files and uploads** go into the folder you're working in. Click **My files** to work outside any folder.
- **Move a file:** use **Move**, or drag it onto a folder. Drag it onto **My files** to take it out of a folder.
- **Class files** can have folders too. When a student edits one, their copy goes into a folder with the same name.
- **In Drive,** folders are real subfolders, one level deep.

## Class files (starter code for a class)
- **Add files:** in the **Classes** panel, pick a class and click **📁 Class files**. Add files there with
  **+ New** or **Upload**, or edit them like any other file.
- **Share an existing file:** open one of **My files** and click **📤 Share to class**, then choose the class.
  This copies the file into that class's Class files. If a file with the same name is already there, it's updated.
- **What students see:** a **Class files** section below their own files. They can open, run and debug them.
  As soon as they type, the file becomes **their own copy** in My files. Your original is never changed.
- **Updating:** when you edit a class file, students see the new version within about 20 seconds. New students in the class get the files too.
- **In Drive:** the files are stored in *PyStudio files › (class) › _Class files (students can see these)*.

## Good to know
- **Shared computers:** PyStudio uses whichever Google account the browser is signed in to.
  Students should sign out of Google at the end of the lesson.
- **Not on the list:** if a student isn't in the sheet yet, PyStudio tells them so and saves
  only on that computer until you add them.
- **Quotas:** Apps Script's free limits are well above what one class needs. Saves happen at most every
  few seconds while someone types.
- **Updating PyStudio:** changes to the editor are published on GitHub and appear straight away.
  You only redo steps 1 and 4 when `apps-script/Code.gs` or `apps-script/index.html` changes.
