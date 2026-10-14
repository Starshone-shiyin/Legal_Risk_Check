'use strict';

const { app, BrowserWindow, dialog, shell } = require('electron');
const fs = require('node:fs');
const http = require('node:http');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');

const PRODUCT_NAME = '识险智控';
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_BACKEND_PORT = 8000;
const DEFAULT_QDRANT_PORT = 6333;
const DEFAULT_FRONTEND_PORT = 8081;
const childProcesses = new Set();

let mainWindow = null;
let splashWindow = null;
let splashReady = null;
let frontendServer = null;
let shuttingDown = false;
let logFile = null;

function log(message, ...args) {
  const suffix = args.length ? ' ' + args.map((item) => String(item)).join(' ') : '';
  const line = '[' + new Date().toISOString() + '] ' + message + suffix + os.EOL;
  if (logFile) {
    try {
      fs.appendFileSync(logFile, line, 'utf8');
    } catch (_error) {
      // Logging must not prevent the desktop shell from starting.
    }
  }
  process.stdout.write(line);
}

function startupSplashHtml() {
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
  <title>${PRODUCT_NAME}</title>
  <style>
    :root { color-scheme: light; font-family: "Microsoft YaHei", "Segoe UI", sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #f3f7fb; color: #182536; }
    .card { width: 520px; padding: 36px 40px 32px; border: 1px solid #dfe8f2; border-radius: 18px; background: #fff; box-shadow: 0 16px 48px rgba(37, 67, 101, .12); }
    .brand { display: flex; align-items: center; gap: 14px; }
    .mark { width: 44px; height: 44px; display: grid; place-items: center; border-radius: 13px; color: #fff; font-size: 22px; font-weight: 700; background: linear-gradient(135deg, #1769aa, #35a7c8); }
    h1 { margin: 0; font-size: 22px; letter-spacing: .04em; }
    .subtitle { margin: 4px 0 0; color: #718096; font-size: 13px; }
    .status { margin-top: 34px; font-size: 17px; font-weight: 600; }
    .detail { min-height: 38px; margin-top: 9px; color: #718096; font-size: 13px; line-height: 1.65; }
    .track { height: 8px; margin-top: 20px; overflow: hidden; border-radius: 99px; background: #e7eef6; }
    .bar { width: 4%; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #1769aa, #35a7c8); transition: width .25s ease; }
    .hint { margin: 22px 0 0; color: #8a98a8; font-size: 12px; line-height: 1.6; }
  </style>
</head>
<body>
  <main class="card" aria-live="polite">
    <div class="brand">
      <div class="mark">险</div>
      <div><h1>${PRODUCT_NAME}</h1><div class="subtitle">风险识别与合规辅助系统</div></div>
    </div>
    <div class="status" id="status">正在准备运行环境</div>
    <div class="detail" id="detail">首次启动将加载内置法规库，请稍候。</div>
    <div class="track"><div class="bar" id="bar"></div></div>
    <div class="hint">正在启动本机服务。此过程不需要 Python、Docker 或额外安装组件。</div>
  </main>
  <script>
    window.updateStartupStatus = function(progress, status, detail) {
      document.getElementById('bar').style.width = Math.max(4, Math.min(100, progress)) + '%';
      document.getElementById('status').textContent = status || '';
      document.getElementById('detail').textContent = detail || '';
    };
  </script>
</body>
</html>`;
}

async function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 600,
    height: 380,
    resizable: false,
    maximizable: false,
    minimizable: false,
    frame: false,
    show: false,
    backgroundColor: '#f3f7fb',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  splashWindow.on('closed', () => {
    splashWindow = null;
    splashReady = null;
  });
  splashReady = splashWindow.loadURL(
    'data:text/html;charset=UTF-8,' + encodeURIComponent(startupSplashHtml()),
  );
  await splashReady;
  splashWindow.show();
}

async function updateSplash(progress, status, detail) {
  if (!splashWindow || splashWindow.isDestroyed()) return;
  const ready = splashReady;
  if (ready) await ready.catch(() => {});
  if (!splashWindow || splashWindow.isDestroyed()) return;
  const script = `window.updateStartupStatus(${JSON.stringify(progress)}, ${JSON.stringify(status)}, ${JSON.stringify(detail || '')});`;
  await splashWindow.webContents.executeJavaScript(script, true).catch(() => {});
}

function closeSplashWindow() {
  if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
  splashWindow = null;
  splashReady = null;
}

function yieldToUi() {
  return new Promise((resolve) => setImmediate(resolve));
}

function ensureDirectory(directory) {
  fs.mkdirSync(directory, { recursive: true });
  return directory;
}

function parsePort(value, fallback) {
  const port = Number.parseInt(String(value || ''), 10);
  return Number.isInteger(port) && port > 0 && port < 65536 ? port : fallback;
}

function readDotEnv(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return {};
  const values = {};
  for (const line of fs.readFileSync(filePath, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!match) continue;
    const key = match[1];
    const raw = match[2];
    if (!raw) {
      values[key] = '';
      continue;
    }
    try {
      values[key] = JSON.parse(raw);
    } catch (_error) {
      values[key] = raw.replace(/^['"]|['"]$/g, '');
    }
  }
  return values;
}

function isPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(false));
    server.once('listening', () => {
      server.close(() => resolve(true));
    });
    server.listen(port, '127.0.0.1');
  });
}

async function findFreePort(preferredPort) {
  for (let port = preferredPort; port < preferredPort + 100; port += 1) {
    if (await isPortAvailable(port)) return port;
  }
  throw new Error('无法找到可用端口，起始端口为 ' + preferredPort);
}

function mimeType(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  return {
    '.css': 'text/css; charset=utf-8',
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.ico': 'image/x-icon',
  }[extension] || 'application/octet-stream';
}

function startStaticServer(root, preferredPort) {
  const rootPath = path.resolve(root);
  if (!fs.existsSync(rootPath)) {
    throw new Error('前端资源目录不存在：' + rootPath);
  }

  return new Promise((resolve, reject) => {
    const server = http.createServer((request, response) => {
      try {
        const requestPath = decodeURIComponent((request.url || '/').split('?')[0]);
        const relativePath = requestPath === '/' ? '/website.html' : requestPath;
        const filePath = path.resolve(rootPath, '.' + relativePath);
        if (filePath !== rootPath && !filePath.startsWith(rootPath + path.sep)) {
          response.writeHead(403);
          response.end('Forbidden');
          return;
        }
        if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
          response.writeHead(404);
          response.end('Not Found');
          return;
        }
        response.writeHead(200, {
          'Content-Type': mimeType(filePath),
          'Cache-Control': 'no-store',
        });
        fs.createReadStream(filePath).pipe(response);
      } catch (error) {
        response.writeHead(400);
        response.end('Bad Request');
        log('静态资源请求失败', error.message);
      }
    });
    server.once('error', reject);
    server.listen(preferredPort, '127.0.0.1', () => resolve(server));
  });
}

function waitForHttp(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  return new Promise((resolve, reject) => {
    const retry = () => {
      if (Date.now() >= deadline) {
        reject(new Error('等待服务超时：' + url));
        return;
      }
      setTimeout(attempt, 250);
    };
    const attempt = () => {
      const request = http.get(url, (response) => {
        response.resume();
        if (response.statusCode >= 200 && response.statusCode < 500) {
          resolve(response.statusCode);
          return;
        }
        retry();
      });
      request.once('error', retry);
      request.setTimeout(1200, () => request.destroy());
    };
    attempt();
  });
}

function spawnManagedProcess(label, command, args, options) {
  log('启动 ' + label, command, args.join(' '));
  const child = spawn(command, args, {
    ...options,
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  childProcesses.add(child);
  child.stdout?.on('data', (data) => log('[' + label + '] ' + String(data).trimEnd()));
  child.stderr?.on('data', (data) => log('[' + label + '] ' + String(data).trimEnd()));
  child.once('error', (error) => log(label + ' 启动失败', error.message));
  child.once('exit', (code, signal) => {
    childProcesses.delete(child);
    if (!shuttingDown) log(label + ' 已退出', 'code=' + code, 'signal=' + (signal || ''));
  });
  return child;
}

function stopManagedProcess(child) {
  if (!child || child.killed || child.exitCode !== null) return Promise.resolve();
  return new Promise((resolve) => {
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      resolve();
    };
    child.once('exit', finish);
    if (process.platform === 'win32' && child.pid) {
      const killer = spawn('taskkill.exe', ['/pid', String(child.pid), '/t', '/f'], {
        windowsHide: true,
        stdio: 'ignore',
      });
      killer.once('exit', finish);
    } else {
      child.kill('SIGTERM');
      setTimeout(() => {
        if (child.exitCode === null) child.kill('SIGKILL');
        finish();
      }, 1500);
    }
  });
}

function copyDirectoryIfNeeded(source, target, marker) {
  if (!fs.existsSync(source) || fs.existsSync(marker)) return false;
  ensureDirectory(target);
  fs.cpSync(source, target, { recursive: true, force: false, errorOnExist: false });
  fs.writeFileSync(marker, new Date().toISOString(), 'utf8');
  return true;
}

function runtimePaths() {
  const resourcesRoot = app.isPackaged ? process.resourcesPath : PROJECT_ROOT;
  const userData = app.getPath('userData');
  const workspaceRoot = app.isPackaged
    ? ensureDirectory(path.join(userData, 'runtime'))
    : PROJECT_ROOT;
  const dataRoot = app.isPackaged
    ? ensureDirectory(path.join(workspaceRoot, 'data'))
    : ensureDirectory(path.join(PROJECT_ROOT, 'tmp', 'desktop_runtime'));
  return {
    resourcesRoot,
    workspaceRoot,
    dataRoot,
    configSeed: path.join(resourcesRoot, 'config'),
    configRoot: path.join(workspaceRoot, 'config'),
    configSeedMarker: path.join(workspaceRoot, 'config', '.installed'),
    knowledgeSeed: path.join(resourcesRoot, 'src', 'knowledge'),
    knowledgeRoot: path.join(workspaceRoot, 'src', 'knowledge'),
    knowledgeSeedMarker: path.join(workspaceRoot, 'src', '.knowledge-installed'),
    manifestSeed: path.join(resourcesRoot, 'knowledge_manifest.json'),
    manifestRoot: path.join(workspaceRoot, 'knowledge_manifest.json'),
    runtimeEnvPath: path.join(workspaceRoot, '.env'),
    qdrantStorage: ensureDirectory(path.join(dataRoot, 'qdrant')),
    qdrantSeed: path.join(resourcesRoot, 'qdrant', 'storage-seed'),
    qdrantSeedMarker: path.join(dataRoot, 'qdrant', '.seed-installed'),
    dataSeed: path.join(resourcesRoot, 'data-seed'),
    dataSeedMarker: path.join(dataRoot, '.competition-seed-installed'),
    fixtureSeed: path.join(resourcesRoot, 'tests', 'fixtures'),
    fixtureRoot: path.join(workspaceRoot, 'tests', 'fixtures'),
    fixtureSeedMarker: path.join(workspaceRoot, 'tests', '.fixtures-installed'),
    webRoot: app.isPackaged ? path.join(resourcesRoot, 'web') : path.join(PROJECT_ROOT, 'web'),
    projectRoot: PROJECT_ROOT,
    logRoot: ensureDirectory(path.join(userData, 'logs')),
  };
}

function seedPackagedWorkspace(paths) {
  if (!app.isPackaged) return;
  ensureDirectory(path.join(paths.workspaceRoot, 'tests'));
  ensureDirectory(path.join(paths.workspaceRoot, 'src'));
  copyDirectoryIfNeeded(paths.configSeed, paths.configRoot, paths.configSeedMarker);
  copyDirectoryIfNeeded(paths.knowledgeSeed, paths.knowledgeRoot, paths.knowledgeSeedMarker);
  if (fs.existsSync(paths.manifestSeed) && !fs.existsSync(paths.manifestRoot)) {
    fs.copyFileSync(paths.manifestSeed, paths.manifestRoot);
  }
  copyDirectoryIfNeeded(paths.dataSeed, paths.dataRoot, paths.dataSeedMarker);
  copyDirectoryIfNeeded(paths.fixtureSeed, paths.fixtureRoot, paths.fixtureSeedMarker);
}

function buildEnvironment(qdrantHost, qdrantPort, backendPort, runtimeEnvPath) {
  const savedEnvironment = readDotEnv(runtimeEnvPath);
  const environment = {
    ...savedEnvironment,
    ...process.env,
    QDRANT_HOST: qdrantHost,
    QDRANT_PORT: String(qdrantPort),
    RISKFLOW_BACKEND_PORT: String(backendPort || DEFAULT_BACKEND_PORT),
    QDRANT_COLLECTION: process.env.QDRANT_COLLECTION
      || savedEnvironment.QDRANT_COLLECTION
      || 'legal_knowledge_staging_20260811',
  };
  // Settings requires these names at boot. Placeholders keep deterministic local
  // demo routes available without ever embedding a real secret in the package.
  environment.LLM_API_KEY = environment.LLM_API_KEY || 'desktop-local-disabled';
  environment.SILICONFLOW_API_KEY = environment.SILICONFLOW_API_KEY || 'desktop-local-disabled';
  environment.RISK_DEMO_IDENTITY_ENABLED = environment.RISK_DEMO_IDENTITY_ENABLED || 'true';
  environment.RISK_LOCAL_FILE_OPEN_ENABLED = environment.RISK_LOCAL_FILE_OPEN_ENABLED || 'true';
  environment.RISK_DEVELOPER_DEBUG_ENABLED = environment.RISK_DEVELOPER_DEBUG_ENABLED || 'false';
  environment.EXTERNAL_RISK_LIVE_ENABLED = environment.EXTERNAL_RISK_LIVE_ENABLED || 'false';
  environment.EXTERNAL_RISK_HTTP_ENABLED = environment.EXTERNAL_RISK_HTTP_ENABLED || 'false';
  environment.EXTERNAL_RISK_INTELLIGENCE_ENABLED = environment.EXTERNAL_RISK_INTELLIGENCE_ENABLED || 'false';
  environment.EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED =
    environment.EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED || 'false';
  environment.EXTERNAL_RISK_WEB_SEARCH_ENABLED = environment.EXTERNAL_RISK_WEB_SEARCH_ENABLED || 'false';
  environment.MINEU_MODE = environment.MINEU_MODE || 'lightweight';
  if (runtimeEnvPath) environment.RISKFLOW_RUNTIME_ENV_PATH = runtimeEnvPath;
  if (app.isPackaged) environment.RISKFLOW_DESKTOP_PACKAGED = 'true';
  return environment;
}

async function startQdrant(paths) {
  const configuredHost = app.isPackaged ? '127.0.0.1' : (process.env.QDRANT_HOST || '127.0.0.1');
  const configuredPort = app.isPackaged
    ? await findFreePort(parsePort(process.env.RISKFLOW_QDRANT_PORT, DEFAULT_QDRANT_PORT))
    : parsePort(process.env.QDRANT_PORT, DEFAULT_QDRANT_PORT);

  if (!app.isPackaged && process.env.RISKFLOW_QDRANT_MODE !== 'bundled') {
    try {
      await waitForHttp('http://' + configuredHost + ':' + configuredPort + '/collections', 3500);
      log('使用现有 Qdrant', configuredHost + ':' + configuredPort);
    } catch (error) {
      log('现有 Qdrant 不可用，后端仍会启动，但 RAG 可能不可用', error.message);
    }
    return { host: configuredHost, port: configuredPort, process: null };
  }

  const executable = process.env.RISKFLOW_QDRANT_EXECUTABLE
    || path.join(paths.resourcesRoot, 'qdrant', process.platform === 'win32' ? 'qdrant.exe' : 'qdrant');
  if (!fs.existsSync(executable)) {
    throw new Error('未找到随包提供的 Qdrant：' + executable + '。请先执行运行时组件准备。');
  }

  copyDirectoryIfNeeded(paths.qdrantSeed, paths.qdrantStorage, paths.qdrantSeedMarker);
  const environment = {
    ...process.env,
    QDRANT__SERVICE__HOST: configuredHost,
    QDRANT__SERVICE__HTTP_PORT: String(configuredPort),
    QDRANT__STORAGE__STORAGE_PATH: paths.qdrantStorage,
  };
  const child = spawnManagedProcess('Qdrant', executable, [], {
    cwd: path.dirname(executable),
    env: environment,
  });
  await waitForHttp('http://' + configuredHost + ':' + configuredPort + '/collections', 15000);
  return { host: configuredHost, port: configuredPort, process: child };
}

async function startBackend(paths, backendPort, qdrant) {
  let command;
  let args;
  let cwd;
  if (app.isPackaged) {
    command = process.env.RISKFLOW_BACKEND_EXECUTABLE
      || path.join(paths.resourcesRoot, 'backend', process.platform === 'win32' ? 'riskflow-backend.exe' : 'riskflow-backend');
    args = [];
    cwd = paths.workspaceRoot;
    if (!fs.existsSync(command)) {
      throw new Error('未找到随包提供的 FastAPI 后端：' + command + '。请先执行运行时组件准备。');
    }
  } else {
    command = process.env.RISKFLOW_PYTHON;
    if (!command) {
      const venvPython = path.join(PROJECT_ROOT, 'venv', 'Scripts', 'python.exe');
      command = fs.existsSync(venvPython) ? venvPython : 'python';
    }
    args = [
      '-m', 'uvicorn', 'src.main:app',
      '--host', '127.0.0.1',
      '--port', String(backendPort),
    ];
    cwd = PROJECT_ROOT;
  }

  const child = spawnManagedProcess('FastAPI', command, args, {
    cwd,
    env: buildEnvironment(qdrant.host, qdrant.port, backendPort, app.isPackaged ? paths.runtimeEnvPath : null),
  });
  await waitForHttp('http://127.0.0.1:' + backendPort + '/health', 30000);
  return child;
}

async function createMainWindow(frontend) {
  mainWindow = new BrowserWindow({
    width: 1480,
    height: 960,
    minWidth: 1160,
    minHeight: 760,
    title: PRODUCT_NAME,
    backgroundColor: '#f4f7fb',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      preload: path.join(__dirname, 'preload.cjs'),
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://') || url.startsWith('https://')) shell.openExternal(url);
    return { action: 'deny' };
  });
  mainWindow.on('closed', () => { mainWindow = null; });
  const target = frontend.url + '/website.html?api=' + encodeURIComponent(frontend.backendUrl) + '&tab=dashboard';
  await mainWindow.loadURL(target);
}

async function shutdown() {
  closeSplashWindow();
  if (frontendServer) {
    await new Promise((resolve) => frontendServer.close(resolve));
    frontendServer = null;
  }
  const processes = [...childProcesses];
  await Promise.all(processes.map(stopManagedProcess));
  childProcesses.clear();
}

async function bootstrap() {
  await createSplashWindow();
  await updateSplash(6, '正在准备运行环境', '正在建立本地运行目录');
  await yieldToUi();
  const paths = runtimePaths();
  logFile = path.join(paths.logRoot, 'desktop.log');
  log('启动桌面封装', 'packaged=' + app.isPackaged, 'platform=' + process.platform, 'arch=' + process.arch);
  await updateSplash(14, '正在加载内置法规库', '首次启动将复制法规文本、演示数据和检索索引');
  await yieldToUi();
  seedPackagedWorkspace(paths);
  await updateSplash(32, '内置法规库已加载', '正在检查本机服务端口');

  const frontendPort = await findFreePort(parsePort(process.env.RISKFLOW_FRONTEND_PORT, DEFAULT_FRONTEND_PORT));
  const backendPort = await findFreePort(parsePort(process.env.RISKFLOW_BACKEND_PORT, DEFAULT_BACKEND_PORT));
  await updateSplash(38, '正在启动向量检索服务', '正在启动本机 Qdrant 服务');
  const qdrant = await startQdrant(paths);
  await updateSplash(62, '向量检索服务已就绪', '正在启动本机业务服务');
  await startBackend(paths, backendPort, qdrant);
  await updateSplash(84, '业务服务已就绪', '正在打开系统界面');

  frontendServer = await startStaticServer(paths.webRoot, frontendPort);
  await createMainWindow({
    url: 'http://127.0.0.1:' + frontendPort,
    backendUrl: 'http://127.0.0.1:' + backendPort,
  });
  await updateSplash(100, '系统已就绪', '正在进入风险识别与合规辅助系统');
  await new Promise((resolve) => setTimeout(resolve, 250));
  closeSplashWindow();
  log(
    '桌面封装已就绪',
    'frontend=http://127.0.0.1:' + frontendPort,
    'backend=http://127.0.0.1:' + backendPort,
    'qdrant=' + qdrant.host + ':' + qdrant.port,
  );
}

app.setAppUserModelId('cn.riskflow.competition');

app.whenReady().then(() => bootstrap()).catch(async (error) => {
  log('桌面封装启动失败', error.stack || error.message);
  await updateSplash(100, '启动失败', '请查看日志文件，或联系项目提供方');
  await new Promise((resolve) => setTimeout(resolve, 500));
  await shutdown();
  await dialog.showMessageBox({
    type: 'error',
    title: PRODUCT_NAME + ' 启动失败',
    message: error.message,
    detail: '请查看用户数据目录下的 logs/desktop.log。开发模式请确认 Python、Qdrant 和项目配置可用。',
  });
  app.exit(1);
});

app.on('before-quit', (event) => {
  if (shuttingDown) return;
  event.preventDefault();
  shuttingDown = true;
  shutdown().finally(() => app.exit(0));
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

process.on('uncaughtException', (error) => log('未捕获异常', error.stack || error.message));
process.on('unhandledRejection', (error) => log('未处理 Promise 异常', error?.stack || error));
