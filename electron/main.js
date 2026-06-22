const { app, BrowserWindow, Menu, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const isDev = !app.isPackaged;
const BACKEND_PORT = 8000;

let mainWindow = null;
let backendProcess = null;

function getBackendDir() {
  if (isDev) return path.join(__dirname, '..', 'backend');
  return path.join(process.resourcesPath, 'backend');
}

function getFrontendDir() {
  if (isDev) return path.join(__dirname, '..', 'video-transcriber-frontend', 'dist');
  return path.join(process.resourcesPath, 'frontend');
}

function waitForBackend(maxRetries = 30, interval = 1000) {
  return new Promise((resolve, reject) => {
    let retries = 0;
    const check = () => {
      const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/api/health`, (res) => {
        let body = '';
        res.on('data', (chunk) => body += chunk);
        res.on('end', () => {
          if (res.statusCode === 200) resolve();
          else retry(`Health check returned ${res.statusCode}`);
        });
      });
      req.on('error', () => retry('Backend not reachable'));
      req.setTimeout(3000, () => { req.destroy(); retry('Request timed out'); });
    };
    const retry = (msg) => {
      if (++retries >= maxRetries) reject(new Error(`Backend failed to start: ${msg}`));
      else setTimeout(check, interval);
    };
    check();
  });
}

function startBackend() {
  const backendDir = getBackendDir();
  const frontendDir = getFrontendDir();
  const userDataDir = app.getPath('userData');

  backendProcess = spawn('uvicorn', [
    'main:app',
    '--host', '127.0.0.1',
    '--port', String(BACKEND_PORT),
    '--timeout-keep-alive', '600',
  ], {
    cwd: backendDir,
    env: {
      ...process.env,
      DATA_DIR: path.join(userDataDir, 'data'),
      FRONTEND_DIR: frontendDir,
    },
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`[backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.log(`[backend] ${data.toString().trim()}`);
  });

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend:', err.message);
    dialog.showErrorBox(
      'Backend Error',
      `Could not start the Python backend.\n\nMake sure Python 3.12+ is installed and uvicorn is available:\n  pip install -r backend/requirements.txt\n\nError: ${err.message}`
    );
    app.quit();
  });

  backendProcess.on('exit', (code, signal) => {
    console.log(`Backend exited (code: ${code}, signal: ${signal})`);
    if (mainWindow && !mainWindow.isDestroyed()) {
      dialog.showErrorBox('Backend Stopped', 'The Python backend has stopped unexpectedly. The app will now close.');
      app.quit();
    }
  });
}

function createMenu() {
  const template = [
    {
      label: 'Transcribo',
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        { role: 'close' },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: 'Transcribo',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    show: false,
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    require('electron').shell.openExternal(url);
    return { action: 'deny' };
  });

  const url = isDev
    ? 'http://localhost:5173'
    : `http://127.0.0.1:${BACKEND_PORT}`;

  console.log(`Loading URL: ${url}`);
  await mainWindow.loadURL(url);
}

app.whenReady().then(async () => {
  createMenu();

  if (!isDev) {
    startBackend();
    try {
      await waitForBackend();
      console.log('Backend is ready');
    } catch (err) {
      console.error(err.message);
      dialog.showErrorBox('Startup Error', err.message);
      app.quit();
      return;
    }
  }

  await createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }
});
