# Medical Laboratory Management System

A Flask-based lab management system (patients, doctors, lab orders,
samples, results, reports, billing, inventory) packaged to run as a
native-feeling Windows desktop application — no browser, no visible
localhost, no console window.

> **Before shipping to any customer, change these two things:**
> 1. **Default admin password.** First run creates `admin` / `admin123`
>    (see `app/__init__.py::_ensure_default_admin`). Log in once and
>    change it immediately under Settings → Users, or edit the seed
>    values before the first build.
> 2. **License signing secret.** `app/license_check.py` ships with a
>    placeholder `MEDLAB_LICENSE_SECRET`. Anyone who reads this
>    repo can forge a valid license key against the default value.
>    Set a real secret (env var at build time, or edit the constant)
>    before you generate and hand out any license keys.
> 3. **Flask `SECRET_KEY`.** `app/config.py` also ships with a
>    placeholder `MEDLAB_SECRET_KEY` fallback, used to sign session
>    cookies. Set a real one (env var, or edit the constant) too.

## Project layout

```
medlab/
  app/                     Flask application (models, routes, templates)
  assets/
    medical_lab.ico         Application icon (all sizes)
    medical_lab_512.png     Icon master, for reference/rebuilding
    make_icon.py            Regenerates the .ico from scratch (needs Pillow)
  installer/
    medlab_installer.iss    Inno Setup installer script
  desktop_launcher.py       PyWebView + Flask desktop entry point (→ .exe)
  medical_lab.spec          PyInstaller build spec
  run.py                    Plain dev entry point (python run.py)
  requirements.txt          Runtime dependencies
  requirements-build.txt    + PyInstaller, for building the .exe
```

## 0. Automated builds (recommended)

`.github/workflows/build-windows.yml` builds this project on a real
Windows machine automatically via GitHub Actions — no local Windows
box needed:

1. Push this project to a GitHub repo.
2. The workflow runs on every push to `main` (or trigger it manually
   from the Actions tab → "Build Windows Desktop App" → "Run workflow").
3. It first runs the test suite (`tests/`) on Linux as a fast sanity
   check, then on a `windows-latest` runner: builds
   `MedicalLaboratory.exe` with PyInstaller, launches it briefly to
   confirm the process stays alive (not just add itself immediately
   crash), then builds `MedicalLaboratorySetup.exe` with Inno Setup.
4. Download both from the run's **Artifacts** section:
   `MedicalLaboratory-exe` (the raw app folder) and
   `MedicalLaboratorySetup` (the installer to hand to customers).

This is the easiest path if you don't have a Windows machine handy.
Steps 3–4 below describe doing the same build manually on a local
Windows PC.

## 1. Run it as a normal web app (development / testing)

Works on Windows, macOS, or Linux — this is how you test the Flask app
itself without touching PyWebView/PyInstaller at all.

```bash
python -m venv venv
venv\Scripts\activate        (Windows)   or   source venv/bin/activate (macOS/Linux)
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5000 — default login is `admin` / `admin123`
(change this immediately in Settings → Users once you're in).

## 2. Run it as a desktop window (still without building the .exe)

This uses the same PyWebView window the final .exe will use, so you
can confirm the "no browser" experience before doing a full build.
**Must be run on Windows** for the real WebView2-backed window (on
Linux/macOS pywebview falls back to another engine, fine for a quick
functional check but not representative of the final look).

```bash
pip install -r requirements.txt
python desktop_launcher.py
```

## 3. Build the Windows executable

Do this step **on a Windows machine** — PyInstaller builds
platform-native executables, so a Windows .exe can't be produced from
Linux/macOS.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements-build.txt

pyinstaller medical_lab.spec
```

This produces `dist\MedicalLaboratory\MedicalLaboratory.exe` plus its
supporting files (an "onedir" build — see the comment in
`medical_lab.spec` for why onedir instead of onefile).

Test it directly first:

```powershell
dist\MedicalLaboratory\MedicalLaboratory.exe
```

Confirm:
- No Chrome/Edge/Firefox window opens — only the app's own window
- Title bar reads "Medical Laboratory Management System"
- No console/terminal window appears
- Taskbar shows the app name, not `python.exe`
- Closing the window fully exits the process (check Task Manager)
- Launching the .exe a second time doesn't spawn a second server

## 4. Build the installer (MedicalLaboratorySetup.exe)

Requires [Inno Setup 6](https://jrsoftware.org/isinfo.php) on the same
Windows build machine, run **after** step 3 (it packages the
`dist\MedicalLaboratory\` folder that PyInstaller just produced).

```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\medlab_installer.iss
```

Output: `dist\installer\MedicalLaboratorySetup.exe` — this is the
single file you hand to a customer. It:

- Installs to Program Files
- Creates a Start Menu shortcut and an uninstaller
- Optionally creates a desktop shortcut (checkbox during install)
- Uses `medical_lab.ico` for the .exe and every shortcut
- Checks for the Microsoft Edge WebView2 Runtime and offers to open
  the download page if it's missing (WebView2 ships with Windows
  Update on most modern PCs already, so this rarely triggers)
- Leaves `%PROGRAMDATA%\MedicalLaboratoryManagementSystem\` (the
  database, backups, reports, license) untouched on uninstall, so
  upgrading or reinstalling never loses lab data

## Data locations at runtime

All writable data lives outside the installed application folder, in:

```
%PROGRAMDATA%\MedicalLaboratoryManagementSystem\
  database\medlab.db
  backups\
  uploads\
  reports\
  license\license.json
  logs\app.log
```

This is deliberate (Part 92 of the spec): the PyInstaller bundle
directory is effectively read-only at runtime, so the SQLite database
and generated files must not live there.

## Licensing

Licensing is fully offline (HMAC-signed key, checked locally — no
phone-home, no internet required) and is **enforced**: once a user is
logged in, every page except the license activation screen itself is
blocked until a valid key is on file (see
`app/__init__.py::_register_license_gate`). Admins are redirected
straight to Settings → License with a prompt to activate; anyone else
sees a plain "contact your administrator" page instead of a redirect
they have no permission to follow. To generate a key for a customer:

```bash
python -c "from app.license_check import generate_license_key as g; print(g('Customer Name', days_valid=3650))"
```

Give the customer that key; they paste it into Settings → License in
the app. **Change `MEDLAB_LICENSE_SECRET`** (in `app/license_check.py`,
or via that environment variable at build time) before shipping —
anyone with the default secret in this repo could forge a valid key.

## Regenerating the icon

If you want a different icon design, edit `assets/make_icon.py` and
rerun `python assets/make_icon.py` (needs `pip install Pillow`). It
regenerates both `medical_lab.ico` (multi-size, used by the .exe and
shortcuts) and `medical_lab_512.png` (a flat master image).

## Security notes

- **License enforcement.** See "Licensing" above — every page beyond
  login/license-activation is blocked without a valid key.
- **Cross-origin write protection.** Even though this app runs inside
  a dedicated desktop window rather than a browser tab, it's still a
  real HTTP server on `127.0.0.1`. `app/__init__.py::_register_origin_guard`
  rejects any state-changing request (`POST`/`PUT`/`PATCH`/`DELETE`)
  whose `Origin` or `Referer` header points somewhere other than the
  app's own origin — this is what stops another website, open at the
  same time in the user's regular browser, from silently submitting
  requests to the local server ("localhost CSRF").
- Change the default admin password, the license-signing secret, and
  the Flask `SECRET_KEY` before shipping (see the warning at the top
  of this file).

## Tests

`tests/` has a full pytest suite (auth, license enforcement,
cross-origin write protection, every page render, the complete patient
→ order → sample → result → report → invoice workflow, inventory
adjustments, backup, offline license activation — 37 tests, all
passing). Each test gets a fully isolated temp data directory via
`MEDLAB_DATA_DIR` (see `tests/conftest.py`), so runs never interfere
with each other or with real user data. Run them with:

```bash
pip install -r requirements.txt pytest
pytest tests/ -v
```

## What's tested vs. what still needs Windows

Everything in `app/` (routes, models, PDF generation, the full
workflow above) has been exercised end-to-end with Flask's test
client and an automated pytest suite, and works.

`desktop_launcher.py`, `medical_lab.spec`, and
`installer/medlab_installer.iss` are written to satisfy the
requirements (single instance, hidden console, custom icon, clean
shutdown, WebView2 check, offline operation). This development
environment is Linux, so the actual `.exe`/installer can't be produced
or run here directly — use the GitHub Actions workflow (section 0
above) to build and smoke-test them on a real Windows runner, or
follow the step-3/step-4 checklist on a local Windows PC.
